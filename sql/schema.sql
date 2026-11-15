--
-- PostgreSQL database dump
--

\restrict SsdDhqkS2AeulrXkFhdzUfTGmKtxvMHiJbaM37FcNnYGe05LJ0XJUHVfeFii2Qh

-- Dumped from database version 15.17 (Homebrew)
-- Dumped by pg_dump version 15.17 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: import_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.import_history (
    filename character varying(255) NOT NULL,
    expected_rows bigint NOT NULL,
    imported_rows bigint NOT NULL,
    duration_seconds double precision,
    imported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(20) NOT NULL
);


--
-- Name: payment_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_types (
    payment_type_id integer NOT NULL,
    description character varying(100) NOT NULL
);


--
-- Name: rate_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rate_codes (
    rate_code_id integer NOT NULL,
    description character varying(100) NOT NULL
);


--
-- Name: taxi_trips; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.taxi_trips (
    trip_id bigint NOT NULL,
    vendor_id integer,
    pickup_datetime timestamp without time zone,
    dropoff_datetime timestamp without time zone,
    passenger_count bigint,
    trip_distance double precision,
    rate_code_id integer,
    store_and_fwd_flag character varying(5),
    pickup_location_id integer,
    dropoff_location_id integer,
    payment_type_id integer,
    fare_amount double precision,
    extra double precision,
    mta_tax double precision,
    tip_amount double precision,
    tolls_amount double precision,
    improvement_surcharge double precision,
    total_amount double precision,
    congestion_surcharge double precision,
    airport_fee double precision,
    cbd_congestion_fee double precision
);


--
-- Name: taxi_trips_trip_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.taxi_trips ALTER COLUMN trip_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.taxi_trips_trip_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: taxi_zones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.taxi_zones (
    location_id integer NOT NULL,
    borough character varying(100),
    zone character varying(150),
    service_zone character varying(100)
);


--
-- Name: vendors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vendors (
    vendor_id integer NOT NULL,
    vendor_name character varying(100) NOT NULL
);


--
-- Name: import_history import_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_history
    ADD CONSTRAINT import_history_pkey PRIMARY KEY (filename);


--
-- Name: payment_types payment_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_types
    ADD CONSTRAINT payment_types_pkey PRIMARY KEY (payment_type_id);


--
-- Name: rate_codes rate_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rate_codes
    ADD CONSTRAINT rate_codes_pkey PRIMARY KEY (rate_code_id);


--
-- Name: taxi_trips taxi_trips_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.taxi_trips
    ADD CONSTRAINT taxi_trips_pkey PRIMARY KEY (trip_id);


--
-- Name: taxi_zones taxi_zones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.taxi_zones
    ADD CONSTRAINT taxi_zones_pkey PRIMARY KEY (location_id);


--
-- Name: vendors vendors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vendors
    ADD CONSTRAINT vendors_pkey PRIMARY KEY (vendor_id);


--
-- Name: idx_taxi_airport_pickups; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_taxi_airport_pickups ON public.taxi_trips USING btree (pickup_location_id, pickup_datetime) INCLUDE (trip_distance, total_amount) WHERE (pickup_location_id = ANY (ARRAY[1, 132, 138]));


--
-- Name: idx_taxi_high_value_trips; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_taxi_high_value_trips ON public.taxi_trips USING btree (total_amount DESC) INCLUDE (pickup_datetime, pickup_location_id, trip_distance) WHERE (total_amount > (100)::double precision);


--
-- Name: taxi_trips taxi_trips_dropoff_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.taxi_trips
    ADD CONSTRAINT taxi_trips_dropoff_location_id_fkey FOREIGN KEY (dropoff_location_id) REFERENCES public.taxi_zones(location_id);


--
-- Name: taxi_trips taxi_trips_payment_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.taxi_trips
    ADD CONSTRAINT taxi_trips_payment_type_id_fkey FOREIGN KEY (payment_type_id) REFERENCES public.payment_types(payment_type_id);


--
-- Name: taxi_trips taxi_trips_pickup_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.taxi_trips
    ADD CONSTRAINT taxi_trips_pickup_location_id_fkey FOREIGN KEY (pickup_location_id) REFERENCES public.taxi_zones(location_id);


--
-- Name: taxi_trips taxi_trips_rate_code_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.taxi_trips
    ADD CONSTRAINT taxi_trips_rate_code_id_fkey FOREIGN KEY (rate_code_id) REFERENCES public.rate_codes(rate_code_id);


--
-- Name: taxi_trips taxi_trips_vendor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.taxi_trips
    ADD CONSTRAINT taxi_trips_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendors(vendor_id);


--
-- PostgreSQL database dump complete
--

\unrestrict SsdDhqkS2AeulrXkFhdzUfTGmKtxvMHiJbaM37FcNnYGe05LJ0XJUHVfeFii2Qh

