"""
Интеграционные тесты: REST API (аэропорты, рейсы).
Запуск: из папки greenquality выполнить
  python manage.py test tests.test_api
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airline.models import Airport, Airplane, Flight, Role, Account


def _login_as_admin(client):
    """Создаёт роль ADMIN, аккаунт и авторизует сессию для доступа к API."""
    role = Role.objects.create(role_name='ADMIN')
    account = Account.objects.create(
        email='admin@test.local',
        password='hash',
        role_id=role
    )
    session = client.session
    session['account_id'] = account.id_account
    session.save()
    return account


class AirportAPITest(TestCase):
    """Интеграционный тест: API аэропортов (список, создание, чтение по id)."""

    def setUp(self):
        self.client = APIClient()
        _login_as_admin(self.client)
        Airport.objects.create(
            id_airport='SVO',
            name='Шереметьево',
            city='Москва',
            country='Россия'
        )

    def test_api_airports_list_and_create(self):
        """API аэропортов: список (GET), создание (POST), чтение по id (GET)."""
        # GET /api/airports/ — список
        url_list = reverse('airport-list')
        response = self.client.get(url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('results', data)
        self.assertGreaterEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['id_airport'], 'SVO')

        # POST /api/airports/ — создание
        payload = {
            'id_airport': 'LED',
            'name': 'Пулково',
            'city': 'Санкт-Петербург',
            'country': 'Россия'
        }
        response = self.client.post(url_list, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], 'Пулково')
        self.assertTrue(Airport.objects.filter(id_airport='LED').exists())

        # GET /api/airports/LED/ — чтение по id
        url_detail = reverse('airport-detail', kwargs={'pk': 'LED'})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['city'], 'Санкт-Петербург')


class FlightAPITest(TestCase):
    """Интеграционный тест: API рейсов (список, поиск, предстоящие)."""

    def setUp(self):
        self.client = APIClient()
        _login_as_admin(self.client)
        self.airport_svo = Airport.objects.create(
            id_airport='SVO',
            name='Шереметьево',
            city='Москва',
            country='Россия'
        )
        self.airport_led = Airport.objects.create(
            id_airport='LED',
            name='Пулково',
            city='Санкт-Петербург',
            country='Россия'
        )
        self.airplane = Airplane.objects.create(
            model='Boeing 737',
            registration_number='RA-12345',
            capacity=180
        )
        from django.utils import timezone
        from datetime import timedelta
        self.future = timezone.now() + timedelta(days=1)
        self.past = timezone.now() - timedelta(days=1)
        Flight.objects.create(
            airplane_id=self.airplane,
            status='SCHEDULED',
            departure_airport_id=self.airport_svo,
            arrival_airport_id=self.airport_led,
            departure_time=self.future,
            arrival_time=self.future + timedelta(hours=2)
        )

    def test_api_flights_list_search_upcoming(self):
        """API рейсов: список, поиск по городам, предстоящие рейсы."""
        # GET /api/flights/ — список рейсов
        url_list = reverse('flight-list')
        response = self.client.get(url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('results', data)
        self.assertGreaterEqual(len(data['results']), 1)

        # GET /api/flights/search/?departure=Москва&arrival=Санкт-Петербург
        url_search = reverse('flight-search')
        response = self.client.get(
            url_search,
            {'departure': 'Москва', 'arrival': 'Санкт-Петербург'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)
        self.assertGreaterEqual(len(response.json()), 1)

        # GET /api/flights/upcoming/ — предстоящие рейсы
        url_upcoming = reverse('flight-upcoming')
        response = self.client.get(url_upcoming)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)
