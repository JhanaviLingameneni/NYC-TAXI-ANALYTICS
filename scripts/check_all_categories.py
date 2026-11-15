
from pathlib import Path
import pyarrow.parquet as pq

DATA_DIR = Path("data")

COLUMNS = [
    "VendorID",
    "RatecodeID",
    "payment_type",
    "PULocationID",
    "DOLocationID",
]

all_values = {column: set() for column in COLUMNS}
missing_counts = {column: 0 for column in COLUMNS}

files = sorted(DATA_DIR.glob("yellow_tripdata_2025-*.parquet"))

for file in files:
    print(f"Checking {file.name}...")

    parquet = pq.ParquetFile(file)

    for batch in parquet.iter_batches(
        batch_size=100_000,
        columns=COLUMNS
    ):
        for column in COLUMNS:
            values = batch.column(
                batch.schema.get_field_index(column)
            ).to_pylist()

            for value in values:
                if value is None:
                    missing_counts[column] += 1
                else:
                    all_values[column].add(int(value))

print("\n=== CATEGORY SUMMARY ===")

for column in COLUMNS:
    values = sorted(all_values[column])

    if column in ["PULocationID", "DOLocationID"]:
        print(f"\n{column}:")
        print(f"Distinct IDs: {len(values)}")
        print(f"Outside 1-265: {[v for v in values if not 1 <= v <= 265]}")
    else:
        print(f"\n{column}: {values}")

    print(f"Missing values: {missing_counts[column]:,}")
