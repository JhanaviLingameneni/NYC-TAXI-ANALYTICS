# NYC Taxi Analytics — Dataset Inspection and PostgreSQL Performance Report

**Project:** Large-Scale NYC Taxi Analytics  
**Dataset:** NYC TLC Yellow Taxi Trip Records (2025)  
**Database:** PostgreSQL  
**Responsibility:** Member 1 — Dataset Collection, Relational Modeling, SQL Queries, and Indexing  
**Status:** Completed

---

## 1. Dataset Information

The dataset was collected from the New York City Taxi and Limousine Commission (NYC TLC).

| Metric | Value |
|---|---|
| Dataset | Yellow Taxi Trip Records |
| Year | 2025 |
| Source | NYC Taxi and Limousine Commission |
| Format | Apache Parquet |
| Total monthly files | 12 |
| Combined file size | Approximately 867 MB |
| Total records | 48,722,602 |
| Dataset columns | 21 (based on published schema) |
| Inspection tools | Python, PyArrow, Pandas |

**Source:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

The dataset contains information about taxi pickup and drop-off times, passenger counts, trip distances, locations, payment methods, fares, tips, and surcharges.

The 2025 dataset also includes the `cbd_congestion_fee` field.

## 2. Full-Year Dataset Collection

All twelve monthly Yellow Taxi Parquet files for 2025 were downloaded and inspected.

### Monthly Record Counts

| Month | Records |
|---|---:|
| January | 3,475,226 |
| February | 3,577,543 |
| March | 4,145,257 |
| April | 3,970,553 |
| May | 4,591,845 |
| June | 4,322,960 |
| July | 3,898,963 |
| August | 3,574,091 |
| September | 4,251,015 |
| October | 4,428,699 |
| November | 4,181,444 |
| December | 4,305,006 |
| **Total** | **48,722,602** |

### Dataset Size Requirement

The project requires approximately 50 million records.

The collected dataset contains 48,722,602 records, representing **97.45% of the target**.

The complete 2025 dataset was selected to preserve year-round patterns and support seasonal, geographical, and financial analysis.

## 3. Dataset Schema

The published 2025 Yellow Taxi schema contains 21 columns.

### Trip Information

- `VendorID`
- `tpep_pickup_datetime`
- `tpep_dropoff_datetime`
- `passenger_count`
- `trip_distance`
- `RatecodeID`
- `store_and_fwd_flag`

### Location Information

- `PULocationID`
- `DOLocationID`

### Payment and Fare Information

- `payment_type`
- `fare_amount`
- `extra`
- `mta_tax`
- `tip_amount`
- `tolls_amount`
- `improvement_surcharge`
- `total_amount`
- `congestion_surcharge`
- `Airport_fee`
- `cbd_congestion_fee`

The fields support analysis of taxi demand, pickup locations, airport activity, trip distances, payment methods, and recorded tipping patterns.

## 4. Data Validation

### January 2025 Inspection

**Total records:** 3,475,226

### Missing Values

| Column | Missing records | Percentage |
|---|---:|---:|
| RatecodeID | 540,149 | 15.54% |
| passenger_count | 540,149 | 15.54% |

No missing values were identified in the other columns included in the initial January inspection.

### Category Validation

The observed categorical values included:

- Vendor IDs: 1, 2, 6, 7
- Rate codes: 1, 2, 3, 4, 5, 6, 99
- Payment types: 0, 1, 2, 3, 4, 5
- Pickup and drop-off location IDs: Within the official range of 1–265

### Potential Data-Quality Issues

| Issue | January records |
|---|---:|
| Negative trip distances | 0 |
| Negative fare amounts | 144,118 |
| Drop-off earlier than pickup | 124 |

These observations show that the original dataset contains unusual or potentially inconsistent records.

### Full-Year Validation

Across the complete dataset:

- All observed vendor IDs were supported by the reference table.
- All observed rate codes were supported by the reference table.
- All observed payment types were supported by the reference table.
- Pickup and drop-off location IDs were validated against the official taxi zone lookup.
- 11,611,894 records contained NULL rate codes, approximately 23.83% of the dataset.

### Data Handling Decisions

1. Preserve missing rate codes and passenger counts as NULL.
2. Retain negative fares for further investigation instead of deleting records.
3. Retain records with inconsistent timestamps.
4. Preserve the original trip data during loading.
5. Support all observed categorical IDs in the corresponding lookup tables.

The goal was to avoid losing information during the database import process.

## 5. PostgreSQL Relational Database Design

The dataset was organized into a relational database containing one main fact table and four lookup tables.

| Table | Description |
|---|---|
| `taxi_trips` | Individual taxi trip records |
| `vendors` | Vendor information |
| `payment_types` | Payment method descriptions |
| `rate_codes` | Rate code descriptions |
| `taxi_zones` | Taxi zone, borough, and service-zone information |

### Primary Keys

- `taxi_trips`: `trip_id`
- `vendors`: `vendor_id`
- `payment_types`: `payment_type_id`
- `rate_codes`: `rate_code_id`
- `taxi_zones`: `location_id`

The `taxi_trips` table references the lookup tables using foreign keys.

Both pickup and drop-off location IDs reference `taxi_zones`.

The official taxi zone lookup contains 265 records.

This design reduces repeated descriptive information and supports SQL joins.

Detailed functional dependencies and normalization are documented separately in `results/normalization.md`.

## 6. PostgreSQL Data Loading

The complete 2025 dataset was successfully imported into PostgreSQL.

### Loading Implementation

The loading program used:

- Python
- PyArrow
- Pandas
- psycopg
- PostgreSQL `COPY`

Parquet files were processed in batches of 50,000 records.

Each monthly file was imported in a separate transaction.

An `import_history` table was created to track successful imports and prevent duplicate loading.

### January Loading Results

| Metric | Value |
|---|---:|
| Records imported | 3,475,226 |
| Loading time | 190.489 seconds |
| Throughput | 18,243.69 records/second |
| Batch size | 50,000 |

### Final Loading Results

| Metric | Value |
|---|---:|
| Total monthly files imported | 12 |
| Total records imported | 48,722,602 |
| Verified PostgreSQL records | 48,722,602 |
| Total loading time | 2,532 seconds |
| Total loading duration | 42 minutes 12 seconds |
| Average throughput | Approximately 19,243 records/second |
| Import status | Successful |

The final database record count matched the sum of imported records recorded in `import_history`.

All 48,722,602 source records were accounted for in the database loading process.

## 7. SQL Query and Indexing Experiments

Five SQL queries were developed to analyze different aspects of the NYC Taxi dataset.

Each query was benchmarked using:

`EXPLAIN (ANALYZE, BUFFERS)`

The execution plans were saved before and after creating indexes.

The objective was to evaluate whether indexing could improve query performance on a dataset containing approximately 48.7 million records.

### Query 1 — Busiest Pickup Zones

**Objective:** Identify the ten busiest taxi pickup zones in NYC during 2025.

The query joins `taxi_trips` with `taxi_zones` and calculates trip counts, average distances, and average total amounts.

**Index tested:** `idx_taxi_pickup_analytics`

**Index definition:** B-tree index on `(pickup_datetime, pickup_location_id)` including `trip_distance` and `total_amount`.

| Metric | Before indexing | After indexing |
|---|---:|---:|
| Execution time | 24,618.694 ms | 23,675.466 ms |
| Scan method | Parallel Seq Scan | Parallel Seq Scan |
| New index used | No | No |

**Observation:**

PostgreSQL did not use the index because the query processes almost the entire dataset.

The observed execution time decreased by approximately 3.83%, but this difference cannot be directly attributed to the index.

**Decision:** Index removed.

**Conclusion:** Sequential scans can be more efficient for large aggregations involving most records.

### Query 2 — High-Value Taxi Trips

**Objective:** Identify the 100 most expensive taxi trips in 2025 and their pickup locations.

**Index:** `idx_taxi_high_value_trips`

**Index type:** Partial B-tree index on `total_amount DESC`, including pickup datetime, pickup location, and trip distance.

The index contains only trips where `total_amount > 100`.

| Metric | Before indexing | After indexing |
|---|---:|---:|
| Execution time | 19,452.444 ms | 13.367 ms |
| Scan method | Parallel Seq Scan | Index Scan |
| New index used | No | Yes |

**Index size:** 34 MB

**Observed improvement:**

- Approximately 1,455× speedup.
- Approximately 99.93% reduction in execution time.

**Explanation:**

Without the index, PostgreSQL scanned nearly the entire taxi trip table to identify expensive trips.

After indexing, PostgreSQL accessed high-value trips in descending order of total amount and retrieved the first 100 qualifying records directly.

This avoided scanning and sorting a large number of records.

**Decision:** Index retained.

**Conclusion:** Partial indexes can significantly improve selective queries involving filtering, sorting, and limiting results.

### Query 3 — Airport Pickup Analysis

**Objective:** Analyze taxi trips originating from JFK, LaGuardia, and Newark airports.

The query calculates total trips, average trip distance, average total amount, and summed trip amounts.

Airport location IDs used:

- JFK Airport: 132
- LaGuardia Airport: 138
- Newark Airport: 1

**Index:** `idx_taxi_airport_pickups`

**Index type:** Partial covering index on `(pickup_location_id, pickup_datetime)` including `trip_distance` and `total_amount`.

| Metric | Before indexing | After indexing |
|---|---:|---:|
| Execution time | 17,250.573 ms | 2,763.886 ms |
| Scan method | Parallel Seq Scan | Parallel Index Only Scan |
| New index used | No | Yes |

**Index size:** 159 MB

**Observed improvement:**

- Approximately 6.24× speedup.
- Approximately 83.98% reduction in execution time.

**Explanation:**

Before indexing, PostgreSQL scanned the entire taxi trip table to find airport pickup records.

After indexing, PostgreSQL used a parallel index-only scan to access the relevant airport trips more efficiently.

The execution plan reported 551,234 heap fetches, indicating that some table-page visibility checks were still required.

**Decision:** Index retained.

**Conclusion:** Partial covering indexes can improve analytical queries that access a limited subset of a large dataset.

### Query 4 — Peak-Hour Taxi Demand

**Objective:** Identify the hours of the day with the highest taxi pickup activity.

The query groups trips by pickup hour and calculates trip counts, average distances, and average total amounts.

**Index tested:** `idx_taxi_peak_hours`

**Index type:** Expression index on the extracted pickup hour, including pickup datetime, trip distance, and total amount.

| Metric | Before indexing | After indexing |
|---|---:|---:|
| Execution time | 42,894.444 ms | 24,609.841 ms |
| Scan method | Parallel Seq Scan | Parallel Seq Scan |
| New index used | No | No |

**Observation:**

PostgreSQL continued using a parallel sequential scan even after the index was created.

The query needs to process almost every trip to calculate hourly demand.

Although the second execution was approximately 42.6% faster, the index was not used. The difference may be related to caching, system conditions, or normal runtime variability.

**Decision:** Index removed.

**Conclusion:** Expression indexes do not necessarily improve full-table aggregations.

### Query 5 — Payment Methods and Tipping Patterns

**Objective:** Analyze taxi payment methods and recorded tipping behavior during 2025.

The query calculates:

- Total trips by payment method.
- Average fare.
- Average recorded tip.
- Average tip percentage relative to fare.
- Percentage of trips with a positive recorded tip.

**Index tested:** `idx_taxi_payment_tips`

**Index type:** Covering index on `payment_type_id`, including pickup datetime, fare amount, and tip amount.

| Metric | Before indexing | After indexing |
|---|---:|---:|
| Execution time | 23,861.232 ms | 27,332.124 ms |
| Scan method | Parallel Seq Scan | Parallel Seq Scan |
| New index used | No | No |

**Observation:**

PostgreSQL did not use the new index because the query aggregates nearly the entire dataset.

The second execution was approximately 14.5% slower, but the difference cannot be attributed to index usage.

The `payment_types` lookup table was small and inexpensive to scan.

**Decision:** Index removed.

**Conclusion:** A sequential scan can be more appropriate than an index for large-scale aggregation.

**Data limitation:** The TLC dataset records credit-card tips but does not include cash tips. Therefore, this analysis describes recorded tipping behavior rather than all tips received by drivers.

## 8. Overall SQL Performance Comparison

| Query | Before indexing (ms) | After indexing (ms) | Index used | Decision |
|---|---:|---:|---|---|
| Q1 — Pickup zones | 24,618.694 | 23,675.466 | No | Removed |
| Q2 — High-value trips | 19,452.444 | 13.367 | Yes | Retained |
| Q3 — Airport trips | 17,250.573 | 2,763.886 | Yes | Retained |
| Q4 — Peak hours | 42,894.444 | 24,609.841 | No | Removed |
| Q5 — Payment and tips | 23,861.232 | 27,332.124 | No | Removed |

### Main Findings

**1. Indexing was highly effective for selective queries.**

Query 2 showed the largest improvement because PostgreSQL could directly access the highest-value trips using a partial index.

**2. Partial covering indexes improved filtered analytical queries.**

Query 3 demonstrated that restricting an index to relevant airport records reduced the amount of data PostgreSQL needed to access.

**3. Indexing did not improve every query.**

Queries 1, 4, and 5 continued using parallel sequential scans because they processed most of the dataset.

**4. Unused indexes introduce unnecessary storage and maintenance overhead.**

The indexes for Queries 1, 4, and 5 were removed after their experiments.

**5. Index effectiveness depends on query structure and selectivity.**

Indexes were most beneficial when PostgreSQL could avoid scanning large portions of the table.

### Benchmark Limitations

All reported timings are actual measurements collected from PostgreSQL execution plans.

However, the comparisons are based on individual benchmark runs rather than repeated controlled trials.

Execution times may be affected by caching, concurrent system activity, disk access, and other environmental conditions.

Therefore, the reported speedups should be interpreted as observed experimental results rather than guaranteed performance improvements.

## 9. Final Index Decisions

The following indexes were retained:

| Index | Size | Purpose |
|---|---:|---|
| `idx_taxi_high_value_trips` | 34 MB | High-value trip retrieval |
| `idx_taxi_airport_pickups` | 159 MB | Airport pickup analytics |
| **Total** | **193 MB** | |

The following experimental indexes were removed:

- `idx_taxi_pickup_analytics`
- `idx_taxi_peak_hours`
- `idx_taxi_payment_tips`

The retained indexes demonstrated measurable benefits and were used in their corresponding execution plans.

## 10. Files and Reproducibility

### SQL Files

The `sql/` directory contains:

- Relational database schema.
- Import history table definition.
- Five SQL analytical queries.
- Index creation scripts for the five experiments.

### Python Scripts

The `scripts/` directory contains:

- PostgreSQL loading scripts.
- Data inspection and validation utilities.
- Monthly import processing logic.

### Results

The `results/` directory contains:

- Dataset inspection report.
- Normalization documentation.
- PostgreSQL loading statistics.
- Monthly import metrics.
- SQL query execution plans.
- Before-and-after indexing measurements.

The execution plans are stored under:

`results/query_plans/`

The original Parquet datasets are stored locally and excluded from Git tracking.

## 11. Notes for Member 3

The PostgreSQL component provides the following information for the SQL–MongoDB comparison:

- Dataset size: 48,722,602 records.
- PostgreSQL loading time: 2,532 seconds.
- PostgreSQL loading throughput: approximately 19,243 records/second.
- Five analytical SQL queries.
- Execution plans before and after indexing.
- Index sizes and index-retention decisions.

For a fair comparison, equivalent MongoDB queries should use consistent filters, aggregation definitions, and data handling rules.

SQL and MongoDB performance measurements should be collected using actual executions under comparable conditions.

## 12. Conclusion

The Member 1 PostgreSQL component of the NYC Taxi Analytics project has been completed.

A full year of NYC Yellow Taxi data containing 48,722,602 records was collected, inspected, validated, and imported into PostgreSQL.

A relational database was designed using one main trip table and four lookup tables.

Five analytical SQL queries were implemented and evaluated using PostgreSQL execution plans.

The indexing experiments showed that selective queries can benefit significantly from partial and covering indexes, while queries that process almost the entire dataset may perform better with sequential scans.

The results provide a foundation for the remaining MongoDB implementation and cross-database performance comparison.

**Member 1 status: Completed — pending final repository verification and commit.**