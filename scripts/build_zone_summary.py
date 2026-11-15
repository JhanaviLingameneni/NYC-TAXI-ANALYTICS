"""
NYC Taxi Analytics - build the zone_summary collection (Phase II-B)

Derives one document per pickup zone from the trips collection, with an
hourly_stats ARRAY holding one entry per hour of day (0-23) that had at
least one 2025 pickup in that zone. Every value is computed from source
trip fields; nothing is invented.

Run after scripts/load_mongo.py:
    python scripts/build_zone_summary.py
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient


MONGO_URI = "mongodb://localhost:27017"
DATABASE = "nyc_taxi_analytics"
RESULTS_DIR = Path("results")

PIPELINE = [
    # Same date filter as the SQL queries.
    {
        "$match": {
            "pickup.datetime": {
                "$gte": datetime(2025, 1, 1),
                "$lt": datetime(2026, 1, 1),
            },
            "pickup.location_id": {"$exists": True},
        }
    },
    # One group per (zone, hour of day).
    {
        "$group": {
            "_id": {
                "location_id": "$pickup.location_id",
                "hour": {"$hour": "$pickup.datetime"},
            },
            "trips": {"$sum": 1},
            "avg_distance": {"$avg": "$trip_distance"},
            "avg_total_amount": {"$avg": "$fare.total_amount"},
            "avg_duration_min": {
                # Date subtraction gives milliseconds.
                "$avg": {
                    "$subtract": [
                        "$dropoff.datetime",
                        "$pickup.datetime",
                    ]
                }
            },
        }
    },
    {"$sort": {"_id.location_id": 1, "_id.hour": 1}},
    # Fold the 24 hourly rows of each zone into one array.
    {
        "$group": {
            "_id": "$_id.location_id",
            "total_trips": {"$sum": "$trips"},
            "hourly_stats": {
                "$push": {
                    "hour": "$_id.hour",
                    "trips": "$trips",
                    "avg_distance": {"$round": ["$avg_distance", 2]},
                    "avg_total_amount": {
                        "$round": ["$avg_total_amount", 2]
                    },
                    "avg_duration_min": {
                        "$round": [
                            {"$divide": ["$avg_duration_min", 60_000]},
                            2,
                        ]
                    },
                }
            },
        }
    },
    # Copy zone names in from the reference collection.
    {
        "$lookup": {
            "from": "taxi_zones",
            "localField": "_id",
            "foreignField": "_id",
            "as": "zone_info",
        }
    },
    {
        "$set": {
            "borough": {"$first": "$zone_info.borough"},
            "zone": {"$first": "$zone_info.zone"},
            "hours_with_pickups": {"$size": "$hourly_stats"},
        }
    },
    {"$unset": "zone_info"},
    {"$out": "zone_summary"},
]


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    client = MongoClient(MONGO_URI)
    db = client[DATABASE]

    print("Building zone_summary from trips (this scans all trips)...")
    start = time.perf_counter()

    db.trips.aggregate(PIPELINE, allowDiskUse=True)

    duration = time.perf_counter() - start
    zones = db.zone_summary.count_documents({})
    sample = db.zone_summary.find_one(
        {}, sort=[("total_trips", -1)]
    )

    result = {
        "collection": "zone_summary",
        "source_collection": "trips",
        "documents": zones,
        "build_seconds": round(duration, 3),
        "busiest_zone": {
            "location_id": sample["_id"],
            "zone": sample.get("zone"),
            "total_trips": sample["total_trips"],
        },
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    output = RESULTS_DIR / "mongo_zone_summary_build.json"
    output.write_text(json.dumps(result, indent=2))

    print(f"zone_summary: {zones} documents in {duration:.1f} s")
    print(f"Busiest zone: {sample.get('zone')} "
          f"({sample['total_trips']:,} trips)")
    print(f"Metrics saved to {output}")

    client.close()


if __name__ == "__main__":
    main()
