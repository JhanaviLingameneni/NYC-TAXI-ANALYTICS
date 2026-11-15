
from pathlib import Path
import pyarrow.parquet as pq

data_dir = Path("data")
files = sorted(data_dir.glob("yellow_tripdata_2025-*.parquet"))

total = 0

print(f"{'Month':<12} {'Records':>15}")
print("-" * 29)

for file in files:
    parquet = pq.ParquetFile(file)
    count = parquet.metadata.num_rows

    total += count

    print(f"{file.stem[-7:]:<12} {count:>15,}")

print("-" * 29)
print(f"{'TOTAL':<12} {total:>15,}")

print(f"\nRemaining to 50M: {max(0, 50_000_000 - total):,}")
