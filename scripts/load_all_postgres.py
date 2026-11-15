
import csv
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import psycopg


# Configuration
DATABASE = "nyc_taxi_analytics"
DATA_DIR = Path("data")
RESULTS_DIR = Path("results")
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

INTEGER_COLUMNS = [
    "VendorID",
    "passenger_count",
    "RatecodeID",
    "PULocationID",
    "DOLocationID",
    "payment_type",
]

COPY_SQL = """
COPY taxi_trips (
    vendor_id,
    pickup_datetime,
    dropoff_datetime,
    passenger_count,
    trip_distance,
    rate_code_id,
    store_and_fwd_flag,
    pickup_location_id,
    dropoff_location_id,
    payment_type_id,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    total_amount,
    congestion_surcharge,
    airport_fee,
    cbd_congestion_fee
)
FROM STDIN WITH (FORMAT CSV, NULL '\\N')
"""


def already_imported(conn, filename):
    """Check whether a file was previously imported."""

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT imported_rows
            FROM import_history
            WHERE filename = %s
              AND status = 'success'
            """,
            (filename,),
        )

        return cur.fetchone()


def import_file(conn, path):
    """Import one Parquet file into PostgreSQL."""

    filename = path.name
    parquet = pq.ParquetFile(path)
    expected = parquet.metadata.num_rows

    print(f"\nImporting {filename}")
    print(f"Expected rows: {expected:,}")

    inserted = 0
    start = time.perf_counter()

    try:
        with conn.cursor() as cur:

            # Count existing records before importing.
            cur.execute(
                "SELECT COUNT(*) FROM taxi_trips"
            )
            rows_before = cur.fetchone()[0]

            # Read the Parquet file in batches.
            for batch in parquet.iter_batches(
                batch_size=BATCH_SIZE,
                columns=COLUMNS,
            ):
                df = batch.to_pandas()

                # Preserve nullable integer columns.
                for column in INTEGER_COLUMNS:
                    df[column] = df[column].astype("Int64")

                # Convert the batch into CSV data.
                buffer = io.StringIO()
                writer = csv.writer(buffer)

                for row in df.itertuples(
                    index=False,
                    name=None,
                ):
                    writer.writerow([
                        "\\N" if pd.isna(value) else value
                        for value in row
                    ])

                buffer.seek(0)

                # Bulk load using PostgreSQL COPY.
                with cur.copy(COPY_SQL) as copy:
                    while True:
                        chunk = buffer.read(1024 * 1024)

                        if not chunk:
                            break

                        copy.write(chunk)

                inserted += len(df)

                print(
                    f"Loaded {inserted:,} / {expected:,} rows",
                    end="\r",
                    flush=True,
                )

            # Verify the number of processed records.
            if inserted != expected:
                raise ValueError(
                    f"Row mismatch for {filename}: "
                    f"expected {expected:,}, "
                    f"inserted {inserted:,}"
                )

            # Verify the database row-count increase.
            cur.execute(
                "SELECT COUNT(*) FROM taxi_trips"
            )
            rows_after = cur.fetchone()[0]

            verified_rows = rows_after - rows_before

            if verified_rows != expected:
                raise ValueError(
                    f"Database verification failed for "
                    f"{filename}: expected {expected:,}, "
                    f"found {verified_rows:,}"
                )

            # Save the import record in the same transaction.
            duration = time.perf_counter() - start

            cur.execute(
                """
                INSERT INTO import_history (
                    filename,
                    expected_rows,
                    imported_rows,
                    duration_seconds,
                    status
                )
                VALUES (%s, %s, %s, %s, 'success')
                """,
                (
                    filename,
                    expected,
                    inserted,
                    duration,
                ),
            )

        # Commit both the data and import history.
        conn.commit()

    except Exception:
        # Roll back this file if anything fails.
        conn.rollback()
        print(f"\nImport failed: {filename}")
        raise

    duration = time.perf_counter() - start

    result = {
        "dataset": filename,
        "database": DATABASE,
        "table": "taxi_trips",
        "expected_rows": expected,
        "inserted_rows": inserted,
        "verified_rows": verified_rows,
        "batch_size": BATCH_SIZE,
        "duration_seconds": round(duration, 3),
        "rows_per_second": round(
            inserted / duration, 2
        ),
        "completed_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "success",
    }

    print(
        f"\nCompleted {filename} "
        f"in {duration:.2f} seconds"
    )

    print(
        f"Throughput: "
        f"{result['rows_per_second']:,.2f} rows/second"
    )

    return result


def main():
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = sorted(
        DATA_DIR.glob(
            "yellow_tripdata_2025-*.parquet"
        )
    )

    if not files:
        raise FileNotFoundError(
            "No 2025 Parquet files found in data/"
        )

    print("NYC Taxi PostgreSQL Bulk Loader")
    print("--------------------------------")
    print(f"Files found: {len(files)}")
    print(f"Batch size: {BATCH_SIZE:,}")

    with psycopg.connect(
        f"dbname={DATABASE}"
    ) as conn:

        for path in files:

            # Check the import history.
            previous = already_imported(
                conn,
                path.name,
            )

            # End the read transaction.
            conn.commit()

            if previous:
                print(
                    f"Skipping {path.name}: "
                    f"already imported "
                    f"({previous[0]:,} rows)"
                )
                continue

            # Import and verify this file.
            result = import_file(
                conn,
                path,
            )

            # Save performance measurements.
            output = RESULTS_DIR / (
                f"postgres_load_{path.stem[-7:]}.json"
            )

            output.write_text(
                json.dumps(
                    result,
                    indent=2,
                )
            )

            print(
                f"Metrics saved to {output}"
            )

    print("\nAll available files processed successfully!")

    # Final verification of imported files.
    with psycopg.connect(
        f"dbname={DATABASE}"
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    COUNT(*),
                    COALESCE(SUM(imported_rows), 0)
                FROM import_history
                WHERE status = 'success'
                """
            )

            completed_files, tracked_rows = (
                cur.fetchone()
            )

            cur.execute(
                "SELECT COUNT(*) FROM taxi_trips"
            )

            database_rows = cur.fetchone()[0]

    print("\n=== FINAL IMPORT SUMMARY ===")
    print(f"Files imported: {completed_files}")
    print(f"Tracked rows: {tracked_rows:,}")
    print(f"Database rows: {database_rows:,}")

    if database_rows == tracked_rows:
        print("Verification: PASSED")
    else:
        print("Verification: FAILED")
        raise ValueError(
            "Database row count does not match "
            "import history."
        )


if __name__ == "__main__":
    main()
