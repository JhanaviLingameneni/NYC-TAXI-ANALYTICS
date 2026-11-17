\# Phase III: PostgreSQL vs MongoDB Performance



Dataset: NYC Yellow Taxi trips, 2025

Total trips: 48,722,602



\## Query execution times



| Query | PostgreSQL (After Indexing) | MongoDB |



| Q1 - Busiest Pickup Zones | 23.675 s | 125.324 s |

| Q2 - High-Value Trips | 0.013 s | 0.283 s |

| Q3 - Airport Trips | 2.764 s | 210.481 s |

| Q4 - Peak-Hour Demand | 24.610 s | 183.218 s |

| Q5 - Payment Methods and Tips | 27.332 s | 192.668 s |



\## Observations



\- PostgreSQL was faster in all five recorded query comparisons.

\- MongoDB Q2 improved significantly after creating a compound index on fare amount and pickup datetime.

\- MongoDB Q3 used an index on pickup location ID and pickup datetime.

\- Q1, Q4, and Q5 process large portions of the dataset, resulting in longer MongoDB aggregation times.

\- MongoDB's embedded document model eliminated the need for a separate payment-method join in Q5.

\- MongoDB used `$lookup` to join taxi zone information in Q1, Q2, and Q3.



\## Benchmark limitation



PostgreSQL timings were obtained from `EXPLAIN ANALYZE`, while MongoDB timings were measured in Python using `perf\_counter()` around aggregation execution and result materialization with `list()`.



Therefore, the measurements are not perfectly equivalent: MongoDB timings include client-side result retrieval and materialization, whereas PostgreSQL execution times do not include client-side result transfer. The results should be interpreted with this limitation in mind.

