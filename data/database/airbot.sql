DELETE FROM pg_type WHERE typname = 'user_role';
DELETE FROM pg_type WHERE typname = 'order_state';

CREATE TYPE user_role AS ENUM ('sender', 'traveler');
CREATE TYPE order_state AS ENUM (
            'OrderStates:order_start_creating',
            'OrderStates:order_accepted',
            'OrderStates:order_in_work',
            'OrderStates:order_completed',
            'OrderStates:order_terminated'
        );

CREATE TABLE IF NOT EXISTS bot.user (
   user_id BIGINT PRIMARY KEY,
   username TEXT,
   first_name TEXT,
   last_name TEXT,
   agree_with_rules BOOLEAN,
   phone TEXT,
   email INTEGER,
   photo TEXT,
   traveler_bio TEXT,
   sender_bio TEXT,
   is_admin BOOLEAN,
   last_seen FLOAT
);

CREATE TABLE IF NOT EXISTS bot.customer (
   user_id BIGINT PRIMARY KEY REFERENCES bot.user(user_id),
   state TEXT,
   completed_orders_id TEXT,
   number_parcels_delivered INTEGER DEFAULT 0,
   last_seen FLOAT
);

CREATE TABLE IF NOT EXISTS bot.contractor (
   user_id BIGINT PRIMARY KEY REFERENCES bot.user(user_id),
   state TEXT,
   completed_deliveries_id TEXT,
   number_parcels_delivered INTEGER DEFAULT 0,
   last_seen FLOAT
);

CREATE TABLE IF NOT EXISTS bot.country (
   iso_code TEXT PRIMARY KEY,
   name_rus TEXT,
   name_eng TEXT,
   flag TEXT
);

CREATE TABLE IF NOT EXISTS bot.airport (
   iata_code TEXT PRIMARY KEY,
   icao_code TEXT,
   name_rus TEXT,
   name_eng TEXT,
   city_rus TEXT,
   city_eng TEXT,
   population INTEGER,
   gmt_offset INTEGER,
   country_rus TEXT,
   country_eng TEXT,
   iso_code TEXT REFERENCES bot.country(iso_code),
   latitude FLOAT,
   longitude FLOAT,
   website TEXT
);

CREATE TABLE IF NOT EXISTS bot.order (
   id BIGINT PRIMARY KEY,
   contractor_id  BIGINT REFERENCES bot.user(user_id) NULL,
   customer_id  BIGINT REFERENCES bot.user(user_id) NULL,
   "role" user_role,
   state order_state,
   departure_date TEXT,
   departure_date_posix FLOAT,
   departure_country TEXT,
   departure_city TEXT,
   departure_airport_abbr TEXT REFERENCES bot.airport(iata_code) NULL,
   arrival_country TEXT,
   arrival_city TEXT,
   arrival_airport_abbr TEXT REFERENCES bot.airport(iata_code) NULL,
   flight_route TEXT,
   "comment" TEXT,
   create_time FLOAT
);

CREATE TABLE IF NOT EXISTS bot.temp (
   user_id BIGINT PRIMARY KEY,
   last_message_id TEXT
);

CREATE OR REPLACE FUNCTION bot.upsert_table_temp(us_id BIGINT, l_msg TEXT) RETURNS VOID AS $$
BEGIN
    UPDATE bot.temp SET last_message_id = $2 WHERE user_id = $1;
    IF NOT FOUND THEN
        INSERT INTO bot.temp values ($1, $2);
    END IF;
END;
$$
LANGUAGE plpgsql;