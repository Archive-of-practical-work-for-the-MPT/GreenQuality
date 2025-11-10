from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'roles', api_views.RoleViewSet)
router.register(r'accounts', api_views.AccountViewSet)
router.register(r'auditlogs', api_views.AuditLogViewSet)
router.register(r'airports', api_views.AirportViewSet)
router.register(r'airplanes', api_views.AirplaneViewSet)
router.register(r'employees', api_views.EmployeeViewSet)
router.register(r'crew', api_views.CrewViewSet)
router.register(r'flights', api_views.FlightViewSet)
router.register(r'flightcrew', api_views.FlightCrewViewSet)
router.register(r'passengers', api_views.PassengerViewSet)
router.register(r'classes', api_views.ClassViewSet)
router.register(r'users', api_views.UserViewSet)
router.register(r'payments', api_views.PaymentViewSet)
router.register(r'tickets', api_views.TicketViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', api_views.api_root),
    path('', include(router.urls)),
]
