# Загрузка начальных данных в базу данных

## Как создать БД и загрузить начальные данные

Из корня проекта выполните:

```bash
python scripts/setup_database.py
```

Или на Windows двойной щелчок по `scripts\setup_database.bat`

Скрипт выполняет:
1. Создание базы данных greenquality (если не существует)
2. Создание таблиц (`scripts/create_tables.sql`)
3. Заполнение начальными данными (`scripts/insert_initial_data.sql`)

### Дополнительные опции

```bash
python scripts/setup_database.py --create     # только создать таблицы
python scripts/setup_database.py --seed       # только заполнить данными
python scripts/setup_database.py --init-db    # только создать БД
```

## Что будет загружено

### 1. Роли
- USER (Пользователь)
- ADMIN (Администратор)
- MANAGER (Менеджер)

### 2. Классы обслуживания
- ECONOMY (Эконом)
- BUSINESS (Бизнес)
- FIRST (Первый)

### 3. Аэропорты
- SVO - Шереметьево (Москва, Россия)
- LED - Пулково (Санкт-Петербург, Россия)
- AER - Сочи (Сочи, Россия)
- MSQ - Минск (Минск, Беларусь)
- CDG - Шарль де Голль (Париж, Франция)
- JFK - Джон Кеннеди (Нью-Йорк, США)
- NRT - Narita (Токио, Япония)

### 4. Самолёты
- Airbus A320 (180 мест)
- Boeing 737 (189 мест)
- Airbus A350 (325 мест)
- Boeing 777 (396 мест)

### 5. Администратор
- Email: admin@gmail.com
- Пароль: adminadmin

### 6. Рейсы
Создаётся 13 рейсов между различными городами:
- Москва ↔ Санкт-Петербург
- Москва ↔ Сочи
- Москва ↔ Минск
- Москва ↔ Париж
- Москва ↔ Нью-Йорк
- И другие направления

Время рейсов рассчитывается относительно момента выполнения скрипта.

## Примечания

- Требуется `.env` с настройками `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- При повторном запуске `create_tables.sql` пересоздаёт все таблицы (данные будут удалены)
- Для Django-миграций (auth, sessions и т.д.): `cd greenquality && python manage.py migrate`

## Проверка

После выполнения скрипта:
1. Страница рейсов: http://localhost:8000/flights/
2. API: http://localhost:8000/api/flights/
3. Вход в админку: admin@gmail.com / adminadmin
