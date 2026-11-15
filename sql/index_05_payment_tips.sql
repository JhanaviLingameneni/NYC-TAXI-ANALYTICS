
-- Index Experiment 5
-- Covering index for payment and tipping analysis

CREATE INDEX idx_taxi_payment_tips
ON taxi_trips (payment_type_id)
INCLUDE (
    pickup_datetime,
    fare_amount,
    tip_amount
);
