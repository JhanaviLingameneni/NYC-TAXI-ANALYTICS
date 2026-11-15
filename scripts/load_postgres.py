
import csv
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
import psycopg

DATA_FILE = Path("data/yellow_tripdata_2025-01.parquet")
RESULT_FILE = Path("results/postgres_load_january.json")
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

COPY_SQL = """
COPY taxi_trips (
    vendor_id, pickup_datetime, dropoff_datetime,
    passenger_count, trip_distance, rate_code_id,
    store_and_fwd_flag, pickup_location_id,
    dropoff_location_id, payment_type_id,
    fare_amount, extra, mta_tax, tip_amount,
    tolls_amount, improvement_surcharge,
    total_amount, congestion_surcharge,
    airport_fee, cbd_congestion_fee
)
FROM STDIN WITH (FORMAT CSV, NULL '\\N')
"""

def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(DATA_FILE)

    parquet = pq.ParquetFile(DATA_FILE)
    expected_rows = parquet.metadata.num_rows

    started = time.perf_counter()
    inserted = 0

    with psycopg.connect(
        "dbname=nyc_taxi_analytics"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM taxi_trips")
            existing = cur.fetchone()[0]

            if existing != 0:
                raise RuntimeError(
                    f"taxi_trips already contains {existing} rows. "
                    "Stopping to prevent duplicate imports."
                )

            for batch in parquet.iter_batches(
                batch_size=BATCH_SIZE,
                columns=COLUMNS
            ):
                df = batch.to_pandas()

                # Preserve nullable integer columns
                integer_columns = [
                    "VendorID",
                    "passenger_count",
                    "RatecodeID",
                    "PULocationID",
                    "DOLocationID",
                    "payment_type",
                ]

                for column in integer_columns:
                    df[column] = df[column].astype("Int64")

                buffer = io.StringIO()
                writer = csv.writer(buffer)

                for row in df.itertuples(
                    index=False, name=None
                ):
                    writer.writerow([
                        "\\N" if value is None
                        or __import__("pandas").isna(value)
                        else value
                        for value in row
                    ])

                buffer.seek(0)

                with cur.copy(COPY_SQL) as copy:
                    while chunk := buffer.read(1024 * 1024):
                        copy.write(chunk)

                inserted += len(df)
                print(
                    f"Loaded {inserted:,} / "
                    f"{expected_rows:,} rows"
                )

        # Commit after all batches succeed
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM taxi_trips")
            verified_rows = cur.fetchone()[0]

    elapsed = time.perf_counter() - started

    if verified_rows != expected_rows:
        raise RuntimeError(
            f"Row count mismatch: expected {expected_rows}, "
            f"found {verified_rows}"
        )

    report = {
        "dataset": DATA_FILE.name,
        "database": "nyc_taxi_analytics",
        "table": "taxi_trips",
        "expected_rows": expected_rows,
        "inserted_rows": inserted,
        "verified_rows": verified_rows,
        "batch_size": BATCH_SIZE,
        "duration_seconds": round(elapsed, 3),
        "rows_per_second": round(
            inserted / elapsed, 2
        ),
        "completed_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "success",
    }

    RESULT_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )
    RESULT_FILE.write_text(
        json.dumps(report, indent=2)
    )

    print("\nImport completed successfully!")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
