
-- Query 2: High-value taxi trips
-- Objective: Find expensive trips and their pickup zones
-- Baseline: Before indexing

SELECT
    t.trip_id,
    t.pickup_datetime,
    z.borough,
    z.zone AS pickup_zone,
    ROUND(t.trip_distance::numeric, 2) AS trip_distance,
    ROUND(t.total_amount::numeric, 2) AS total_amount
FROM taxi_trips t
JOIN taxi_zones z
    ON t.pickup_location_id = z.location_id
WHERE
    t.total_amount > 100
    AND t.pickup_datetime >= '2025-01-01'
    AND t.pickup_datetime < '2026-01-01'
ORDER BY
    t.total_amount DESC
LIMIT 100;
