-- =============================================================================
-- GreenQuality: Начальные данные для БД
-- Запускать ПОСЛЕ create_tables.sql
-- =============================================================================

-- Очистка существующих данных (для повторного заполнения)
TRUNCATE TABLE baggage, tickets, payments, audit_log, flights, users, passengers,
    accounts, baggage_types, class, airplanes, airports, roles
RESTART IDENTITY CASCADE;

-- =============================================================================
-- Роли
-- =============================================================================
INSERT INTO roles (role_name) VALUES
    ('USER'),
    ('ADMIN'),
    ('MANAGER');

-- =============================================================================
-- Классы обслуживания
-- =============================================================================
INSERT INTO class (class_name) VALUES
    ('ECONOMY'),
    ('BUSINESS'),
    ('FIRST');

-- =============================================================================
-- Аэропорты
-- =============================================================================
INSERT INTO airports (id_airport, name, city, country) VALUES
    ('SVO', 'Шереметьево', 'Москва', 'Россия'),
    ('LED', 'Пулково', 'Санкт-Петербург', 'Россия'),
    ('AER', 'Сочи', 'Сочи', 'Россия'),
    ('MSQ', 'Минск', 'Минск', 'Беларусь'),
    ('CDG', 'Шарль де Голль', 'Париж', 'Франция'),
    ('JFK', 'Джон Кеннеди', 'Нью-Йорк', 'США'),
    ('NRT', 'Нarita', 'Токио', 'Япония');

-- =============================================================================
-- Типы багажа
-- =============================================================================
INSERT INTO baggage_types (type_name, max_weight_kg, description, base_price) VALUES
    ('STANDARD', 23.00, 'Стандартный багаж до 23 кг', 2000.00),
    ('EXTRA', 32.00, 'Дополнительный багаж до 32 кг', 3500.00),
    ('SPORT', 30.00, 'Спортивный инвентарь до 30 кг', 5000.00),
    ('OVERSIZE', 50.00, 'Крупногабаритный багаж до 50 кг', 8000.00);

-- =============================================================================
-- Аккаунт администратора (пароль: adminadmin)
-- =============================================================================
INSERT INTO accounts (email, password, role_id) VALUES
    ('admin@gmail.com', 'pbkdf2_sha256$1000000$93PNmEBtQdjXzKOGg824Dx$ZJxzzcw643ID29iUV/6iqrx37q9xOsRZH0WbpGsl1Vk=', (SELECT id_role FROM roles WHERE role_name = 'ADMIN' LIMIT 1));

-- =============================================================================
-- Пользователь администратора
-- =============================================================================
INSERT INTO users (account_id, first_name, patronymic, last_name, phone, passport_number, birthday) VALUES
    ((SELECT id_account FROM accounts WHERE email = 'admin@gmail.com' LIMIT 1), 'Администратор', NULL, 'Системы', NULL, NULL, NULL);

-- =============================================================================
-- Самолёты
-- =============================================================================
INSERT INTO airplanes (model, registration_number, capacity, economy_capacity, business_capacity, first_capacity, rows, seats_row) VALUES
    ('Airbus A320', 'GQ-A320-001', 180, 150, 30, 0, 30, 6),
    ('Boeing 737', 'GQ-B737-001', 189, 162, 27, 0, 31, 6),
    ('Airbus A350', 'GQ-A350-001', 325, 280, 40, 5, 50, 7),
    ('Boeing 777', 'GQ-B777-001', 396, 350, 40, 6, 60, 7);

-- =============================================================================
-- Рейсы (время относительно момента выполнения скрипта)
-- =============================================================================
INSERT INTO flights (airplane_id, departure_airport_id, arrival_airport_id, departure_time, arrival_time, status) VALUES
    -- Москва - Санкт-Петербург
    (1, 'SVO', 'LED', NOW() + INTERVAL '1 day 8 hours 45 minutes', NOW() + INTERVAL '1 day 10 hours 15 minutes', 'SCHEDULED'),
    (1, 'SVO', 'LED', NOW() + INTERVAL '2 days 14 hours 30 minutes', NOW() + INTERVAL '2 days 16 hours', 'SCHEDULED'),
    -- Москва - Сочи
    (2, 'SVO', 'AER', NOW() + INTERVAL '1 day 12 hours 30 minutes', NOW() + INTERVAL '1 day 14 hours 45 minutes', 'SCHEDULED'),
    -- Москва - Минск (задержан)
    (1, 'SVO', 'MSQ', NOW() + INTERVAL '1 day 16 hours 20 minutes', NOW() + INTERVAL '1 day 17 hours 55 minutes', 'DELAYED'),
    -- Москва - Париж
    (3, 'SVO', 'CDG', NOW() + INTERVAL '1 day 21 hours 10 minutes', NOW() + INTERVAL '2 days 45 minutes', 'SCHEDULED'),
    -- Санкт-Петербург - Москва
    (1, 'LED', 'SVO', NOW() + INTERVAL '1 day 9 hours 30 minutes', NOW() + INTERVAL '1 day 11 hours', 'SCHEDULED'),
    -- Сочи - Москва
    (2, 'AER', 'SVO', NOW() + INTERVAL '1 day 13 hours 15 minutes', NOW() + INTERVAL '1 day 15 hours 30 minutes', 'SCHEDULED'),
    -- Минск - Москва
    (1, 'MSQ', 'SVO', NOW() + INTERVAL '1 day 18 hours 40 minutes', NOW() + INTERVAL '1 day 20 hours 15 minutes', 'SCHEDULED'),
    -- Париж - Москва (отменён)
    (3, 'CDG', 'SVO', NOW() + INTERVAL '1 day 7 hours 25 minutes', NOW() + INTERVAL '1 day 11 hours', 'CANCELLED'),
    -- Москва - Нью-Йорк
    (4, 'SVO', 'JFK', NOW() + INTERVAL '1 day 23 hours 30 minutes', NOW() + INTERVAL '2 days 6 hours 45 minutes', 'SCHEDULED'),
    -- Нью-Йорк - Москва
    (4, 'JFK', 'SVO', NOW() + INTERVAL '2 days 14 hours 20 minutes', NOW() + INTERVAL '3 days 20 minutes', 'SCHEDULED'),
    -- Дополнительные рейсы
    (1, 'SVO', 'LED', NOW() + INTERVAL '3 days 6 hours', NOW() + INTERVAL '3 days 7 hours 30 minutes', 'SCHEDULED'),
    (2, 'SVO', 'AER', NOW() + INTERVAL '3 days 10 hours 15 minutes', NOW() + INTERVAL '3 days 12 hours 30 minutes', 'SCHEDULED');

-- Обновление actual_departure_time для задержанного рейса Москва-Минск
UPDATE flights
SET actual_departure_time = departure_time + INTERVAL '30 minutes'
WHERE status = 'DELAYED' AND departure_airport_id = 'SVO' AND arrival_airport_id = 'MSQ';
