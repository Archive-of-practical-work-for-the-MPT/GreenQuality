"""Функции для панели администратора"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.utils.dateparse import parse_date, parse_datetime
from django.urls import reverse
from decimal import Decimal
from .models import (
    User, Account, Role, Payment, Ticket, Flight, Passenger, 
    Airport, Class, BaggageType, Baggage, Airplane, AuditLog
)


def admin_panel(request):
    """Панель администратора с CRUD для всех таблиц"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        messages.error(request, 'Для доступа к панели администратора необходимо войти в систему')
        return redirect('login')
    
    account_id = request.session['account_id']
    
    try:
        account = Account.objects.get(id_account=account_id)
        # Проверка роли администратора
        if not account.role_id or account.role_id.role_name != 'ADMIN':
            messages.error(request, 'У вас нет доступа к панели администратора')
            return redirect('index')
        
        # Определяем все модели для отображения
        models_info = {
            'Role': {
                'model': Role,
                'name': 'Роли',
                'fields': ['id_role', 'role_name'],
                'readonly': False,
            },
            'Account': {
                'model': Account,
                'name': 'Аккаунты',
                'fields': ['id_account', 'email', 'role_id', 'created_at'],
                'readonly': False,
            },
            'User': {
                'model': User,
                'name': 'Пользователи',
                'fields': ['id_user', 'account_id', 'first_name', 'last_name', 'patronymic', 'phone', 'passport_number', 'birthday'],
                'readonly': False,
            },
            'Airport': {
                'model': Airport,
                'name': 'Аэропорты',
                'fields': ['id_airport', 'name', 'city', 'country'],
                'readonly': False,
            },
            'Airplane': {
                'model': Airplane,
                'name': 'Самолеты',
                'fields': ['id_airplane', 'model', 'registration_number', 'capacity', 'economy_capacity', 'business_capacity', 'first_capacity', 'rows', 'seats_row'],
                'readonly': False,
            },
            'Flight': {
                'model': Flight,
                'name': 'Рейсы',
                'fields': ['id_flight', 'airplane_id', 'departure_airport_id', 'arrival_airport_id', 'departure_time', 'arrival_time', 'status'],
                'readonly': False,
            },
            'Passenger': {
                'model': Passenger,
                'name': 'Пассажиры',
                'fields': ['id_passenger', 'first_name', 'last_name', 'patronymic', 'passport_number', 'birthday'],
                'readonly': False,
            },
            'Class': {
                'model': Class,
                'name': 'Классы обслуживания',
                'fields': ['id_class', 'class_name'],
                'readonly': False,
            },
            'Payment': {
                'model': Payment,
                'name': 'Платежи',
                'fields': ['id_payment', 'user_id', 'payment_date', 'total_cost', 'payment_method', 'status'],
                'readonly': False,
            },
            'Ticket': {
                'model': Ticket,
                'name': 'Билеты',
                'fields': ['id_ticket', 'flight_id', 'class_id', 'seat_number', 'price', 'status', 'passenger_id', 'payment_id'],
                'readonly': False,
            },
            'BaggageType': {
                'model': BaggageType,
                'name': 'Типы багажа',
                'fields': ['id_baggage_type', 'type_name', 'max_weight_kg', 'description', 'base_price'],
                'readonly': False,
            },
            'Baggage': {
                'model': Baggage,
                'name': 'Багаж',
                'fields': ['id_baggage', 'ticket_id', 'baggage_type_id', 'weight_kg', 'baggage_tag', 'status', 'registered_at'],
                'readonly': False,
            },
            'AuditLog': {
                'model': AuditLog,
                'name': 'Журнал аудита',
                'fields': ['id_audit', 'table_name', 'record_id', 'operation', 'changed_by', 'changed_at'],
                'readonly': True,  # Только просмотр
            },
        }
        
        # Получаем выбранную таблицу из GET параметра
        selected_table = request.GET.get('table', 'Role')
        if selected_table not in models_info:
            selected_table = 'Role'
        
        model_info = models_info[selected_table]
        model = model_info['model']
        
        # Получаем все записи выбранной таблицы
        objects = model.objects.all()
        
        # Применяем select_related для ForeignKey полей
        if selected_table == 'Account':
            objects = objects.select_related('role_id')
        elif selected_table == 'User':
            objects = objects.select_related('account_id')
        elif selected_table == 'Flight':
            objects = objects.select_related('airplane_id', 'departure_airport_id', 'arrival_airport_id')
        elif selected_table == 'Ticket':
            objects = objects.select_related('flight_id', 'class_id', 'passenger_id', 'payment_id')
        elif selected_table == 'Payment':
            objects = objects.select_related('user_id')
        elif selected_table == 'Baggage':
            objects = objects.select_related('ticket_id', 'baggage_type_id')
        elif selected_table == 'AuditLog':
            objects = objects.select_related('changed_by')
        
        # Сортируем по первичному ключу
        objects = objects.order_by('-pk')[:100]  # Ограничиваем 100 записями для производительности
        
        context = {
            'models_info': models_info,
            'selected_table': selected_table,
            'model_info': model_info,
            'objects': objects,
            'fields': model_info['fields'],
        }
        
        return render(request, 'admin_panel.html', context)
        
    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('index')


def admin_crud(request):
    """Обработка CRUD операций для панели администратора"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        messages.error(request, 'Для доступа к панели администратора необходимо войти в систему')
        return redirect('login')
    
    account_id = request.session['account_id']
    
    try:
        account = Account.objects.get(id_account=account_id)
        # Проверка роли администратора
        if not account.role_id or account.role_id.role_name != 'ADMIN':
            messages.error(request, 'У вас нет доступа к панели администратора')
            return redirect('index')
        
        table_name = request.POST.get('table_name')
        action = request.POST.get('action')  # create, update, delete
        record_id = request.POST.get('record_id')
        
        # Маппинг имен таблиц на модели
        model_map = {
            'Role': Role,
            'Account': Account,
            'User': User,
            'Airport': Airport,
            'Airplane': Airplane,
            'Flight': Flight,
            'Passenger': Passenger,
            'Class': Class,
            'Payment': Payment,
            'Ticket': Ticket,
            'BaggageType': BaggageType,
            'Baggage': Baggage,
        }
        
        if table_name not in model_map:
            messages.error(request, 'Неизвестная таблица')
            return redirect('/admin-panel/')
        
        model = model_map[table_name]
        
        if action == 'delete':
            if not record_id:
                messages.error(request, 'ID записи не указан')
                return redirect(f'/admin-panel/?table={table_name}')
            try:
                obj = model.objects.get(pk=record_id)
                obj.delete()
                messages.success(request, 'Запись успешно удалена')
            except model.DoesNotExist:
                messages.error(request, 'Запись не найдена')
            except Exception as e:
                messages.error(request, f'Ошибка при удалении: {str(e)}')
            return redirect(f'/admin-panel/?table={table_name}')
        
        elif action in ['create', 'update']:
            # Получаем данные из POST
            data = {}
            password_field_present = False
            password_value = None
            
            for key, value in request.POST.items():
                if key not in ['csrfmiddlewaretoken', 'table_name', 'action', 'record_id']:
                    if key == 'password':
                        # Отдельно обрабатываем пароль
                        password_field_present = True
                        password_value = value
                    elif value:  # Только непустые значения для остальных полей
                        data[key] = value
            
            # Обрабатываем ForeignKey поля
            fk_fields_map = {
                'role_id': Role,
                'account_id': Account,
                'user_id': User,
                'airplane_id': Airplane,
                'departure_airport_id': Airport,
                'arrival_airport_id': Airport,
                'class_id': Class,
                'passenger_id': Passenger,
                'flight_id': Flight,
                'payment_id': Payment,
                'ticket_id': Ticket,
                'baggage_type_id': BaggageType,
            }
            
            for field_name, related_model in fk_fields_map.items():
                if field_name in data and data[field_name]:
                    try:
                        data[field_name] = related_model.objects.get(pk=data[field_name])
                    except related_model.DoesNotExist:
                        messages.error(request, f'Связанная запись не найдена для поля {field_name}')
                        return redirect(f'/admin-panel/?table={table_name}')
                elif field_name in data:
                    data[field_name] = None
            
            # Обрабатываем пароль отдельно
            # При создании - пароль обязателен
            # При обновлении - пароль обновляется только если он был введен (не пустой)
            if action == 'create':
                if not password_field_present or not password_value:
                    messages.error(request, 'Пароль обязателен при создании аккаунта')
                    return redirect(f'/admin-panel/?table={table_name}')
                data['password'] = make_password(password_value)
            elif action == 'update':
                # При обновлении пароль обновляется только если он был введен
                if password_field_present and password_value:
                    data['password'] = make_password(password_value)
                # Если пароль не был введен, просто не добавляем его в data
                # и он не будет обновлен
            
            if 'birthday' in data:
                if data['birthday']:
                    try:
                        data['birthday'] = parse_date(data['birthday'])
                    except:
                        data['birthday'] = None
                else:
                    data['birthday'] = None
            
            # Обрабатываем Decimal поля
            decimal_fields = ['total_cost', 'price', 'max_weight_kg', 'base_price', 'weight_kg']
            for field_name in decimal_fields:
                if field_name in data and data[field_name]:
                    try:
                        data[field_name] = Decimal(str(data[field_name]))
                    except:
                        pass
            
            # Обрабатываем datetime поля
            if 'departure_time' in data or 'arrival_time' in data:
                if 'departure_time' in data and data['departure_time']:
                    try:
                        data['departure_time'] = parse_datetime(data['departure_time'])
                    except:
                        pass
                if 'arrival_time' in data and data['arrival_time']:
                    try:
                        data['arrival_time'] = parse_datetime(data['arrival_time'])
                    except:
                        pass
            
            if action == 'create':
                # Создаем новую запись
                try:
                    obj = model.objects.create(**data)
                    messages.success(request, 'Запись успешно создана')
                except Exception as e:
                    messages.error(request, f'Ошибка при создании: {str(e)}')
            elif action == 'update':
                # Обновляем существующую запись
                if not record_id:
                    messages.error(request, 'ID записи не указан')
                    return redirect(f'/admin-panel/?table={table_name}')
                try:
                    obj = model.objects.get(pk=record_id)
                    for key, value in data.items():
                        setattr(obj, key, value)
                    obj.save()
                    messages.success(request, 'Запись успешно обновлена')
                except model.DoesNotExist:
                    messages.error(request, 'Запись не найдена')
                except Exception as e:
                    messages.error(request, f'Ошибка при обновлении: {str(e)}')
            
            return redirect(f'/admin-panel/?table={table_name}')
        
        return redirect('/admin-panel/')
        
    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('index')


def admin_get_record(request):
    """Получение данных записи для редактирования"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        return JsonResponse({'error': 'Не авторизован'}, status=401)
    
    account_id = request.session['account_id']
    
    try:
        account = Account.objects.get(id_account=account_id)
        if not account.role_id or account.role_id.role_name != 'ADMIN':
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        
        table_name = request.GET.get('table')
        record_id = request.GET.get('id')
        
        model_map = {
            'Role': Role,
            'Account': Account,
            'User': User,
            'Airport': Airport,
            'Airplane': Airplane,
            'Flight': Flight,
            'Passenger': Passenger,
            'Class': Class,
            'Payment': Payment,
            'Ticket': Ticket,
            'BaggageType': BaggageType,
            'Baggage': Baggage,
        }
        
        if table_name not in model_map:
            return JsonResponse({'error': 'Неизвестная таблица'}, status=400)
        
        model = model_map[table_name]
        obj = model.objects.get(pk=record_id)
        
        # Преобразуем объект в словарь
        data = {}
        for field in model._meta.get_fields():
            if hasattr(obj, field.name):
                # Не возвращаем пароль при редактировании (безопасность)
                if field.name == 'password':
                    continue
                value = getattr(obj, field.name)
                if value is None:
                    data[field.name] = None
                elif hasattr(value, 'pk'):  # ForeignKey
                    data[field.name] = value.pk
                elif hasattr(value, 'isoformat'):  # DateTime или Date
                    data[field.name] = value.isoformat()
                else:
                    data[field.name] = str(value)
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def admin_get_options(request):
    """Получение опций для select полей"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        return JsonResponse({'error': 'Не авторизован'}, status=401)
    
    account_id = request.session['account_id']
    
    try:
        account = Account.objects.get(id_account=account_id)
        if not account.role_id or account.role_id.role_name != 'ADMIN':
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        
        model_name = request.GET.get('model')
        
        model_map = {
            'Role': (Role, 'id_role', 'role_name'),
            'Account': (Account, 'id_account', 'email'),
            'User': (User, 'id_user', lambda x: f"{x.first_name} {x.last_name}"),
            'Airport': (Airport, 'id_airport', 'name'),
            'Airplane': (Airplane, 'id_airplane', 'model'),
            'Flight': (Flight, 'id_flight', lambda x: f"GQ{x.id_flight:03d}"),
            'Passenger': (Passenger, 'id_passenger', lambda x: f"{x.first_name} {x.last_name}"),
            'Class': (Class, 'id_class', 'class_name'),
            'Payment': (Payment, 'id_payment', 'id_payment'),
            'Ticket': (Ticket, 'id_ticket', 'id_ticket'),
            'BaggageType': (BaggageType, 'id_baggage_type', 'type_name'),
            'Baggage': (Baggage, 'id_baggage', 'baggage_tag'),
        }
        
        if model_name not in model_map:
            return JsonResponse({'error': 'Неизвестная модель'}, status=400)
        
        model, pk_field, display_field = model_map[model_name]
        objects = model.objects.all()[:100]  # Ограничиваем для производительности
        
        options = []
        for obj in objects:
            pk_value = getattr(obj, pk_field)
            if callable(display_field):
                display_value = display_field(obj)
            else:
                display_value = getattr(obj, display_field)
            options.append({
                'value': pk_value,
                'text': str(display_value)
            })
        
        return JsonResponse(options, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
