"""
URL маршруты для RESTful API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    AirportViewSet, FlightViewSet, TicketViewSet,
    UserViewSet, AccountViewSet, PaymentViewSet,
    PassengerViewSet, ClassViewSet, AirplaneViewSet,
    RoleViewSet, BaggageViewSet, BaggageTypeViewSet
)

# Создаем роутер для автоматической генерации URL маршрутов
router = DefaultRouter()

# Регистрируем ViewSets
router.register(r'airports', AirportViewSet, basename='airport')
router.register(r'flights', FlightViewSet, basename='flight')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'users', UserViewSet, basename='user')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'passengers', PassengerViewSet, basename='passenger')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'airplanes', AirplaneViewSet, basename='airplane')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'baggage', BaggageViewSet, basename='baggage')
router.register(r'baggage-types', BaggageTypeViewSet, basename='baggage-type')

# URL patterns для API
urlpatterns = [
    path('', include(router.urls)),
]
