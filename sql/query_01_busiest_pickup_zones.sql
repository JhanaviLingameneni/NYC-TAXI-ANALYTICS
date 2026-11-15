
-- Query 1: Top 10 busiest taxi pickup zones
-- Dataset: NYC Yellow Taxi, 2025
-- Purpose: Identify areas with the highest taxi demand.
-- Baseline: Before adding performance indexes.

SELECT
    z.borough,
    z.zone,
    COUNT(*) AS total_trips,
    ROUND(AVG(t.trip_distance)::numeric, 2)
        AS avg_trip_distance,
    ROUND(AVG(t.total_amount)::numeric, 2)
        AS avg_trip_amount
FROM taxi_trips t
JOIN taxi_zones z
    ON t.pickup_location_id = z.location_id
WHERE
    t.pickup_datetime >= '2025-01-01'
    AND t.pickup_datetime < '2026-01-01'
GROUP BY
    z.borough,
    z.zone
ORDER BY
    total_trips DESC
LIMIT 10;
