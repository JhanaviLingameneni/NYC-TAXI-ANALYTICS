
# Functional Dependencies and Normalization

## 1. Relational Database Design

The NYC Taxi Analytics database contains one main fact table,
taxi_trips, and four lookup tables: vendors, payment_types,
rate_codes, and taxi_zones.

The taxi_trips table stores individual trip records, while the
lookup tables store information associated with vendor IDs,
payment types, rate codes, and taxi zone IDs.

## 2. Functional Dependencies

The main functional dependencies are:

1. trip_id -> pickup_datetime, dropoff_datetime,
   passenger_count, trip_distance, fare_amount,
   tip_amount, total_amount, and other trip attributes.

2. vendor_id -> vendor_name

3. payment_type_id -> description

4. rate_code_id -> description

5. location_id -> borough, zone, service_zone

Each primary key uniquely identifies the corresponding
record and determines its non-key attributes.

## 3. First Normal Form (1NF)

The tables satisfy 1NF because each column stores a single
value, and each row can be uniquely identified using its
primary key.

There are no repeating groups or multi-valued columns.

## 4. Second Normal Form (2NF)

The tables satisfy 2NF because they are already in 1NF
and their primary keys consist of a single column.

Therefore, there are no partial dependencies on a
composite primary key.

## 5. Third Normal Form (3NF)

The design separates descriptive lookup information from
individual trip records.

For example, payment descriptions are stored in
payment_types instead of being repeated in every trip.

Similarly, borough and zone information are stored in
taxi_zones rather than duplicated across millions of trips.

The taxi_trips table references these records using
foreign keys.

This avoids transitive dependencies involving lookup
descriptions and reduces unnecessary data duplication.

## 6. Benefits of Normalization

- Reduces repeated descriptive information.
- Improves consistency across records.
- Prevents common update anomalies.
- Makes lookup information easier to maintain.
- Supports joins between trip records and descriptive data.

## 7. Conclusion

The relational schema is designed to satisfy 3NF based on
the identified functional dependencies.

It separates trip-level facts from descriptive lookup
information while preserving relationships through
primary and foreign keys.
