
-- Index Experiment 1
-- Supports pickup-date filtering and zone analytics.

CREATE INDEX idx_taxi_pickup_analytics
ON taxi_trips (
    pickup_datetime,
    pickup_location_id
)
INCLUDE (
    trip_distance,
    total_amount
);
