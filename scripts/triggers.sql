-- =============================================================================
-- GreenQuality: Триггеры БД
-- 1-2. Триггеры аудита (INSERT, UPDATE/DELETE)
-- 3. Триггер генерации билетов при создании рейса
-- =============================================================================

-- Удаление существующих триггеров и функций
DROP TRIGGER IF EXISTS audit_flights_insert ON flights;
DROP TRIGGER IF EXISTS audit_flights_update_delete ON flights;
DROP TRIGGER IF EXISTS audit_tickets_insert ON tickets;
DROP TRIGGER IF EXISTS audit_tickets_update_delete ON tickets;
DROP TRIGGER IF EXISTS audit_users_insert ON users;
DROP TRIGGER IF EXISTS audit_users_update_delete ON users;
DROP TRIGGER IF EXISTS tr_generate_tickets_after_flight_insert ON flights;

DROP FUNCTION IF EXISTS audit_trigger_insert();
DROP FUNCTION IF EXISTS audit_trigger_update_delete();
DROP FUNCTION IF EXISTS generate_tickets_for_flight();

-- =============================================================================
-- 1. Триггер аудита для INSERT
-- =============================================================================
CREATE OR REPLACE FUNCTION audit_trigger_insert()
RETURNS TRIGGER AS $$
DECLARE
    rec_id INT;
    tbl_name TEXT;
BEGIN
    tbl_name := TG_TABLE_NAME;
    rec_id := CASE tbl_name
        WHEN 'flights' THEN (NEW).id_flight
        WHEN 'tickets' THEN (NEW).id_ticket
        WHEN 'users' THEN (NEW).id_user
        ELSE 0
    END;

    INSERT INTO audit_log (table_name, record_id, operation, old_data, new_data, changed_by)
    VALUES (tbl_name, rec_id, 'INSERT', NULL, to_jsonb(NEW), NULL);

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RETURN NEW;  -- не прерываем основную операцию
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 2. Триггер аудита для UPDATE и DELETE
-- =============================================================================
CREATE OR REPLACE FUNCTION audit_trigger_update_delete()
RETURNS TRIGGER AS $$
DECLARE
    rec_id INT;
    tbl_name TEXT;
    op TEXT;
BEGIN
    tbl_name := TG_TABLE_NAME;
    op := TG_OP;

    rec_id := CASE tbl_name
        WHEN 'flights' THEN COALESCE((NEW).id_flight, (OLD).id_flight)
        WHEN 'tickets' THEN COALESCE((NEW).id_ticket, (OLD).id_ticket)
        WHEN 'users' THEN COALESCE((NEW).id_user, (OLD).id_user)
        ELSE 0
    END;

    INSERT INTO audit_log (table_name, record_id, operation, old_data, new_data, changed_by)
    VALUES (
        tbl_name,
        rec_id,
        op,
        to_jsonb(OLD),
        CASE WHEN op = 'DELETE' THEN NULL ELSE to_jsonb(NEW) END,
        NULL
    );

    RETURN COALESCE(NEW, OLD);
EXCEPTION WHEN OTHERS THEN
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Привязка триггеров аудита к таблицам
CREATE TRIGGER audit_flights_insert
    AFTER INSERT ON flights
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_insert();

CREATE TRIGGER audit_flights_update_delete
    AFTER UPDATE OR DELETE ON flights
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_update_delete();

CREATE TRIGGER audit_tickets_insert
    AFTER INSERT ON tickets
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_insert();

CREATE TRIGGER audit_tickets_update_delete
    AFTER UPDATE OR DELETE ON tickets
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_update_delete();

CREATE TRIGGER audit_users_insert
    AFTER INSERT ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_insert();

CREATE TRIGGER audit_users_update_delete
    AFTER UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_update_delete();

-- =============================================================================
-- 3. Триггер генерации билетов при создании рейса
-- =============================================================================
CREATE OR REPLACE FUNCTION generate_tickets_for_flight()
RETURNS TRIGGER AS $$
DECLARE
    a_rows INT;
    a_seats_row INT;
    r INT;
    s INT;
    seat_letters TEXT[] := ARRAY['A','B','C','D','E','F','G','H'];
    seat_num TEXT;
    economy_class_id INT;
BEGIN
    SELECT COALESCE(rows, 30), COALESCE(seats_row, 6)
    INTO a_rows, a_seats_row
    FROM airplanes WHERE id_airplane = NEW.airplane_id;

    SELECT id_class INTO economy_class_id FROM class WHERE class_name = 'ECONOMY' LIMIT 1;

    IF economy_class_id IS NULL THEN
        RAISE EXCEPTION 'Класс ECONOMY не найден в таблице class';
    END IF;

    FOR r IN 1..a_rows LOOP
        FOR s IN 1..a_seats_row LOOP
            seat_num := r::TEXT || seat_letters[s];
            INSERT INTO tickets (flight_id, class_id, seat_number, price, status, passenger_id, payment_id)
            VALUES (NEW.id_flight, economy_class_id, seat_num, 0, 'AVAILABLE', NULL, NULL);
        END LOOP;
    END LOOP;

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_generate_tickets_after_flight_insert
    AFTER INSERT ON flights
    FOR EACH ROW EXECUTE FUNCTION generate_tickets_for_flight();