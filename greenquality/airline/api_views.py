"""
API Views для Django REST Framework
Предоставляют RESTful API endpoints для работы с моделями
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import (
    Airport, Flight, Ticket, User, Account, Payment,
    Passenger, Class, Airplane, Role, Baggage, BaggageType
)
from .serializers import (
    AirportSerializer, FlightSerializer, TicketSerializer,
    UserSerializer, AccountSerializer, PaymentSerializer,
    PassengerSerializer, ClassSerializer, AirplaneSerializer,
    RoleSerializer, BaggageSerializer, BaggageTypeSerializer
)


class AirportViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с аэропортами
    Предоставляет CRUD операции: Create, Read, Update, Delete
    """
    queryset = Airport.objects.all().order_by('id_airport')
    serializer_class = AirportSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Поиск аэропортов по городу или названию"""
        query = request.query_params.get('q', '')
        if query:
            airports = Airport.objects.filter(
                Q(city__icontains=query) | Q(name__icontains=query)
            )
            serializer = self.get_serializer(airports, many=True)
            return Response(serializer.data)
        return Response([])


class FlightViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с рейсами
    """
    queryset = Flight.objects.select_related(
        'departure_airport_id', 'arrival_airport_id', 'airplane_id'
    ).order_by('id_flight')
    serializer_class = FlightSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Поиск рейсов по аэропортам отправления/прибытия"""
        departure = request.query_params.get('departure', '')
        arrival = request.query_params.get('arrival', '')
        
        flights = Flight.objects.all()
        
        if departure:
            flights = flights.filter(departure_airport_id__city__icontains=departure)
        if arrival:
            flights = flights.filter(arrival_airport_id__city__icontains=arrival)
        
        serializer = self.get_serializer(flights, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Получить предстоящие рейсы"""
        from django.utils import timezone
        flights = Flight.objects.filter(
            departure_time__gte=timezone.now(),
            status__in=['SCHEDULED', 'DELAYED']
        ).order_by('departure_time')
        serializer = self.get_serializer(flights, many=True)
        return Response(serializer.data)


class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с билетами
    """
    queryset = Ticket.objects.select_related(
        'flight_id', 'passenger_id', 'class_id', 'payment_id'
    ).all()
    serializer_class = TicketSerializer
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Получить билеты пользователя через платежи"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Получаем все платежи пользователя
        payments = Payment.objects.filter(user_id=user_id)
        # Получаем все билеты этих платежей
        tickets = Ticket.objects.filter(payment_id__in=payments)
        
        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с пользователями
    """
    queryset = User.objects.select_related('account_id').all()
    serializer_class = UserSerializer


class AccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с аккаунтами
    """
    queryset = Account.objects.select_related('role_id').all()
    serializer_class = AccountSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с платежами
    """
    queryset = Payment.objects.select_related('user_id').all()
    serializer_class = PaymentSerializer
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Получить платежи пользователя"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payments = Payment.objects.filter(user_id=user_id).order_by('-payment_date')
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)


class PassengerViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с пассажирами
    """
    queryset = Passenger.objects.all()
    serializer_class = PassengerSerializer


class ClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с классами обслуживания (только чтение)
    """
    queryset = Class.objects.all()
    serializer_class = ClassSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с самолетами
    """
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с ролями (только чтение)
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class BaggageTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с типами багажа (только чтение)
    """
    queryset = BaggageType.objects.all()
    serializer_class = BaggageTypeSerializer


class BaggageViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с багажом
    """
    queryset = Baggage.objects.select_related('ticket_id', 'baggage_type_id').all()
    serializer_class = BaggageSerializer
