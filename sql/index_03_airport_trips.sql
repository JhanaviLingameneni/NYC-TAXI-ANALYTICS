
-- Index Experiment 3
-- Optimize airport pickup analytics.

CREATE INDEX idx_taxi_airport_pickups
ON taxi_trips (
    pickup_location_id,
    pickup_datetime
)
INCLUDE (
    trip_distance,
    total_amount
)
WHERE pickup_location_id IN (1, 132, 138);
