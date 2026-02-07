"""
Locust: нагрузочное тестирование GreenQuality.

Два типа пользователей:
- WebsiteUser: просмотр публичных страниц (главная, о компании, контакты, рейсы).
- ApiUser: работа с API после авторизации (аэропорты, рейсы, поиск).

Запуск с веб-интерфейсом:
  cd greenquality && locust -f tests/locust/locustfile.py --config tests/locust/locust.conf

Или без конфига:
  locust -f tests/locust/locustfile.py --host http://localhost:8000

Затем открыть http://localhost:8089
"""
import re
from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    """Пользователь, просматривающий публичные страницы сайта."""

    wait_time = between(1, 3)

    @task(3)
    def index(self):
        """Главная страница."""
        self.client.get("/")

    @task(2)
    def about(self):
        """Страница «О компании»."""
        self.client.get("/about/")

    @task(1)
    def contacts(self):
        """Страница контактов."""
        self.client.get("/contacts/")

    @task(4)
    def flights(self):
        """Страница с рейсами."""
        self.client.get("/flights/")


class ApiUser(HttpUser):
    """
    Пользователь API: авторизуется и выполняет запросы к REST API.
    Требуется аккаунт администратора (admin@gmail.com / adminadmin).
    """

    wait_time = between(0.5, 2)

    def on_start(self):
        """Авторизация при старте виртуального пользователя."""
        self._login()

    def _login(self):
        """Вход в систему для получения сессии."""
        response = self.client.get("/login/")
        if response.status_code != 200:
            return
        csrf = self.client.cookies.get("csrftoken")
        if not csrf:
            # Пытаемся извлечь из HTML
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
            csrf = match.group(1) if match else ""
        self.client.post(
            "/login/",
            {
                "email": "admin@gmail.com",
                "password": "adminadmin",
                "csrfmiddlewaretoken": csrf,
            },
            headers={"Referer": f"{self.host}/login/"},
        )

    @task(4)
    def api_airports_list(self):
        """Список аэропортов."""
        self.client.get("/api/airports/")

    @task(3)
    def api_flights_list(self):
        """Список рейсов."""
        self.client.get("/api/flights/")

    @task(2)
    def api_flights_search(self):
        """Поиск рейсов Москва — Санкт-Петербург."""
        self.client.get(
            "/api/flights/search/",
            params={"departure": "Москва", "arrival": "Санкт-Петербург"},
        )

    @task(2)
    def api_flights_upcoming(self):
        """Предстоящие рейсы."""
        self.client.get("/api/flights/upcoming/")

    @task(1)
    def api_airports_search(self):
        """Поиск аэропортов по городу."""
        self.client.get("/api/airports/search/", params={"q": "Москва"})
