# RESTful API Документация

## Что такое RESTful API?

RESTful API (Representational State Transfer) - это архитектурный стиль для создания веб-сервисов. В нашем случае Django REST Framework позволяет Django сайту общаться с базой данных через HTTP запросы, возвращая данные в формате JSON.

## Как это работает?

### 1. **Сериализаторы (serializers.py)**
Сериализаторы преобразуют модели Django в JSON формат и обратно:
- **Сериализация** (Model → JSON): когда данные из базы данных отправляются клиенту
- **Десериализация** (JSON → Model): когда данные от клиента сохраняются в базу данных

### 2. **ViewSets (api_views.py)**
ViewSets предоставляют стандартные операции CRUD:
- **Create** (POST) - создание новой записи
- **Read** (GET) - чтение записи/записей
- **Update** (PUT/PATCH) - обновление записи
- **Delete** (DELETE) - удаление записи

### 3. **Роутер (api_urls.py)**
Роутер автоматически создает URL маршруты для каждого ViewSet:
- `/api/airports/` - работа с аэропортами
- `/api/flights/` - работа с рейсами
- `/api/tickets/` - работа с билетами
- и т.д.

## Доступные API Endpoints

### Базовые URL:
- `http://localhost:8000/api/airports/` - Аэропорты
- `http://localhost:8000/api/flights/` - Рейсы
- `http://localhost:8000/api/tickets/` - Билеты
- `http://localhost:8000/api/users/` - Пользователи
- `http://localhost:8000/api/accounts/` - Аккаунты
- `http://localhost:8000/api/payments/` - Платежи
- `http://localhost:8000/api/passengers/` - Пассажиры
- `http://localhost:8000/api/classes/` - Классы обслуживания
- `http://localhost:8000/api/airplanes/` - Самолеты
- `http://localhost:8000/api/roles/` - Роли
- `http://localhost:8000/api/baggage/` - Багаж
- `http://localhost:8000/api/baggage-types/` - Типы багажа

### Специальные endpoints:

#### Поиск аэропортов:
```
GET /api/airports/search/?q=Москва
```

#### Поиск рейсов:
```
GET /api/flights/search/?departure=Москва&arrival=Санкт-Петербург
```

#### Предстоящие рейсы:
```
GET /api/flights/upcoming/
```

#### Билеты пользователя:
```
GET /api/tickets/by_user/?user_id=1
```

#### Платежи пользователя:
```
GET /api/payments/by_user/?user_id=1
```

## Как проверить API?

### Способ 1: Через браузер (Browsable API)

1. Запустите сервер Django:
```bash
python manage.py runserver
```

2. Откройте в браузере:
```
http://localhost:8000/api/
```

3. Вы увидите список всех доступных API endpoints. Кликните на любой из них для просмотра и тестирования.

### Способ 2: Через curl (командная строка)

#### Получить список всех аэропортов:
```bash
curl http://localhost:8000/api/airports/
```

#### Получить конкретный аэропорт (ID=1):
```bash
curl http://localhost:8000/api/airports/1/
```

#### Создать новый аэропорт:
```bash
curl -X POST http://localhost:8000/api/airports/ \
  -H "Content-Type: application/json" \
  -d '{"id_airport": "SVO", "name": "Шереметьево", "city": "Москва", "country": "Россия"}'
```

#### Обновить аэропорт:
```bash
curl -X PUT http://localhost:8000/api/airports/SVO/ \
  -H "Content-Type: application/json" \
  -d '{"id_airport": "SVO", "name": "Шереметьево", "city": "Москва", "country": "Россия"}'
```

#### Удалить аэропорт:
```bash
curl -X DELETE http://localhost:8000/api/airports/SVO/
```

### Способ 3: Через Python (requests)

```python
import requests

# Получить список рейсов
response = requests.get('http://localhost:8000/api/flights/')
flights = response.json()
print(flights)

# Создать новый рейс
new_flight = {
    "airplane_id": 1,
    "status": "SCHEDULED",
    "departure_airport_id": "SVO",
    "arrival_airport_id": "LED",
    "departure_time": "2025-02-01T10:00:00Z",
    "arrival_time": "2025-02-01T12:00:00Z"
}
response = requests.post(
    'http://localhost:8000/api/flights/',
    json=new_flight
)
print(response.json())
```

### Способ 4: Через Postman

1. Установите Postman (https://www.postman.com/)
2. Создайте новый запрос
3. Выберите метод (GET, POST, PUT, DELETE)
4. Введите URL: `http://localhost:8000/api/airports/`
5. Для POST/PUT запросов:
   - Перейдите на вкладку "Body"
   - Выберите "raw" и "JSON"
   - Введите данные в формате JSON
6. Нажмите "Send"

### Способ 5: Через JavaScript (fetch)

```javascript
// Получить список рейсов
fetch('http://localhost:8000/api/flights/')
  .then(response => response.json())
  .then(data => console.log(data));

// Создать новый рейс
fetch('http://localhost:8000/api/flights/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    airplane_id: 1,
    status: 'SCHEDULED',
    departure_airport_id: 'SVO',
    arrival_airport_id: 'LED',
    departure_time: '2025-02-01T10:00:00Z',
    arrival_time: '2025-02-01T12:00:00Z'
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

## Примеры использования

### Получить все рейсы с детальной информацией:
```
GET http://localhost:8000/api/flights/
```

Ответ будет включать:
- Информацию о рейсе
- Аэропорты отправления и прибытия (полная информация)
- Информацию о самолете

### Поиск рейсов:
```
GET http://localhost:8000/api/flights/search/?departure=Москва&arrival=Санкт-Петербург
```

### Получить билеты пользователя:
```
GET http://localhost:8000/api/tickets/by_user/?user_id=1
```

## HTTP Методы

- **GET** - получение данных (чтение)
- **POST** - создание новой записи
- **PUT** - полное обновление записи
- **PATCH** - частичное обновление записи
- **DELETE** - удаление записи

## Формат ответа

Все ответы приходят в формате JSON:

```json
{
  "count": 10,
  "next": "http://localhost:8000/api/flights/?page=2",
  "previous": null,
  "results": [
    {
      "id_flight": 1,
      "status": "SCHEDULED",
      "departure_airport": {
        "id_airport": "SVO",
        "name": "Шереметьево",
        "city": "Москва",
        "country": "Россия"
      },
      ...
    }
  ]
}
```

## Пагинация

API автоматически разбивает результаты на страницы (по 20 записей на страницу). Используйте параметры:
- `?page=1` - первая страница
- `?page=2` - вторая страница
- и т.д.

## Обработка ошибок

При ошибке API вернет JSON с описанием проблемы:

```json
{
  "error": "Описание ошибки",
  "detail": "Детальная информация"
}
```

## Безопасность

⚠️ **Важно**: В текущей конфигурации API доступен всем (AllowAny). Для production необходимо настроить аутентификацию и авторизацию.
