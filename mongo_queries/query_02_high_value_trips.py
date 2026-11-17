from datetime import datetime
from time import perf_counter
from pprint import pprint

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["nyc_taxi_analytics"]

pipeline = [
    {
        "$match": {
            "fare.total_amount": {"$gt": 100},
            "pickup.datetime": {
                "$gte": datetime(2025, 1, 1),
                "$lt": datetime(2026, 1, 1)
            }
        }
    },
    {
        "$sort": {
            "fare.total_amount": -1
        }
    },
    {
        "$limit": 100
    },
    {
        "$lookup": {
            "from": "taxi_zones",
            "localField": "pickup.location_id",
            "foreignField": "_id",
            "as": "pickup_zone"
        }
    },
    {
        "$unwind": "$pickup_zone"
    },
    {
        "$project": {
            "_id": 1,
            "pickup_datetime": "$pickup.datetime",
            "borough": "$pickup_zone.borough",
            "pickup_zone": "$pickup_zone.zone",
            "trip_distance": {"$round": ["$trip_distance", 2]},
            "total_amount": {"$round": ["$fare.total_amount", 2]}
        }
    }
]

start = perf_counter()
results = list(db.trips.aggregate(pipeline, allowDiskUse=True))
execution_time = perf_counter() - start

print("\nTop 100 High-Value Taxi Trips\n")
for i, trip in enumerate(results, 1):
    print(f"\n{i}.")
    pprint(trip)

print(f"\nReturned records: {len(results)}")
print(f"Execution time: {execution_time:.4f} seconds")

client.close()