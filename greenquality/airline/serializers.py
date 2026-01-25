"""
Сериализаторы для Django REST Framework
Преобразуют модели Django в JSON и обратно
"""
from rest_framework import serializers
from .models import (
    Airport, Flight, Ticket, User, Account, Payment, 
    Passenger, Class, Airplane, Role, Baggage, BaggageType
)


class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Role (Роли)"""
    class Meta:
        model = Role
        fields = ['id_role', 'role_name']


class AirportSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Airport (Аэропорты)"""
    class Meta:
        model = Airport
        fields = ['id_airport', 'name', 'city', 'country']


class AirplaneSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Airplane (Самолеты)"""
    class Meta:
        model = Airplane
        fields = [
            'id_airplane', 'model', 'registration_number', 'capacity',
            'economy_capacity', 'business_capacity', 'first_capacity',
            'rows', 'seats_row'
        ]


class FlightSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Flight (Рейсы)"""
    # Включаем связанные объекты для удобства
    departure_airport = AirportSerializer(source='departure_airport_id', read_only=True)
    arrival_airport = AirportSerializer(source='arrival_airport_id', read_only=True)
    airplane = AirplaneSerializer(source='airplane_id', read_only=True)
    
    # Для создания/обновления используем только ID
    departure_airport_id = serializers.CharField(write_only=True)
    arrival_airport_id = serializers.CharField(write_only=True)
    airplane_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Flight
        fields = [
            'id_flight', 'airplane_id', 'airplane', 'status',
            'departure_airport_id', 'departure_airport',
            'arrival_airport_id', 'arrival_airport',
            'departure_time', 'arrival_time',
            'actual_departure_time', 'actual_arrival_time'
        ]
        read_only_fields = ['id_flight']


class PassengerSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Passenger (Пассажиры)"""
    class Meta:
        model = Passenger
        fields = [
            'id_passenger', 'first_name', 'patronymic', 'last_name',
            'passport_number', 'birthday'
        ]


class ClassSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Class (Классы обслуживания)"""
    class Meta:
        model = Class
        fields = ['id_class', 'class_name']


class AccountSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Account (Аккаунты)"""
    role = RoleSerializer(source='role_id', read_only=True)
    role_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Account
        fields = ['id_account', 'email', 'password', 'role_id', 'role', 'created_at']
        read_only_fields = ['id_account', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}  # Пароль не возвращается в ответе
        }


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User (Пользователи)"""
    account = AccountSerializer(source='account_id', read_only=True)
    account_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id_user', 'account_id', 'account', 'first_name', 'patronymic',
            'last_name', 'phone', 'passport_number', 'birthday'
        ]


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Payment (Платежи)"""
    user = UserSerializer(source='user_id', read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id_payment', 'payment_date', 'total_cost', 'user_id', 'user',
            'payment_method', 'status'
        ]
        read_only_fields = ['id_payment', 'payment_date']


class TicketSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ticket (Билеты)"""
    # Включаем связанные объекты
    flight = FlightSerializer(source='flight_id', read_only=True)
    passenger = PassengerSerializer(source='passenger_id', read_only=True)
    class_obj = ClassSerializer(source='class_id', read_only=True)
    payment = PaymentSerializer(source='payment_id', read_only=True)
    
    # Для создания/обновления используем только ID
    flight_id = serializers.IntegerField(write_only=True)
    passenger_id = serializers.IntegerField(write_only=True)
    class_id = serializers.IntegerField(write_only=True)
    payment_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id_ticket', 'flight_id', 'flight', 'class_id', 'class_obj',
            'seat_number', 'price', 'status', 'passenger_id', 'passenger',
            'payment_id', 'payment'
        ]
        read_only_fields = ['id_ticket']


class BaggageTypeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели BaggageType (Типы багажа)"""
    class Meta:
        model = BaggageType
        fields = [
            'id_baggage_type', 'type_name', 'max_weight_kg',
            'description', 'base_price'
        ]


class BaggageSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Baggage (Багаж)"""
    ticket = TicketSerializer(source='ticket_id', read_only=True)
    baggage_type = BaggageTypeSerializer(source='baggage_type_id', read_only=True)
    
    ticket_id = serializers.IntegerField(write_only=True)
    baggage_type_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Baggage
        fields = [
            'id_baggage', 'ticket_id', 'ticket', 'baggage_type_id', 'baggage_type',
            'weight_kg', 'baggage_tag', 'status', 'registered_at'
        ]
        read_only_fields = ['id_baggage', 'registered_at']
