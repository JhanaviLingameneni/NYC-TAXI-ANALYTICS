
-- Query 5: Payment methods and tipping patterns
-- NYC Yellow Taxi 2025

SELECT
    p.description AS payment_method,
    COUNT(*) AS total_trips,
    ROUND(AVG(t.fare_amount)::numeric, 2)
        AS avg_fare,
    ROUND(AVG(t.tip_amount)::numeric, 2)
        AS avg_tip,
    ROUND(
        AVG(
            CASE
                WHEN t.fare_amount > 0
                THEN 100.0 * t.tip_amount / t.fare_amount
            END
        )::numeric, 2
    ) AS avg_tip_percentage,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE t.tip_amount > 0
        ) / NULLIF(COUNT(*), 0), 2
    ) AS pct_trips_with_tip
FROM taxi_trips t
JOIN payment_types p
    ON t.payment_type_id = p.payment_type_id
WHERE
    t.pickup_datetime >= '2025-01-01'
    AND t.pickup_datetime < '2026-01-01'
GROUP BY
    p.description
ORDER BY
    total_trips DESC;
