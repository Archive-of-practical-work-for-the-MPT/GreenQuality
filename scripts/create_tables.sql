-- =============================================================================
-- GreenQuality: Создание таблиц БД (соответствует моделям Django airline)
-- СУБД: PostgreSQL
-- =============================================================================

-- Удаление таблиц в обратном порядке зависимостей (для повторного запуска)
DROP TABLE IF EXISTS baggage CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS flights CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS passengers CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS baggage_types CASCADE;
DROP TABLE IF EXISTS class CASCADE;
DROP TABLE IF EXISTS airplanes CASCADE;
DROP TABLE IF EXISTS airports CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- =============================================================================
-- Таблицы без внешних ключей
-- =============================================================================

CREATE TABLE roles (
    id_role SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE airports (
    id_airport VARCHAR(3) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL
);

CREATE TABLE airplanes (
    id_airplane SERIAL PRIMARY KEY,
    model VARCHAR(50) NOT NULL,
    registration_number VARCHAR(20) NOT NULL UNIQUE,
    capacity INTEGER NOT NULL,
    economy_capacity INTEGER,
    business_capacity INTEGER,
    first_capacity INTEGER,
    rows INTEGER,
    seats_row INTEGER
);

CREATE TABLE passengers (
    id_passenger SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    patronymic VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    passport_number VARCHAR(20) NOT NULL UNIQUE,
    birthday DATE NOT NULL
);

CREATE TABLE class (
    id_class SERIAL PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE baggage_types (
    id_baggage_type SERIAL PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE,
    max_weight_kg NUMERIC(5, 2) NOT NULL,
    description TEXT,
    base_price NUMERIC(6, 2) NOT NULL
);

-- =============================================================================
-- Таблицы с внешними ключами
-- =============================================================================

CREATE TABLE accounts (
    id_account SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id_role) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id_user SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL UNIQUE REFERENCES accounts(id_account) ON DELETE CASCADE,
    first_name VARCHAR(50) NOT NULL,
    patronymic VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    passport_number VARCHAR(20) UNIQUE,
    birthday DATE
);

CREATE TABLE audit_log (
    id_audit SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    operation VARCHAR(10) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    changed_by INTEGER REFERENCES accounts(id_account) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE flights (
    id_flight SERIAL PRIMARY KEY,
    airplane_id INTEGER NOT NULL REFERENCES airplanes(id_airplane) ON DELETE CASCADE,
    departure_airport_id VARCHAR(3) NOT NULL REFERENCES airports(id_airport) ON DELETE CASCADE,
    arrival_airport_id VARCHAR(3) NOT NULL REFERENCES airports(id_airport) ON DELETE CASCADE,
    departure_time TIMESTAMP WITH TIME ZONE NOT NULL,
    arrival_time TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_departure_time TIMESTAMP WITH TIME ZONE,
    actual_arrival_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED',
    CONSTRAINT check_departure_before_arrival CHECK (departure_time < arrival_time)
);

CREATE TABLE payments (
    id_payment SERIAL PRIMARY KEY,
    payment_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_cost NUMERIC(9, 2) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id_user) ON DELETE CASCADE,
    payment_method VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
);

CREATE TABLE tickets (
    id_ticket SERIAL PRIMARY KEY,
    flight_id INTEGER NOT NULL REFERENCES flights(id_flight) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES class(id_class) ON DELETE CASCADE,
    seat_number VARCHAR(5) NOT NULL,
    price NUMERIC(8, 2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE',
    passenger_id INTEGER REFERENCES passengers(id_passenger) ON DELETE CASCADE,
    payment_id INTEGER REFERENCES payments(id_payment) ON DELETE SET NULL,
    CONSTRAINT unique_flight_seat UNIQUE (flight_id, seat_number)
);

CREATE TABLE baggage (
    id_baggage SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id_ticket) ON DELETE CASCADE,
    baggage_type_id INTEGER NOT NULL REFERENCES baggage_types(id_baggage_type) ON DELETE CASCADE,
    weight_kg NUMERIC(5, 2) NOT NULL,
    baggage_tag VARCHAR(12) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'REGISTERED',
    registered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Индексы для ускорения частых запросов (опционально)
-- =============================================================================

CREATE INDEX idx_accounts_role ON accounts(role_id);
CREATE INDEX idx_audit_log_changed_by ON audit_log(changed_by);
CREATE INDEX idx_flights_airplane ON flights(airplane_id);
CREATE INDEX idx_flights_departure_airport ON flights(departure_airport_id);
CREATE INDEX idx_flights_arrival_airport ON flights(arrival_airport_id);
CREATE INDEX idx_flights_departure_time ON flights(departure_time);
CREATE INDEX idx_tickets_flight ON tickets(flight_id);
CREATE INDEX idx_tickets_passenger ON tickets(passenger_id);
CREATE INDEX idx_baggage_ticket ON baggage(ticket_id);
