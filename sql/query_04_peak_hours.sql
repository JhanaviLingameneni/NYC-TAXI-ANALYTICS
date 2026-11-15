
-- Query 4: Peak-hour taxi demand
-- Analyze pickup activity by hour during 2025.

SELECT
    EXTRACT(HOUR FROM pickup_datetime)::integer
        AS pickup_hour,
    COUNT(*) AS total_trips,
    ROUND(AVG(trip_distance)::numeric, 2)
        AS avg_trip_distance,
    ROUND(AVG(total_amount)::numeric, 2)
        AS avg_total_amount
FROM taxi_trips
WHERE
    pickup_datetime >= '2025-01-01'
    AND pickup_datetime < '2026-01-01'
GROUP BY
    EXTRACT(HOUR FROM pickup_datetime)
ORDER BY
    total_trips DESC;
