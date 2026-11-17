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
            "_id": {"$hour": "$pickup.datetime"},
            "total_trips": {"$sum": 1},
            "avg_trip_distance": {"$avg": "$trip_distance"},
            "avg_total_amount": {"$avg": "$fare.total_amount"}
        }
    },
    {
        "$project": {
            "_id": 0,
            "pickup_hour": "$_id",
            "total_trips": 1,
            "avg_trip_distance": {
                "$round": ["$avg_trip_distance", 2]
            },
            "avg_total_amount": {
                "$round": ["$avg_total_amount", 2]
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

print("\nPeak-Hour Taxi Demand (2025)")
print("-" * 65)

for result in results:
    print(result)

print("\nTotal hours:", len(results))
print("Execution time:", round(end - start, 4), "seconds")

client.close()
