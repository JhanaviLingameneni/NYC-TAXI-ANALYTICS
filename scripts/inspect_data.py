
import pyarrow.parquet as pq

file_path = "data/yellow_tripdata_2025-01.parquet"

# Read Parquet metadata without loading all records
parquet_file = pq.ParquetFile(file_path)

print("Total records:", parquet_file.metadata.num_rows)
print("Total columns:", len(parquet_file.schema.names))

print("\nDataset Schema:")
print(parquet_file.schema)

# Load only the first 5 rows
first_batch = next(parquet_file.iter_batches(batch_size=5))
print("\nSample Records:")
print(first_batch.to_pandas().to_string(index=False))
