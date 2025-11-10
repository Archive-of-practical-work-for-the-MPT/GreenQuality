from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .models import (
    Role, Account, AuditLog, Airport, Airplane, Employee, Crew,
    Flight, FlightCrew, Passenger, Class, User, Payment, Ticket
)
from .serializers import (
    RoleSerializer, AccountSerializer, AuditLogSerializer, AirportSerializer,
    AirplaneSerializer, EmployeeSerializer, CrewSerializer, FlightSerializer,
    FlightCrewSerializer, PassengerSerializer, ClassSerializer, UserSerializer,
    PaymentSerializer, TicketSerializer
)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.AllowAny]


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [permissions.AllowAny]


class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.AllowAny]


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    permission_classes = [permissions.AllowAny]


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer
    permission_classes = [permissions.AllowAny]


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.AllowAny]


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = [permissions.AllowAny]


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    permission_classes = [permissions.AllowAny]


class FlightCrewViewSet(viewsets.ModelViewSet):
    queryset = FlightCrew.objects.all()
    serializer_class = FlightCrewSerializer
    permission_classes = [permissions.AllowAny]


class PassengerViewSet(viewsets.ModelViewSet):
    queryset = Passenger.objects.all()
    serializer_class = PassengerSerializer
    permission_classes = [permissions.AllowAny]


class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.AllowAny]


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'roles': reverse('role-list', request=request, format=format),
        'accounts': reverse('account-list', request=request, format=format),
        'auditlogs': reverse('auditlog-list', request=request, format=format),
        'airports': reverse('airport-list', request=request, format=format),
        'airplanes': reverse('airplane-list', request=request, format=format),
        'employees': reverse('employee-list', request=request, format=format),
        'crew': reverse('crew-list', request=request, format=format),
        'flights': reverse('flight-list', request=request, format=format),
        'flightcrew': reverse('flightcrew-list', request=request, format=format),
        'passengers': reverse('passenger-list', request=request, format=format),
        'classes': reverse('class-list', request=request, format=format),
        'users': reverse('user-list', request=request, format=format),
        'payments': reverse('payment-list', request=request, format=format),
        'tickets': reverse('ticket-list', request=request, format=format),
    })
