
-- Query 3: Airport pickup analysis
-- Dataset: NYC Yellow Taxi, 2025
-- Baseline: Before adding a dedicated airport index

SELECT
    z.zone AS airport,
    COUNT(*) AS total_trips,
    ROUND(AVG(t.trip_distance)::numeric, 2)
        AS avg_trip_distance,
    ROUND(AVG(t.total_amount)::numeric, 2)
        AS avg_total_amount,
    ROUND(SUM(t.total_amount)::numeric, 2)
        AS total_revenue
FROM taxi_trips t
JOIN taxi_zones z
    ON t.pickup_location_id = z.location_id
WHERE
    t.pickup_location_id IN (1, 132, 138)
    AND t.pickup_datetime >= '2025-01-01'
    AND t.pickup_datetime < '2026-01-01'
GROUP BY
    z.zone
ORDER BY
    total_trips DESC;
