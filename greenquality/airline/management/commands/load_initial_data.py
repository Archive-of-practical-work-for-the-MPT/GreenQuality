"""
Management команда для загрузки начальных данных в базу данных
Использование: python manage.py load_initial_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from airline.models import (
    Airport, Airplane, Flight, Role, Class, Account, User, BaggageType
)
from decimal import Decimal


class Command(BaseCommand):
    help = 'Загружает начальные данные в базу данных (аэропорты, самолеты, рейсы)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаем загрузку начальных данных...'))
        
        # Создаем роли
        self.create_roles()
        
        # Создаем классы обслуживания
        self.create_classes()
        
        # Создаем аэропорты
        self.create_airports()
        
        # Создаем самолеты
        self.create_airplanes()
        
        # Создаем типы багажа
        self.create_baggage_types()
        
        # Создаем рейсы
        self.create_flights()
        
        self.stdout.write(self.style.SUCCESS('✓ Начальные данные успешно загружены!'))

    def create_roles(self):
        """Создание ролей"""
        roles_data = [
            {'role_name': 'USER'},
            {'role_name': 'ADMIN'},
            {'role_name': 'MANAGER'},
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(**role_data)
            if created:
                self.stdout.write(f'  ✓ Создана роль: {role.role_name}')
            else:
                self.stdout.write(f'  - Роль уже существует: {role.role_name}')

    def create_classes(self):
        """Создание классов обслуживания"""
        classes_data = [
            {'class_name': 'ECONOMY'},
            {'class_name': 'BUSINESS'},
            {'class_name': 'FIRST'},
        ]
        
        for class_data in classes_data:
            class_obj, created = Class.objects.get_or_create(**class_data)
            if created:
                self.stdout.write(f'  ✓ Создан класс: {class_obj.get_class_name_display()}')
            else:
                self.stdout.write(f'  - Класс уже существует: {class_obj.get_class_name_display()}')

    def create_airports(self):
        """Создание аэропортов"""
        airports_data = [
            {'id_airport': 'SVO', 'name': 'Шереметьево', 'city': 'Москва', 'country': 'Россия'},
            {'id_airport': 'LED', 'name': 'Пулково', 'city': 'Санкт-Петербург', 'country': 'Россия'},
            {'id_airport': 'AER', 'name': 'Сочи', 'city': 'Сочи', 'country': 'Россия'},
            {'id_airport': 'MSQ', 'name': 'Минск', 'city': 'Минск', 'country': 'Беларусь'},
            {'id_airport': 'CDG', 'name': 'Шарль де Голль', 'city': 'Париж', 'country': 'Франция'},
            {'id_airport': 'JFK', 'name': 'Джон Кеннеди', 'city': 'Нью-Йорк', 'country': 'США'},
            {'id_airport': 'NRT', 'name': 'Нarita', 'city': 'Токио', 'country': 'Япония'},
        ]
        
        for airport_data in airports_data:
            airport, created = Airport.objects.get_or_create(
                id_airport=airport_data['id_airport'],
                defaults={
                    'name': airport_data['name'],
                    'city': airport_data['city'],
                    'country': airport_data['country']
                }
            )
            if created:
                self.stdout.write(f'  ✓ Создан аэропорт: {airport.name} ({airport.id_airport})')
            else:
                self.stdout.write(f'  - Аэропорт уже существует: {airport.name}')

    def create_baggage_types(self):
        """Создание типов багажа"""
        baggage_types_data = [
            {
                'type_name': 'STANDARD',
                'max_weight_kg': Decimal('23.00'),
                'description': 'Стандартный багаж до 23 кг',
                'base_price': Decimal('2000.00')
            },
            {
                'type_name': 'EXTRA',
                'max_weight_kg': Decimal('32.00'),
                'description': 'Дополнительный багаж до 32 кг',
                'base_price': Decimal('3500.00')
            },
            {
                'type_name': 'SPORT',
                'max_weight_kg': Decimal('30.00'),
                'description': 'Спортивный инвентарь до 30 кг',
                'base_price': Decimal('5000.00')
            },
            {
                'type_name': 'OVERSIZE',
                'max_weight_kg': Decimal('50.00'),
                'description': 'Крупногабаритный багаж до 50 кг',
                'base_price': Decimal('8000.00')
            },
        ]
        
        for baggage_data in baggage_types_data:
            baggage_type, created = BaggageType.objects.get_or_create(
                type_name=baggage_data['type_name'],
                defaults={
                    'max_weight_kg': baggage_data['max_weight_kg'],
                    'description': baggage_data['description'],
                    'base_price': baggage_data['base_price']
                }
            )
            if created:
                self.stdout.write(f'  ✓ Создан тип багажа: {baggage_type.get_type_name_display()}')
            else:
                self.stdout.write(f'  - Тип багажа уже существует: {baggage_type.get_type_name_display()}')

    def create_airplanes(self):
        """Создание самолетов"""
        airplanes_data = [
            {
                'model': 'Airbus A320',
                'registration_number': 'GQ-A320-001',
                'capacity': 180,
                'economy_capacity': 150,
                'business_capacity': 30,
                'first_capacity': 0,
                'rows': 30,
                'seats_row': 6
            },
            {
                'model': 'Boeing 737',
                'registration_number': 'GQ-B737-001',
                'capacity': 189,
                'economy_capacity': 162,
                'business_capacity': 27,
                'first_capacity': 0,
                'rows': 31,
                'seats_row': 6
            },
            {
                'model': 'Airbus A350',
                'registration_number': 'GQ-A350-001',
                'capacity': 325,
                'economy_capacity': 280,
                'business_capacity': 40,
                'first_capacity': 5,
                'rows': 50,
                'seats_row': 7
            },
            {
                'model': 'Boeing 777',
                'registration_number': 'GQ-B777-001',
                'capacity': 396,
                'economy_capacity': 350,
                'business_capacity': 40,
                'first_capacity': 6,
                'rows': 60,
                'seats_row': 7
            },
        ]
        
        for airplane_data in airplanes_data:
            airplane, created = Airplane.objects.get_or_create(
                registration_number=airplane_data['registration_number'],
                defaults=airplane_data
            )
            if created:
                self.stdout.write(f'  ✓ Создан самолет: {airplane.model} ({airplane.registration_number})')
            else:
                self.stdout.write(f'  - Самолет уже существует: {airplane.model}')

    def create_flights(self):
        """Создание рейсов"""
        now = timezone.now()
        
        # Получаем аэропорты
        try:
            svo = Airport.objects.get(id_airport='SVO')
            led = Airport.objects.get(id_airport='LED')
            aer = Airport.objects.get(id_airport='AER')
            msq = Airport.objects.get(id_airport='MSQ')
            cdg = Airport.objects.get(id_airport='CDG')
            jfk = Airport.objects.get(id_airport='JFK')
        except Airport.DoesNotExist:
            self.stdout.write(self.style.ERROR('  ✗ Аэропорты не найдены. Сначала создайте аэропорты.'))
            return
        
        # Получаем самолеты
        try:
            a320 = Airplane.objects.filter(model='Airbus A320').first()
            b737 = Airplane.objects.filter(model='Boeing 737').first()
            a350 = Airplane.objects.filter(model='Airbus A350').first()
            b777 = Airplane.objects.filter(model='Boeing 777').first()
        except Airplane.DoesNotExist:
            self.stdout.write(self.style.ERROR('  ✗ Самолеты не найдены. Сначала создайте самолеты.'))
            return
        
        flights_data = [
            # Москва - Санкт-Петербург
            {
                'airplane_id': a320,
                'status': 'SCHEDULED',
                'departure_airport_id': svo,
                'arrival_airport_id': led,
                'departure_time': now + timedelta(days=1, hours=8, minutes=45),
                'arrival_time': now + timedelta(days=1, hours=10, minutes=15),
            },
            {
                'airplane_id': a320,
                'status': 'SCHEDULED',
                'departure_airport_id': svo,
                'arrival_airport_id': led,
                'departure_time': now + timedelta(days=2, hours=14, minutes=30),
                'arrival_time': now + timedelta(days=2, hours=16, minutes=0),
            },
            # Москва - Сочи
            {
                'airplane_id': b737,
                'status': 'SCHEDULED',
                'departure_airport_id': svo,
                'arrival_airport_id': aer,
                'departure_time': now + timedelta(days=1, hours=12, minutes=30),
                'arrival_time': now + timedelta(days=1, hours=14, minutes=45),
            },
            # Москва - Минск
            {
                'airplane_id': a320,
                'status': 'DELAYED',
                'departure_airport_id': svo,
                'arrival_airport_id': msq,
                'departure_time': now + timedelta(days=1, hours=16, minutes=20),
                'arrival_time': now + timedelta(days=1, hours=17, minutes=55),
                'actual_departure_time': now + timedelta(days=1, hours=16, minutes=50),
            },
            # Москва - Париж
            {
                'airplane_id': a350,
                'status': 'SCHEDULED',
                'departure_airport_id': svo,
                'arrival_airport_id': cdg,
                'departure_time': now + timedelta(days=1, hours=21, minutes=10),
                'arrival_time': now + timedelta(days=2, hours=0, minutes=45),
            },
            # Санкт-Петербург - Москва
            {
                'airplane_id': a320,
                'status': 'SCHEDULED',
                'departure_airport_id': led,
                'arrival_airport_id': svo,
                'departure_time': now + timedelta(days=1, hours=9, minutes=30),
                'arrival_time': now + timedelta(days=1, hours=11, minutes=0),
            },
            # Сочи - Москва
            {
                'airplane_id': b737,
                'status': 'SCHEDULED',
                'departure_airport_id': aer,
                'arrival_airport_id': svo,
                'departure_time': now + timedelta(days=1, hours=13, minutes=15),
                'arrival_time': now + timedelta(days=1, hours=15, minutes=30),
            },
            # Минск - Москва
            {
                'airplane_id': a320,
                'status': 'SCHEDULED',
                'departure_airport_id': msq,
                'arrival_airport_id': svo,
                'departure_time': now + timedelta(days=1, hours=18, minutes=40),
                'arrival_time': now + timedelta(days=1, hours=20, minutes=15),
            },
            # Париж - Москва
            {
                'airplane_id': a350,
                'status': 'CANCELLED',
                'departure_airport_id': cdg,
                'arrival_airport_id': svo,
                'departure_time': now + timedelta(days=1, hours=7, minutes=25),
                'arrival_time': now + timedelta(days=1, hours=11, minutes=0),
            },
            # Москва - Нью-Йорк (долгий перелет)
            {
                'airplane_id': b777,
                'status': 'SCHEDULED',
                'departure_airport_id': svo,
                'arrival_airport_id': jfk,
                'departure_time': now + timedelta(days=1, hours=23, minutes=30),
                'arrival_time': now + timedelta(days=2, hours=6, minutes=45),  # ~11 часов полета
            },
            # Нью-Йорк - Москва (долгий перелет ~10 часов + разница во времени)
            {
                'airplane_id': b777,
                'status': 'SCHEDULED',
                'departure_airport_id': jfk,
                'arrival_airport_id': svo,
                'departure_time': now + timedelta(days=2, hours=14, minutes=20),
                'arrival_time': now + timedelta(days=3, hours=0, minutes=20),  # ~10 часов полета + разница во времени
            },
            # Дополнительные рейсы
            {
                'airplane_id': a320,
                'status': 'SCHEDULED',
                'departure_airport_id': svo,
                'arrival_airport_id': led,
                'departure_time': now + timedelta(days=3, hours=6, minutes=0),
                'arrival_time': now + timedelta(days=3, hours=7, minutes=30),
            },
            {
                'airplane_id': b737,
                'status': 'SCHEDULED',
                'departure_airport_id': svo,
                'arrival_airport_id': aer,
                'departure_time': now + timedelta(days=3, hours=10, minutes=15),
                'arrival_time': now + timedelta(days=3, hours=12, minutes=30),
            },
        ]
        
        created_count = 0
        for flight_data in flights_data:
            # Проверяем, не существует ли уже такой рейс
            existing = Flight.objects.filter(
                departure_airport_id=flight_data['departure_airport_id'],
                arrival_airport_id=flight_data['arrival_airport_id'],
                departure_time=flight_data['departure_time']
            ).first()
            
            if not existing:
                flight = Flight.objects.create(**flight_data)
                created_count += 1
                route = f"{flight.departure_airport_id.city} → {flight.arrival_airport_id.city}"
                self.stdout.write(f'  ✓ Создан рейс: {route} ({flight.departure_time.strftime("%d.%m.%Y %H:%M")})')
        
        if created_count > 0:
            self.stdout.write(f'  ✓ Всего создано рейсов: {created_count}')
        else:
            self.stdout.write('  - Рейсы уже существуют')
