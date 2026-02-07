"""
Функциональные Unit-тесты: CRUD операции над моделями.
Запуск: из папки greenquality выполнить
  python manage.py test tests.test_crud
"""
from datetime import date
from django.test import TestCase
from airline.models import Airport, Passenger, Role


class AirportCRUDTest(TestCase):
    """Функциональный тест: CRUD для модели Airport (аэропорт)."""

    def test_airport_crud(self):
        """CRUD для аэропорта (Airport): создание, чтение, обновление, удаление."""
        # Create
        airport = Airport.objects.create(
            id_airport='TST',
            name='Тестовый аэропорт',
            city='Тестоград',
            country='Россия'
        )
        self.assertIsNotNone(airport.id_airport)
        self.assertEqual(airport.name, 'Тестовый аэропорт')

        # Read
        found = Airport.objects.get(id_airport='TST')
        self.assertEqual(found.city, 'Тестоград')

        # Update
        airport.name = 'Обновлённый аэропорт'
        airport.save()
        found.refresh_from_db()
        self.assertEqual(found.name, 'Обновлённый аэропорт')

        # Delete
        pk = airport.id_airport
        airport.delete()
        self.assertFalse(Airport.objects.filter(id_airport=pk).exists())


class PassengerCRUDTest(TestCase):
    """Функциональный тест: CRUD для модели Passenger (пассажир)."""

    def test_passenger_crud(self):
        """CRUD для пассажира (Passenger): создание, чтение, обновление, удаление."""
        # Create
        passenger = Passenger.objects.create(
            first_name='Иван',
            patronymic='Петрович',
            last_name='Тестов',
            passport_number='1234 567890',
            birthday=date(1990, 5, 15)
        )
        self.assertIsNotNone(passenger.id_passenger)
        self.assertEqual(passenger.last_name, 'Тестов')

        # Read
        found = Passenger.objects.get(passport_number='1234 567890')
        self.assertEqual(found.first_name, 'Иван')

        # Update
        passenger.last_name = 'Обновлён'
        passenger.save()
        found.refresh_from_db()
        self.assertEqual(found.last_name, 'Обновлён')

        # Delete
        pk = passenger.id_passenger
        passenger.delete()
        self.assertFalse(Passenger.objects.filter(id_passenger=pk).exists())


class RoleCRUDTest(TestCase):
    """Функциональный тест: CRUD для модели Role (роль)."""

    def test_role_crud(self):
        """CRUD для роли (Role): создание, чтение, обновление, удаление."""
        # Create
        role = Role.objects.create(role_name='TEST_ROLE')
        self.assertIsNotNone(role.id_role)
        self.assertEqual(role.role_name, 'TEST_ROLE')

        # Read
        found = Role.objects.get(role_name='TEST_ROLE')
        self.assertEqual(found.id_role, role.id_role)

        # Update
        role.role_name = 'UPDATED_ROLE'
        role.save()
        found.refresh_from_db()
        self.assertEqual(found.role_name, 'UPDATED_ROLE')

        # Delete
        pk = role.id_role
        role.delete()
        self.assertFalse(Role.objects.filter(id_role=pk).exists())
