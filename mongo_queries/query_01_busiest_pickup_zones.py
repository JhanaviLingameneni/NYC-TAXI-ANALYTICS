
from pymongo import MongoClient
from datetime import datetime
from time import perf_counter
from pprint import pprint

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
            "_id": "$pickup.location_id",
            "total_trips": {"$sum": 1},
            "avg_trip_distance": {"$avg": "$trip_distance"},
            "avg_trip_amount": {"$avg": "$fare.total_amount"}
        }
    },
    {
        "$lookup": {
            "from": "taxi_zones",
            "localField": "_id",
            "foreignField": "_id",
            "as": "zone_info"
        }
    },
    {"$unwind": "$zone_info"},
    {
        "$project": {
            "_id": 0,
            "borough": "$zone_info.borough",
            "zone": "$zone_info.zone",
            "total_trips": 1,
            "avg_trip_distance": {
                "$round": ["$avg_trip_distance", 2]
            },
            "avg_trip_amount": {
                "$round": ["$avg_trip_amount", 2]
            }
        }
    },
    {"$sort": {"total_trips": -1}},
    {"$limit": 10}
]

start = perf_counter()
results = list(db.trips.aggregate(pipeline, allowDiskUse=True))
elapsed = perf_counter() - start

print("\nTop 10 Busiest Pickup Zones")
print("=" * 60)

for result in results:
    pprint(result)

print(f"\nExecution time: {elapsed:.4f} seconds")

client.close()
