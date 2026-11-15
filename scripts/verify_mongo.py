"""
NYC Taxi Analytics - verify the MongoDB load (Phase II-B)

Checks counts against import_history and the PostgreSQL totals, field
types on a random sample, indexes, and prints one sample document per
collection. Writes results/mongo_verification.json.

    python scripts/verify_mongo.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util
from pymongo import MongoClient


MONGO_URI = "mongodb://localhost:27017"
DATABASE = "nyc_taxi_analytics"
RESULTS_DIR = Path("results")
EXPECTED_TOTAL = 48_722_602  # PostgreSQL / Parquet total for 2025

# Field path -> allowed BSON types (missing = was NULL in the source).
TYPE_CHECKS = {
    "pickup.datetime": ["date"],
    "dropoff.datetime": ["date"],
    "pickup.location_id": ["int"],
    "dropoff.location_id": ["int"],
    "trip_distance": ["double"],
    "passenger_count": ["int", "long"],
    "fare.total_amount": ["double"],
    "payment.type_id": ["int"],
}


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    client = MongoClient(MONGO_URI)
    db = client[DATABASE]
    report = {"database": DATABASE}

    # 1. Counts
    trips = db.trips.count_documents({})
    imported = sum(
        h["imported_rows"]
        for h in db.import_history.find({"status": "success"})
    )

    report["counts"] = {
        "trips": trips,
        "import_history_total": imported,
        "expected_total": EXPECTED_TOTAL,
        "matches_postgres": trips == EXPECTED_TOTAL,
        "taxi_zones": db.taxi_zones.count_documents({}),
        "zone_summary": db.zone_summary.count_documents({}),
    }

    per_month = list(db.trips.aggregate([
        {"$group": {"_id": "$source_month", "rows": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]))
    report["rows_per_month"] = {m["_id"]: m["rows"] for m in per_month}

    # 2. Types on a random sample of 100,000 trips
    type_report = {}
    for field, allowed in TYPE_CHECKS.items():
        counts = list(db.trips.aggregate([
            {"$sample": {"size": 100_000}},
            {"$group": {"_id": {"$type": f"${field}"}, "n": {"$sum": 1}}},
        ]))
        found = {c["_id"]: c["n"] for c in counts}
        bad = {
            t: n for t, n in found.items()
            if t not in allowed and t != "missing"
        }
        type_report[field] = {"found": found, "ok": not bad}

    report["type_checks_sample_100k"] = type_report

    # 3. Indexes
    report["indexes"] = {
        name: [ix["key"] for ix in db[name].list_indexes()]
        for name in ("trips", "taxi_zones", "zone_summary")
    }

    # 4. Storage
    stats = db.command("collstats", "trips")
    report["trips_storage_mb"] = {
        "data_size": round(stats["size"] / 1e6, 1),
        "storage_size": round(stats["storageSize"] / 1e6, 1),
        "avg_document_bytes": stats.get("avgObjSize"),
    }

    # 5. Sample documents
    report["samples"] = {
        "trips": db.trips.find_one({"payment.type_id": 1}),
        "taxi_zones": db.taxi_zones.find_one({"_id": 132}),
        "zone_summary": db.zone_summary.find_one(
            {}, sort=[("total_trips", -1)]
        ),
    }

    report["verified_at_utc"] = datetime.now(timezone.utc).isoformat()

    output = RESULTS_DIR / "mongo_verification.json"
    output.write_text(json_util.dumps(report, indent=2))

    print(json.dumps(report["counts"], indent=2))
    print("Type checks:",
          "all ok" if all(v["ok"] for v in type_report.values())
          else "PROBLEMS - see report")
    print(f"Full report saved to {output}")

    client.close()


if __name__ == "__main__":
    main()
