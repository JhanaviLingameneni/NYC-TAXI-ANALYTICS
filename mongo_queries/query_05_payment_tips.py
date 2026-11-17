from pymongo import MongoClient
from datetime import datetime
import time

client = MongoClient("mongodb://localhost:27017")
db = client["nyc_taxi_analytics"]

pipeline = [
    {
        "$match": {
            "pickup.datetime": {
                "$gte": datetime(2025, 1, 1),
                "$lt": datetime(2026, 1, 1)
            }
        }
    },
    {
        "$group": {
            "_id": "$payment.method",
            "total_trips": {"$sum": 1},
            "avg_fare": {"$avg": "$fare.fare_amount"},
            "avg_tip": {"$avg": "$fare.tip_amount"},
            "avg_tip_percentage": {
                "$avg": {
                    "$cond": [
                        {"$gt": ["$fare.fare_amount", 0]},
                        {
                            "$multiply": [
                                100,
                                {
                                    "$divide": [
                                        "$fare.tip_amount",
                                        "$fare.fare_amount"
                                    ]
                                }
                            ]
                        },
                        None
                    ]
                }
            },
            "trips_with_tip": {
                "$sum": {
                    "$cond": [
                        {"$gt": ["$fare.tip_amount", 0]},
                        1,
                        0
                    ]
                }
            }
        }
    },
    {
        "$project": {
            "_id": 0,
            "payment_method": "$_id",
            "total_trips": 1,
            "avg_fare": {"$round": ["$avg_fare", 2]},
            "avg_tip": {"$round": ["$avg_tip", 2]},
            "avg_tip_percentage": {
                "$round": ["$avg_tip_percentage", 2]
            },
            "pct_trips_with_tip": {
                "$round": [
                    {
                        "$multiply": [
                            100,
                            {"$divide": ["$trips_with_tip", "$total_trips"]}
                        ]
                    },
                    2
                ]
            }
        }
    },
    {
        "$sort": {"total_trips": -1}
    }
]

start = time.perf_counter()

results = list(
    db.trips.aggregate(pipeline, allowDiskUse=True)
)

end = time.perf_counter()

print("\nPayment Methods and Tipping Patterns (2025)")
print("-" * 75)

for result in results:
    print(result)

print("\nTotal payment methods:", len(results))
print("Execution time:", round(end - start, 4), "seconds")

client.close()