-- Таблица: roles
CREATE TABLE roles (
    id_role SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

-- Таблица: accounts
CREATE TABLE accounts (
    id_account SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role_id INT NOT NULL REFERENCES roles(id_role),
    created_at TIMESTAMP
);

-- Таблица: audit_log
CREATE TABLE audit_log (
    id_audit SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INT NOT NULL,
    operation VARCHAR(10) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    changed_by INT REFERENCES accounts(id_account),
    changed_at TIMESTAMP
);

-- Таблица: airports
CREATE TABLE airports (
    id_airport CHAR(3) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL
);

-- Таблица: airplanes
CREATE TABLE airplanes (
    id_airplane SERIAL PRIMARY KEY,
    model VARCHAR(50) NOT NULL,
    registration_number VARCHAR(20) UNIQUE NOT NULL,
    capacity INT NOT NULL,
    economy_capacity INT,
    business_capacity INT,
    first_capacity INT,
    rows INT,
    seats_row INT
);

-- Таблица: employees
CREATE TABLE employees (
    id_employee SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    patronymic VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    position VARCHAR(50) NOT NULL,
    account_id INT REFERENCES accounts(id_account)
);

-- Таблица: crew
CREATE TABLE crew (
    id_crew SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    patronymic VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    position VARCHAR(50) NOT NULL,
    account_id INT REFERENCES accounts(id_account)
);

-- Таблица: flights
CREATE TABLE flights (
    id_flight SERIAL PRIMARY KEY,
    airplane_id INT NOT NULL REFERENCES airplanes(id_airplane),
    status VARCHAR(30),
    departure_airport_id CHAR(3) NOT NULL REFERENCES airports(id_airport),
    arrival_airport_id CHAR(3) NOT NULL REFERENCES airports(id_airport),
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    actual_departure_time TIMESTAMP,
    actual_arrival_time TIMESTAMP
);

-- Таблица: flight_crew (связь многие-ко-многим)
CREATE TABLE flight_crew (
    flight_id INT NOT NULL REFERENCES flights(id_flight),
    crew_id INT NOT NULL REFERENCES crew(id_crew),
    PRIMARY KEY (flight_id, crew_id)
);

-- Таблица: passengers
CREATE TABLE passengers (
    id_passenger SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    patronymic VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    passport_number VARCHAR(20) NOT NULL,
    bithday DATE NOT NULL
);

-- Таблица: class
CREATE TABLE class (
    id_class SERIAL PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL
);

-- Таблица: users
CREATE TABLE users (
    id_user SERIAL PRIMARY KEY,
    account_id INT REFERENCES accounts(id_account),
    first_name VARCHAR(50) NOT NULL,
    patronymic VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(14) NOT NULL,
    passport_number VARCHAR(20) NOT NULL,
    birthday DATE NOT NULL
);

-- Таблица: payments
CREATE TABLE payments (
    id_payment SERIAL PRIMARY KEY,
    payment_date TIMESTAMP,
    total_cost DECIMAL(9,2),
    user_id INT REFERENCES users(id_user),
    payment_method VARCHAR(30),
    status VARCHAR(20)
);

-- Таблица: tickets
CREATE TABLE tickets (
    id_ticket SERIAL PRIMARY KEY,
    flight_id INT NOT NULL REFERENCES flights(id_flight),
    class_id INT NOT NULL REFERENCES class(id_class),
    seat INT NOT NULL,
    price DECIMAL(8,2) NOT NULL,
    status VARCHAR(20),
    passenger_id INT REFERENCES passengers(id_passenger),
    payment_id INT REFERENCES payments(id_payment)
);


-- ==== ROLES ====
INSERT INTO roles (role_name) VALUES
('Администратор'),
('Менеджер'),
('Пользователь');

-- ==== ACCOUNTS ====
INSERT INTO accounts (email, password, role_id, created_at) VALUES
('admin@greenquality.ru', 'admin123', 1, NOW()),              -- id = 1
('manager@greenquality.ru', 'manager123', 2, NOW()),          -- id = 2
('dispatcher@greenquality.ru', 'disp123', 2, NOW()),          -- id = 3
('pilot.volkov@greenquality.ru', 'pilot123', 2, NOW()),       -- id = 4
('pilot.smirnova@greenquality.ru', 'pilot123', 2, NOW()),     -- id = 5
('steward.ivanova@greenquality.ru', 'crew123', 3, NOW()),     -- id = 6
('steward.kozlov@greenquality.ru', 'crew123', 3, NOW()),      -- id = 7
('steward.orlova@greenquality.ru', 'crew123', 3, NOW()),      -- id = 8
('user1@greenquality.ru', 'user123', 3, NOW()),               -- id = 9
('user2@greenquality.ru', 'user456', 3, NOW());               -- id = 10

-- ==== AIRPORTS ====
INSERT INTO airports (id_airport, name, city, country) VALUES
('SVO', 'Международный аэропорт Шереметьево', 'Москва', 'Россия'),
('LED', 'Аэропорт Пулково', 'Санкт-Петербург', 'Россия'),
('KZN', 'Аэропорт Казань', 'Казань', 'Россия'),
('SVX', 'Аэропорт Кольцово', 'Екатеринбург', 'Россия'),
('ROV', 'Аэропорт Платов', 'Ростов-на-Дону', 'Россия');

-- ==== AIRPLANES ====
INSERT INTO airplanes (model, registration_number, capacity, economy_capacity, business_capacity, first_capacity, rows, seats_row)
VALUES
('Sukhoi Superjet 100', 'RA-89001', 98, 80, 12, 6, 20, 5),
('Airbus A320', 'RA-89022', 180, 150, 24, 6, 30, 6),
('Boeing 737-800', 'RA-73100', 189, 160, 24, 5, 32, 6);

-- ==== CLASS ====
INSERT INTO class (class_name) VALUES
('Эконом'),
('Бизнес'),
('Первый');

-- ==== EMPLOYEES ====
INSERT INTO employees (first_name, patronymic, last_name, position, account_id)
VALUES
('Иван', 'Петрович', 'Сидоров', 'Менеджер по рейсам', 2),
('Ольга', 'Владимировна', 'Кузнецова', 'Кадровик', 3);

-- ==== CREW ====
INSERT INTO crew (first_name, patronymic, last_name, position, account_id)
VALUES
('Алексей', 'Николаевич', 'Волков', 'Командир воздушного судна', 4),
('Марина', 'Игоревна', 'Смирнова', 'Второй пилот', 5),
('Ольга', 'Васильевна', 'Иванова', 'Бортпроводник', 6),
('Дмитрий', 'Петрович', 'Козлов', 'Бортпроводник', 7),
('Екатерина', 'Сергеевна', 'Орлова', 'Бортпроводник', 8);

-- ==== USERS ====
INSERT INTO users (account_id, first_name, patronymic, last_name, phone, passport_number, birthday) VALUES
(9, 'Сергей', 'Александрович', 'Новиков', '+79031234567', '4010 123456', '1985-03-12'),
(10, 'Анна', 'Петровна', 'Морозова', '+79261234567', '4011 654321', '1990-06-25');

-- ==== PASSENGERS ====
INSERT INTO passengers (first_name, patronymic, last_name, passport_number, bithday) VALUES
('Сергей', 'Александрович', 'Новиков', '4010 123456', '1985-03-12'),
('Анна', 'Петровна', 'Морозова', '4011 654321', '1990-06-25'),
('Игорь', 'Николаевич', 'Белов', '4012 112233', '1978-12-02'),
('Елена', 'Викторовна', 'Козлова', '4013 998877', '1995-04-10');

-- ==== PAYMENTS ====
INSERT INTO payments (payment_date, total_cost, user_id, payment_method, status) VALUES
('2025-11-01 10:00:00', 7500.00, 1, 'Карта Мир', 'Оплачен'),
('2025-11-02 15:30:00', 12500.00, 2, 'Кредитная карта', 'Оплачен');

-- ==== FLIGHTS ====
INSERT INTO flights (airplane_id, status, departure_airport_id, arrival_airport_id, departure_time, arrival_time)
VALUES
(1, 'Запланирован', 'SVO', 'LED', '2025-11-10 08:00:00', '2025-11-10 09:30:00'),  -- id = 1
(2, 'Запланирован', 'SVO', 'KZN', '2025-11-11 07:45:00', '2025-11-11 09:00:00'),  -- id = 2
(3, 'Запланирован', 'LED', 'SVX', '2025-11-12 10:15:00', '2025-11-12 13:00:00');  -- id = 3

-- ==== FLIGHT_CREW ====
INSERT INTO flight_crew (flight_id, crew_id) VALUES
(1, 1), (1, 2), (1, 3), (1, 4),
(2, 1), (2, 2), (2, 5),
(3, 1), (3, 3), (3, 5);

-- ============================================
-- ==== ГЕНЕРАЦИЯ ВСЕХ БИЛЕТОВ ДЛЯ РЕЙСОВ ====
-- ============================================

-- === Рейс 1 (Sukhoi Superjet 100, 98 мест) ===
INSERT INTO tickets (flight_id, class_id, seat, price, status)
SELECT 
    1 AS flight_id,
    CASE WHEN s <= 12 THEN 2 ELSE 1 END AS class_id,
    s AS seat,
    CASE WHEN s <= 12 THEN 11000.00 ELSE 7500.00 END AS price,
    CASE WHEN s % 10 = 0 THEN 'Забронирован' ELSE 'Свободен' END AS status
FROM generate_series(1, 98) AS s;

-- === Рейс 2 (Airbus A320, 180 мест) ===
INSERT INTO tickets (flight_id, class_id, seat, price, status)
SELECT 
    2 AS flight_id,
    CASE WHEN s <= 24 THEN 2 ELSE 1 END AS class_id,
    s AS seat,
    CASE WHEN s <= 24 THEN 13000.00 ELSE 8700.00 END AS price,
    CASE WHEN s % 15 = 0 THEN 'Забронирован' ELSE 'Свободен' END AS status
FROM generate_series(1, 180) AS s;

-- === Рейс 3 (Boeing 737-800, 189 мест) ===
INSERT INTO tickets (flight_id, class_id, seat, price, status)
SELECT 
    3 AS flight_id,
    CASE WHEN s <= 30 THEN 2 ELSE 1 END AS class_id,
    s AS seat,
    CASE WHEN s <= 30 THEN 14500.00 ELSE 8900.00 END AS price,
    CASE WHEN s % 20 = 0 THEN 'Забронирован' ELSE 'Свободен' END AS status
FROM generate_series(1, 189) AS s;

-- === Пример нескольких проданных билетов ===
UPDATE tickets SET passenger_id = 1, payment_id = 1, status = 'Выдан'
WHERE flight_id = 1 AND seat IN (1, 2);

UPDATE tickets SET passenger_id = 2, payment_id = 2, status = 'Выдан'
WHERE flight_id = 2 AND seat IN (3, 4);
