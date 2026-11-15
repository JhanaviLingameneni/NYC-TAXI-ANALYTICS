"""
NYC Taxi Analytics - MongoDB bulk loader (Phase II-B)

Loads the same 2025 Yellow Taxi Parquet files used for PostgreSQL into
MongoDB, using a document model instead of a copy of the SQL tables:

  trips          one document per trip; vendor, rate code and payment
                 descriptions plus all fare components are embedded
  taxi_zones     one document per TLC taxi zone (reference collection,
                 joined from trips with $lookup)
  import_history one document per imported Parquet file

Usage (from the repo root):
    python scripts/load_mongo.py

Requires: data/yellow_tripdata_2025-*.parquet, data/taxi_zone_lookup.csv
"""

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
from pymongo import ASCENDING, MongoClient


# Configuration
MONGO_URI = "mongodb://localhost:27017"
DATABASE = "nyc_taxi_analytics"
DATA_DIR = Path("data")
RESULTS_DIR = Path("results")
ZONE_FILE = DATA_DIR / "taxi_zone_lookup.csv"
BATCH_SIZE = 50_000

COLUMNS = [
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "RatecodeID",
    "store_and_fwd_flag",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "fare_amount",
    "extra",
    "mta_tax",
    "tip_amount",
    "tolls_amount",
    "improvement_surcharge",
    "total_amount",
    "congestion_surcharge",
    "Airport_fee",
    "cbd_congestion_fee",
]

# Same reference values as sql/seed_lookups.sql, embedded into each trip.
VENDORS = {
    1: "Creative Mobile Technologies",
    2: "VeriFone Inc.",
    6: "Vendor 6 - Description Unverified",
    7: "Vendor 7 - Description Unverified",
}

PAYMENT_TYPES = {
    0: "Flex Fare trip",
    1: "Credit card",
    2: "Cash",
    3: "No charge",
    4: "Dispute",
    5: "Unknown",
    6: "Voided trip",
}

RATE_CODES = {
    1: "Standard rate",
    2: "JFK",
    3: "Newark",
    4: "Nassau or Westchester",
    5: "Negotiated fare",
    6: "Group ride",
    99: "Unknown",
}

# Parquet column -> field name inside the embedded "fare" subdocument.
FARE_FIELDS = {
    "fare_amount": "fare_amount",
    "extra": "extra",
    "mta_tax": "mta_tax",
    "tip_amount": "tip_amount",
    "tolls_amount": "tolls_amount",
    "improvement_surcharge": "improvement_surcharge",
    "congestion_surcharge": "congestion_surcharge",
    "Airport_fee": "airport_fee",
    "cbd_congestion_fee": "cbd_congestion_fee",
    "total_amount": "total_amount",
}


def to_int(value):
    """Parquet stores some integer codes as doubles; keep them as ints."""

    if value is None:
        return None

    return int(value)


def lookup(code, table):
    """Embed a coded value as {id, description}; None if code is missing."""

    if code is None:
        return None

    return {
        "id": code,
        "description": table.get(code, "Unrecognized code"),
    }


def drop_nulls(doc):
    """Omit missing values instead of storing nulls (MongoDB convention).

    $avg/$sum ignore missing fields the same way SQL AVG/SUM ignore NULL,
    so aggregations stay comparable with the PostgreSQL queries.
    """

    return {k: v for k, v in doc.items() if v is not None}


def build_trip(row, source_month):
    """Turn one Parquet row (dict) into one trip document."""

    pickup = drop_nulls({
        "datetime": row["tpep_pickup_datetime"],
        "location_id": to_int(row["PULocationID"]),
    })

    dropoff = drop_nulls({
        "datetime": row["tpep_dropoff_datetime"],
        "location_id": to_int(row["DOLocationID"]),
    })

    fare = drop_nulls({
        name: row[column]
        for column, name in FARE_FIELDS.items()
    })

    payment_code = to_int(row["payment_type"])
    payment = None

    if payment_code is not None:
        payment = {
            "type_id": payment_code,
            "method": PAYMENT_TYPES.get(
                payment_code, "Unrecognized code"
            ),
        }

    return drop_nulls({
        "source_month": source_month,
        "vendor": lookup(to_int(row["VendorID"]), VENDORS),
        "pickup": pickup,
        "dropoff": dropoff,
        "passenger_count": to_int(row["passenger_count"]),
        "trip_distance": row["trip_distance"],
        "rate_code": lookup(to_int(row["RatecodeID"]), RATE_CODES),
        "store_and_fwd_flag": row["store_and_fwd_flag"],
        "payment": payment,
        "fare": fare,
    })


def load_zones(db):
    """Load the TLC taxi zone lookup into the taxi_zones collection."""

    if not ZONE_FILE.exists():
        raise FileNotFoundError(
            f"{ZONE_FILE} not found. Download taxi_zone_lookup.csv "
            "from the TLC Trip Record Data page."
        )

    with ZONE_FILE.open(newline="") as f:
        zones = [
            {
                "_id": int(r["LocationID"]),
                "borough": r["Borough"],
                "zone": r["Zone"],
                "service_zone": r["service_zone"],
            }
            for r in csv.DictReader(f)
        ]

    db.taxi_zones.drop()
    db.taxi_zones.insert_many(zones)
    print(f"Loaded {len(zones)} taxi zones")


def import_file(db, path):
    """Import one Parquet file into the trips collection."""

    filename = path.name
    source_month = path.stem[-7:]  # e.g. "2025-01"
    parquet = pq.ParquetFile(path)
    expected = parquet.metadata.num_rows

    print(f"\nImporting {filename}")
    print(f"Expected rows: {expected:,}")

    # Remove leftovers from an earlier failed run of this file.
    removed = db.trips.delete_many(
        {"source_month": source_month}
    ).deleted_count

    if removed:
        print(f"Removed {removed:,} rows from an earlier partial run")

    rows_before = db.trips.estimated_document_count()
    inserted = 0
    start = time.perf_counter()

    for batch in parquet.iter_batches(
        batch_size=BATCH_SIZE,
        columns=COLUMNS,
    ):
        docs = [
            build_trip(row, source_month)
            for row in batch.to_pylist()
        ]

        result = db.trips.insert_many(docs, ordered=False)
        inserted += len(result.inserted_ids)

        print(
            f"Loaded {inserted:,} / {expected:,} rows",
            end="\r",
            flush=True,
        )

    if inserted != expected:
        raise ValueError(
            f"Row mismatch for {filename}: "
            f"expected {expected:,}, inserted {inserted:,}"
        )

    rows_after = db.trips.estimated_document_count()
    verified_rows = rows_after - rows_before

    if verified_rows != expected:
        raise ValueError(
            f"Database verification failed for {filename}: "
            f"expected {expected:,}, found {verified_rows:,}"
        )

    duration = time.perf_counter() - start

    db.import_history.replace_one(
        {"_id": filename},
        {
            "_id": filename,
            "expected_rows": expected,
            "imported_rows": inserted,
            "duration_seconds": duration,
            "imported_at": datetime.now(timezone.utc),
            "status": "success",
        },
        upsert=True,
    )

    result = {
        "dataset": filename,
        "database": DATABASE,
        "collection": "trips",
        "expected_rows": expected,
        "inserted_rows": inserted,
        "verified_rows": verified_rows,
        "batch_size": BATCH_SIZE,
        "duration_seconds": round(duration, 3),
        "rows_per_second": round(inserted / duration, 2),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "success",
    }

    print(f"\nCompleted {filename} in {duration:.2f} seconds")
    print(f"Throughput: {result['rows_per_second']:,.2f} rows/second")

    return result


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(DATA_DIR.glob("yellow_tripdata_2025-*.parquet"))

    if not files:
        raise FileNotFoundError("No 2025 Parquet files found in data/")

    print("NYC Taxi MongoDB Bulk Loader")
    print("----------------------------")
    print(f"Files found: {len(files)}")
    print(f"Batch size: {BATCH_SIZE:,}")

    client = MongoClient(MONGO_URI)
    db = client[DATABASE]

    load_zones(db)

    # Small index so a failed month can be found and removed quickly.
    db.trips.create_index([("source_month", ASCENDING)])

    for path in files:
        previous = db.import_history.find_one(
            {"_id": path.name, "status": "success"}
        )

        if previous:
            print(
                f"Skipping {path.name}: already imported "
                f"({previous['imported_rows']:,} rows)"
            )
            continue

        result = import_file(db, path)

        output = RESULTS_DIR / f"mongo_load_{path.stem[-7:]}.json"
        output.write_text(json.dumps(result, indent=2))
        print(f"Metrics saved to {output}")

    total = db.trips.estimated_document_count()
    print(f"\nAll files processed. trips collection: {total:,} documents")

    client.close()


if __name__ == "__main__":
    main()
