from django.db import models
from django.contrib.auth.models import AbstractUser


class Role(models.Model):
    id_role = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self):
        return str(self.role_name)


class Account(models.Model):
    id_account = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    role_id = models.ForeignKey(
        Role, on_delete=models.CASCADE, db_column='role_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts'
        verbose_name = 'Аккаунт'
        verbose_name_plural = 'Аккаунты'

    def __str__(self):
        return str(self.email)


class AuditLog(models.Model):
    id_audit = models.AutoField(primary_key=True)
    table_name = models.CharField(max_length=50)
    record_id = models.IntegerField()
    operation = models.CharField(max_length=10, choices=[(
        'INSERT', 'Insert'), ('UPDATE', 'Update'), ('DELETE', 'Delete')])
    old_data = models.JSONField(blank=True, null=True)
    new_data = models.JSONField(blank=True, null=True)
    changed_by = models.ForeignKey(
        Account, on_delete=models.SET_NULL, blank=True, null=True, db_column='changed_by')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_log'
        verbose_name = 'Журнал аудита'
        verbose_name_plural = 'Журналы аудита'


class Airport(models.Model):
    id_airport = models.CharField(primary_key=True, max_length=3)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=50)

    class Meta:
        db_table = 'airports'
        verbose_name = 'Аэропорт'
        verbose_name_plural = 'Аэропорты'

    def __str__(self):
        return str(self.name)


class Airplane(models.Model):
    id_airplane = models.AutoField(primary_key=True)
    model = models.CharField(max_length=50)
    registration_number = models.CharField(unique=True, max_length=20)
    capacity = models.IntegerField()
    economy_capacity = models.IntegerField(blank=True, null=True)
    business_capacity = models.IntegerField(blank=True, null=True)
    first_capacity = models.IntegerField(blank=True, null=True)
    rows = models.IntegerField(blank=True, null=True)
    seats_row = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'airplanes'
        verbose_name = 'Самолет'
        verbose_name_plural = 'Самолеты'

    def __str__(self):
        return str(self.model)


class Flight(models.Model):
    id_flight = models.AutoField(primary_key=True)
    airplane_id = models.ForeignKey(
        Airplane, on_delete=models.CASCADE, db_column='airplane_id')
    status = models.CharField(max_length=30, choices=[
        ('SCHEDULED', 'Запланирован'),
        ('DELAYED', 'Задержан'),
        ('CANCELLED', 'Отменен'),
        ('COMPLETED', 'Выполнен')
    ], default='SCHEDULED')
    departure_airport_id = models.ForeignKey(
        Airport, on_delete=models.CASCADE, db_column='departure_airport_id', related_name='departure_flights')
    arrival_airport_id = models.ForeignKey(
        Airport, on_delete=models.CASCADE, db_column='arrival_airport_id', related_name='arrival_flights')
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    actual_departure_time = models.DateTimeField(blank=True, null=True)
    actual_arrival_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'flights'
        verbose_name = 'Рейс'
        verbose_name_plural = 'Рейсы'
        constraints = [
            models.CheckConstraint(
                check=models.Q(departure_time__lt=models.F('arrival_time')),
                name='check_departure_before_arrival'
            )
        ]

    def __str__(self):
        return f"Flight {self.id_flight}: {self.departure_airport_id} -> {self.arrival_airport_id}"


class Passenger(models.Model):
    id_passenger = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    passport_number = models.CharField(max_length=20, unique=True)
    birthday = models.DateField()

    class Meta:
        db_table = 'passengers'
        verbose_name = 'Пассажир'
        verbose_name_plural = 'Пассажиры'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Class(models.Model):
    id_class = models.AutoField(primary_key=True)
    class_name = models.CharField(max_length=50, unique=True, choices=[
        ('ECONOMY', 'Эконом'),
        ('BUSINESS', 'Бизнес'),
        ('FIRST', 'Первый')
    ])

    class Meta:
        db_table = 'class'
        verbose_name = 'Класс'
        verbose_name_plural = 'Классы'

    def __str__(self):
        return str(self.class_name)


class User(models.Model):
    id_user = models.AutoField(primary_key=True)
    account_id = models.OneToOneField(
        Account, on_delete=models.CASCADE, db_column='account_id')
    first_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, blank=True, null=True)
    passport_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Payment(models.Model):
    id_payment = models.AutoField(primary_key=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    total_cost = models.DecimalField(max_digits=9, decimal_places=2)
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, db_column='user_id')
    payment_method = models.CharField(max_length=30, choices=[
        ('CARD', 'Карта'),
        ('CASH', 'Наличные'),
        ('ONLINE', 'Онлайн')
    ])
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Ожидает'),
        ('COMPLETED', 'Завершен'),
        ('FAILED', 'Ошибка')
    ], default='PENDING')

    class Meta:
        db_table = 'payments'
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'

    def __str__(self):
        return f"Payment {self.id_payment}"


class Ticket(models.Model):
    id_ticket = models.AutoField(primary_key=True)
    flight_id = models.ForeignKey(
        Flight, on_delete=models.CASCADE, db_column='flight_id')
    class_id = models.ForeignKey(
        Class, on_delete=models.CASCADE, db_column='class_id')
    seat_number = models.CharField(max_length=5)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[
        ('AVAILABLE', 'Свободен'),
        ('BOOKED', 'Забронирован'),
        ('PAID', 'Оплачен'),
        ('CHECKED_IN', 'Зарегистрирован'),
        ('CANCELLED', 'Отменен')
    ], default='AVAILABLE')
    passenger_id = models.ForeignKey(
        Passenger, on_delete=models.CASCADE, db_column='passenger_id', blank=True, null=True)
    payment_id = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, blank=True, null=True, db_column='payment_id')

    class Meta:
        db_table = 'tickets'
        verbose_name = 'Билет'
        verbose_name_plural = 'Билеты'
        constraints = [
            models.UniqueConstraint(
                fields=['flight_id', 'seat_number'], name='unique_flight_seat')
        ]

    def __str__(self):
        return f"Ticket {self.id_ticket} - Seat {self.seat_number}"


# Новые таблицы для багажа

class BaggageType(models.Model):
    id_baggage_type = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=50, unique=True, choices=[
        ('HAND', 'Ручная кладь'),
        ('STANDARD', 'Стандартный'),
        ('EXTRA', 'Дополнительный'),
        ('SPORT', 'Спортивный инвентарь'),
        ('OVERSIZE', 'Крупногабаритный')
    ])
    max_weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        db_table = 'baggage_types'
        verbose_name = 'Тип багажа'
        verbose_name_plural = 'Типы багажа'

    def __str__(self):
        return f"{self.type_name} (до {self.max_weight_kg} кг)"


class Baggage(models.Model):
    id_baggage = models.AutoField(primary_key=True)
    ticket_id = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, db_column='ticket_id', related_name='baggage_items')
    baggage_type_id = models.ForeignKey(
        BaggageType, on_delete=models.CASCADE, db_column='baggage_type_id')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    # Уникальный номер багажной бирки
    baggage_tag = models.CharField(max_length=12, unique=True)
    status = models.CharField(max_length=20, choices=[
        ('REGISTERED', 'Зарегистрирован'),
        ('LOADED', 'Загружен'),
        ('DELIVERED', 'Выдан'),
        ('LOST', 'Утерян')
    ], default='REGISTERED')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'baggage'
        verbose_name = 'Багаж'
        verbose_name_plural = 'Багаж'

    def __str__(self):
        return f"Baggage {self.baggage_tag} ({self.weight_kg} кг)"
