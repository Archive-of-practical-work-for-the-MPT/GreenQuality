# Нагрузочное тестирование Locust

## Подготовка

1. Установить зависимости:
   ```bash
   pip install locust
   ```

2. Запустить Django-сервер (в отдельном терминале):
   ```bash
   cd greenquality
   python manage.py runserver
   ```

3. Убедиться, что в БД есть аккаунт администратора:
   - Email: `admin@gmail.com`
   - Пароль: `adminadmin`
   (создаётся скриптом `scripts/insert_initial_data.sql`)

## Запуск с веб-интерфейсом

Из папки `greenquality`:

```bash
locust --config tests/locust/locust.conf
```

Или без конфига:

```bash
locust -f tests/locust/locustfile.py --host http://localhost:8000
```

Затем откройте в браузере: **http://localhost:8089**

## В веб-интерфейсе

1. Укажите число пользователей (Users) и скорость появления (Spawn rate).
2. Нажмите **Start swarming**.
3. Следите за статистикой, графиками и ошибками в реальном времени.

## Классы пользователей

| Класс        | Описание                                                      |
|-------------|---------------------------------------------------------------|
| WebsiteUser | Просмотр публичных страниц: главная, о компании, контакты, рейсы |
| ApiUser     | Работа с REST API после авторизации: аэропорты, рейсы, поиск  |

Включён `class-picker` — в веб-интерфейсе можно выбрать один или несколько классов.

## Headless (без веб-интерфейса)

```bash
locust -f tests/locust/locustfile.py --host http://localhost:8000 --headless -u 20 -r 5 -t 60s
```

- `-u 20` — 20 пользователей
- `-r 5` — 5 пользователей в секунду
- `-t 60s` — длительность 60 секунд
