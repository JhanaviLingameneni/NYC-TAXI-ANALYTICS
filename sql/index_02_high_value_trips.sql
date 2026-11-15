
-- Index Experiment 2
-- Optimize queries for trips above $100.

CREATE INDEX idx_taxi_high_value_trips
ON taxi_trips (total_amount DESC)
INCLUDE (
    pickup_datetime,
    pickup_location_id,
    trip_distance
)
WHERE total_amount > 100;
