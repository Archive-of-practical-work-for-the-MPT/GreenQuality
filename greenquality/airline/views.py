from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


def index(request):
    return render(request, 'index.html')


def control_panel(request):
    """Control panel view with links to CRUD operations for all models"""
    # Define the models and their API endpoints
    models_info = [
        {'name': 'Роли', 'endpoint': 'roles', 'model': 'Role'},
        {'name': 'Аккаунты', 'endpoint': 'accounts', 'model': 'Account'},
        {'name': 'Журналы аудита', 'endpoint': 'auditlogs', 'model': 'AuditLog'},
        {'name': 'Аэропорты', 'endpoint': 'airports', 'model': 'Airport'},
        {'name': 'Самолеты', 'endpoint': 'airplanes', 'model': 'Airplane'},
        {'name': 'Сотрудники', 'endpoint': 'employees', 'model': 'Employee'},
        {'name': 'Экипажи', 'endpoint': 'crew', 'model': 'Crew'},
        {'name': 'Рейсы', 'endpoint': 'flights', 'model': 'Flight'},
        {'name': 'Экипажи рейсов', 'endpoint': 'flightcrew', 'model': 'FlightCrew'},
        {'name': 'Пассажиры', 'endpoint': 'passengers', 'model': 'Passenger'},
        {'name': 'Классы', 'endpoint': 'classes', 'model': 'Class'},
        {'name': 'Пользователи', 'endpoint': 'users', 'model': 'User'},
        {'name': 'Платежи', 'endpoint': 'payments', 'model': 'Payment'},
        {'name': 'Билеты', 'endpoint': 'tickets', 'model': 'Ticket'},
    ]

    context = {
        'models_info': models_info
    }
    return render(request, 'control_panel.html', context)


def crud_interface(request, model_name):
    """CRUD interface for a specific model"""
    # Map model names to display names
    model_display_names = {
        'roles': 'Роли',
        'accounts': 'Аккаунты',
        'auditlogs': 'Журналы аудита',
        'airports': 'Аэропорты',
        'airplanes': 'Самолеты',
        'employees': 'Сотрудники',
        'crew': 'Экипажи',
        'flights': 'Рейсы',
        'flightcrew': 'Экипажи рейсов',
        'passengers': 'Пассажиры',
        'classes': 'Классы',
        'users': 'Пользователи',
        'payments': 'Платежи',
        'tickets': 'Билеты',
    }

    context = {
        'model_name': model_name,
        'model_display_name': model_display_names.get(model_name, model_name),
    }
    return render(request, 'crud_interface.html', context)
