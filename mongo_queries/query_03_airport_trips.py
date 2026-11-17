
from pymongo import MongoClient
from datetime import datetime
import time

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["nyc_taxi_analytics"]

# Airport pickup analysis
pipeline = [
    {
        "$match": {
            "pickup.location_id": {"$in": [1, 132, 138]},
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
            "avg_total_amount": {"$avg": "$fare.total_amount"},
            "total_revenue": {"$sum": "$fare.total_amount"}
        }
    },
    {
        "$lookup": {
            "from": "taxi_zones",
            "localField": "_id",
            "foreignField": "_id",
            "as": "airport_info"
        }
    },
    {"$unwind": "$airport_info"},
    {
        "$project": {
            "_id": 0,
            "airport": "$airport_info.zone",
            "total_trips": 1,
            "avg_trip_distance": {
                "$round": ["$avg_trip_distance", 2]
            },
            "avg_total_amount": {
                "$round": ["$avg_total_amount", 2]
            },
            "total_revenue": {
                "$round": ["$total_revenue", 2]
            }
        }
    },
    {"$sort": {"total_trips": -1}}
]

# Measure execution time
start = time.perf_counter()

results = list(db.trips.aggregate(pipeline, allowDiskUse=True))

end = time.perf_counter()

# Display results
print("\nQUERY 3: AIRPORT PICKUP ANALYSIS")
print("-" * 75)

for result in results:
    print(result)

print("-" * 75)
print("Airports returned:", len(results))
print(f"Execution time: {end - start:.4f} seconds")

client.close()

