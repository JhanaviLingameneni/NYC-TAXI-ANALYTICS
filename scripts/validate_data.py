
import json
from pathlib import Path

import pyarrow.parquet as pq
import pandas as pd

DATA_FILE = Path("data/yellow_tripdata_2025-01.parquet")
OUTPUT_FILE = Path("results/january_validation.json")

columns = [
    "VendorID",
    "RatecodeID",
    "payment_type",
    "PULocationID",
    "DOLocationID",
    "passenger_count",
    "trip_distance",
    "fare_amount",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
]

table = pq.read_table(DATA_FILE, columns=columns)
df = table.to_pandas()

print("Total records:", len(df))

print("\nMissing values:")
missing = df.isnull().sum()
print(missing.to_string())

category_columns = [
    "VendorID",
    "RatecodeID",
    "payment_type",
    "PULocationID",
    "DOLocationID",
]

category_values = {}

for column in category_columns:
    values = sorted(df[column].dropna().unique().tolist())
    category_values[column] = [
        int(value) for value in values
    ]

    print(f"\n{column}:")
    print(category_values[column])

invalid = {
    "negative_distance": int((df["trip_distance"] < 0).sum()),
    "negative_fare": int((df["fare_amount"] < 0).sum()),
    "dropoff_before_pickup": int((
        df["tpep_dropoff_datetime"]
        < df["tpep_pickup_datetime"]
    ).sum()),
}

print("\nPotentially invalid records:")
print(json.dumps(invalid, indent=2))

report = {
    "dataset": DATA_FILE.name,
    "total_records": len(df),
    "missing_values": {
        key: int(value)
        for key, value in missing.items()
    },
    "category_values": category_values,
    "potentially_invalid": invalid,
}

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w") as file:
    json.dump(report, file, indent=2)

print(f"\nValidation report saved to {OUTPUT_FILE}")
