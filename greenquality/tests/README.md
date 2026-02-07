# Тесты GreenQuality

Шесть тестов: три функциональных (CRUD) и три интеграционных (API и экспорт).

## Запуск

Из папки `greenquality` (где лежит `manage.py`):

```bash
# Все тесты пакета tests
python manage.py test tests

# Только CRUD
python manage.py test tests.test_crud

# Только API
python manage.py test tests.test_api

# Только экспорт
python manage.py test tests.test_export
```

## Состав

| № | Модуль        | Тест                          | Тип           |
|---|---------------|-------------------------------|----------------|
| 1 | test_crud     | Airport CRUD                  | Функциональный |
| 2 | test_crud     | Passenger CRUD                | Функциональный |
| 3 | test_crud     | Role CRUD                     | Функциональный |
| 4 | test_api      | API аэропортов (list/create/get) | Интеграционный |
| 5 | test_api      | API рейсов (list/search/upcoming) | Интеграционный |
| 6 | test_export   | Экспорт статистики (CSV/PDF)  | Интеграционный |

Для API-тестов в сессии создаётся пользователь с ролью ADMIN (требуется для доступа к API). Для теста экспорта создаётся менеджер (MANAGER).
