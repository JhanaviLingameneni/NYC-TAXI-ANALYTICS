
-- Index Experiment 4
-- Covering expression index for hourly pickup analytics.

CREATE INDEX idx_taxi_peak_hours
ON taxi_trips (
    (EXTRACT(HOUR FROM pickup_datetime))
)
INCLUDE (
    pickup_datetime,
    trip_distance,
    total_amount
);
