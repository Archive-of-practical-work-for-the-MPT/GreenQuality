-- =============================================================================
-- GreenQuality: Процедуры (расчёты) и представления (отчётность)
-- СУБД: PostgreSQL
-- =============================================================================

-- =============================================================================
-- Удаление существующих представлений и процедур/функций
-- =============================================================================
DROP VIEW IF EXISTS v_flights_report CASCADE;
DROP VIEW IF EXISTS v_airports_revenue_report CASCADE;
DROP VIEW IF EXISTS v_audit_operations_report CASCADE;

DROP FUNCTION IF EXISTS calc_flight_revenue(INTEGER);
DROP FUNCTION IF EXISTS calc_flight_occupancy(INTEGER);
DROP FUNCTION IF EXISTS calc_user_payments_in_period(INTEGER, TIMESTAMP WITH TIME ZONE, TIMESTAMP WITH TIME ZONE);

-- =============================================================================
-- ПРОЦЕДУРЫ (расчёты)
-- =============================================================================

-- 1. Расчёт общей выручки по рейсу (сумма оплаченных/забронированных билетов)
CREATE OR REPLACE FUNCTION calc_flight_revenue(p_flight_id INTEGER)
RETURNS NUMERIC(12, 2) AS $$
DECLARE
    total NUMERIC(12, 2);
BEGIN
    SELECT COALESCE(SUM(t.price), 0)
    INTO total
    FROM tickets t
    WHERE t.flight_id = p_flight_id
      AND t.status IN ('PAID', 'BOOKED', 'CHECKED_IN');

    RETURN total;
END;
$$ LANGUAGE plpgsql;

-- 2. Расчёт загрузки рейса (процент занятых мест от общего числа мест)
CREATE OR REPLACE FUNCTION calc_flight_occupancy(p_flight_id INTEGER)
RETURNS NUMERIC(5, 2) AS $$
DECLARE
    total_seats INT;
    occupied_seats INT;
    result_pct NUMERIC(5, 2);
BEGIN
    SELECT COUNT(*)
    INTO total_seats
    FROM tickets t
    WHERE t.flight_id = p_flight_id;

    SELECT COUNT(*)
    INTO occupied_seats
    FROM tickets t
    WHERE t.flight_id = p_flight_id
      AND t.status IN ('PAID', 'BOOKED', 'CHECKED_IN');

    IF total_seats = 0 THEN
        RETURN 0;
    END IF;

    result_pct := (occupied_seats::NUMERIC / total_seats::NUMERIC) * 100;
    RETURN ROUND(result_pct, 2);
END;
$$ LANGUAGE plpgsql;

-- 3. Расчёт суммы платежей пользователя за период
CREATE OR REPLACE FUNCTION calc_user_payments_in_period(
    p_user_id INTEGER,
    p_date_from TIMESTAMP WITH TIME ZONE,
    p_date_to TIMESTAMP WITH TIME ZONE
)
RETURNS NUMERIC(12, 2) AS $$
DECLARE
    total NUMERIC(12, 2);
BEGIN
    SELECT COALESCE(SUM(p.total_cost), 0)
    INTO total
    FROM payments p
    WHERE p.user_id = p_user_id
      AND p.status = 'COMPLETED'
      AND p.payment_date >= p_date_from
      AND p.payment_date <= p_date_to;

    RETURN total;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ПРЕДСТАВЛЕНИЯ (отчётность)
-- =============================================================================

-- 1. Отчёт по рейсам: рейс, аэропорты, время, статус, кол-во мест, занято, выручка
CREATE OR REPLACE VIEW v_flights_report AS
SELECT
    f.id_flight,
    f.departure_time,
    f.arrival_time,
    f.status AS flight_status,
    dep.id_airport AS departure_airport_code,
    dep.name AS departure_airport_name,
    dep.city AS departure_city,
    arr.id_airport AS arrival_airport_code,
    arr.name AS arrival_airport_name,
    arr.city AS arrival_city,
    (SELECT COUNT(*) FROM tickets t WHERE t.flight_id = f.id_flight) AS total_seats,
    (SELECT COUNT(*) FROM tickets t WHERE t.flight_id = f.id_flight AND t.status IN ('PAID', 'BOOKED', 'CHECKED_IN')) AS occupied_seats,
    calc_flight_revenue(f.id_flight) AS revenue
FROM flights f
JOIN airports dep ON f.departure_airport_id = dep.id_airport
JOIN airports arr ON f.arrival_airport_id = arr.id_airport
ORDER BY f.departure_time DESC;

-- 2. Отчёт по выручке по аэропортам (вылеты и прилёты)
CREATE OR REPLACE VIEW v_airports_revenue_report AS
SELECT
    a.id_airport,
    a.name AS airport_name,
    a.city,
    a.country,
    COALESCE(SUM(CASE WHEN f.departure_airport_id = a.id_airport THEN calc_flight_revenue(f.id_flight) ELSE 0 END), 0) AS revenue_departures,
    COALESCE(SUM(CASE WHEN f.arrival_airport_id = a.id_airport THEN calc_flight_revenue(f.id_flight) ELSE 0 END), 0) AS revenue_arrivals,
    COALESCE(SUM(calc_flight_revenue(f.id_flight)), 0) AS revenue_total
FROM airports a
LEFT JOIN flights f ON (f.departure_airport_id = a.id_airport OR f.arrival_airport_id = a.id_airport)
GROUP BY a.id_airport, a.name, a.city, a.country;

-- 3. Отчёт по операциям аудита (таблица, тип операции, количество за последние записи)
CREATE OR REPLACE VIEW v_audit_operations_report AS
SELECT
    table_name,
    operation,
    COUNT(*) AS operations_count,
    MIN(changed_at) AS first_at,
    MAX(changed_at) AS last_at
FROM audit_log
GROUP BY table_name, operation
ORDER BY table_name, operation;
