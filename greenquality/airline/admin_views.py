"""Функции для панели администратора"""
import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.messages import get_messages
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.utils.dateparse import parse_date, parse_datetime
from django.urls import reverse
from django.db import models as django_models
from decimal import Decimal, InvalidOperation
from .models import (
    User, Account, Role, Payment, Ticket, Flight, Passenger,
    Airport, Class, BaggageType, Baggage, Airplane, AuditLog
)
from .exceptions_utils import get_user_friendly_message
from .audit_utils import model_instance_to_audit_dict, get_record_id_for_audit, log_audit


def _validate_crud_data(model, data, action, instance=None):
    """
    Валидация данных для CRUD. Возвращает список строк с ошибками (пустой — если всё ок).
    """
    errors = []
    # Только конкретные поля модели (без обратных связей)
    for field in model._meta.fields:
        if getattr(field, 'primary_key', False) or isinstance(field, django_models.AutoField):
            continue
        if getattr(field, 'auto_now_add', False) or getattr(field, 'auto_now', False):
            continue

        value = data.get(field.name)
        is_empty = value is None or value == '' or (isinstance(value, str) and not value.strip())

        # Обязательность при создании
        if action == 'create':
            if not field.null and not getattr(field, 'blank', True):
                if is_empty:
                    label = getattr(field, 'verbose_name', field.name)
                    errors.append(f'Поле «{label}» обязательно для заполнения.')
                    continue
        elif action == 'update':
            if is_empty and not field.null and not getattr(field, 'blank', True):
                continue

        if is_empty:
            continue

        # Длина строки
        if isinstance(field, django_models.CharField) and hasattr(field, 'max_length'):
            if len(str(value)) > field.max_length:
                label = getattr(field, 'verbose_name', field.name)
                errors.append(f'Поле «{label}» не должно превышать {field.max_length} символов.')

        # Телефон: только цифры (допускается + в начале)
        if field.name == 'phone' and value:
            if not re.match(r'^\+?\d+$', str(value)):
                label = getattr(field, 'verbose_name', field.name)
                errors.append(f'Поле «{label}» должно содержать только цифры (в начале допускается +).')
        # Номер паспорта: только цифры и пробелы
        if field.name == 'passport_number' and value:
            if not re.match(r'^[\d\s]+$', str(value)):
                label = getattr(field, 'verbose_name', field.name)
                errors.append(f'Поле «{label}» должно содержать только цифры и пробелы.')

        # Выбор из списка (choices)
        if getattr(field, 'choices', None):
            allowed = [str(c[0]) for c in field.choices]
            if str(value) not in allowed:
                label = getattr(field, 'verbose_name', field.name)
                errors.append(f'Поле «{label}» должно быть одним из: {", ".join(allowed)}.')

        # Decimal: корректное число и не отрицательное где нужно
        if isinstance(field, django_models.DecimalField):
            try:
                d = Decimal(str(value))
                non_negative = field.name in (
                    'total_cost', 'price', 'max_weight_kg', 'base_price', 'weight_kg',
                    'capacity', 'economy_capacity', 'business_capacity', 'first_capacity', 'rows', 'seats_row'
                )
                if non_negative and d < 0:
                    label = getattr(field, 'verbose_name', field.name)
                    errors.append(f'Поле «{label}» должно быть не меньше нуля.')
            except (InvalidOperation, TypeError, ValueError):
                label = getattr(field, 'verbose_name', field.name)
                errors.append(f'Поле «{label}» должно быть числом.')

        # Integer: не отрицательный где нужно
        if isinstance(field, django_models.IntegerField) and not isinstance(field, django_models.AutoField):
            try:
                v = int(value)
                if field.name in ('capacity', 'economy_capacity', 'business_capacity', 'first_capacity', 'rows', 'seats_row') and v < 0:
                    label = getattr(field, 'verbose_name', field.name)
                    errors.append(f'Поле «{label}» должно быть не меньше нуля.')
            except (TypeError, ValueError):
                label = getattr(field, 'verbose_name', field.name)
                errors.append(f'Поле «{label}» должно быть целым числом.')

    return errors


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
                'fields': ['id_audit', 'table_name', 'record_id', 'operation', 'changed_by', 'changed_at', 'old_data', 'new_data'],
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
        
        # Сортировка по столбцу (из GET: sort_by, order=asc/desc)
        sort_by = request.GET.get('sort_by', '').strip()
        sort_order = request.GET.get('order', 'asc').lower()
        if sort_order not in ('asc', 'desc'):
            sort_order = 'asc'
        if sort_by and sort_by in model_info['fields']:
            order_field = sort_by if sort_order == 'asc' else f'-{sort_by}'
            objects = objects.order_by(order_field)
        else:
            sort_by = ''
            sort_order = 'asc'
            objects = objects.order_by('-pk')
        
        # Пагинация: 10 записей на странице
        paginator = Paginator(objects, 10)
        page_num = request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page_num)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Диапазон страниц для отображения (макс. 10)
        num_pages = paginator.num_pages
        current = page_obj.number
        if num_pages <= 10:
            page_range_display = list(range(1, num_pages + 1))
        else:
            start = max(1, min(current - 4, num_pages - 9))
            end = min(num_pages, start + 9)
            page_range_display = list(range(start, end + 1))
        
        # Удаляем сообщения об успешном входе из панели
        storage = get_messages(request)
        for message in storage:
            if message.message == 'Вы успешно вошли в систему!':
                storage.used = False
                break
        
        context = {
            'models_info': models_info,
            'selected_table': selected_table,
            'model_info': model_info,
            'objects': page_obj.object_list,
            'page_obj': page_obj,
            'page_range_display': page_range_display,
            'fields': model_info['fields'],
            'panel_type': 'admin',
            'sort_by': sort_by,
            'sort_order': sort_order,
        }
        
        return render(request, 'admin_panel.html', context)
        
    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except Exception as e:
        messages.error(request, get_user_friendly_message(e))
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
                old_data = model_instance_to_audit_dict(obj)
                rid = get_record_id_for_audit(obj)
                obj.delete()
                log_audit(table_name, rid, 'DELETE', account_id, old_data=old_data, new_data=None)
                messages.success(request, 'Запись успешно удалена')
            except model.DoesNotExist:
                messages.error(request, 'Запись не найдена')
            except Exception as e:
                messages.error(request, get_user_friendly_message(e, 'delete'))
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
                        messages.error(request, 'Связанная запись не найдена. Выберите существующее значение.')
                        return redirect(f'/admin-panel/?table={table_name}')
                elif field_name in data:
                    data[field_name] = None
            
            # Обрабатываем пароль отдельно (только для таблицы Account)
            if table_name == 'Account':
                if action == 'create':
                    if not password_field_present or not password_value:
                        messages.error(request, 'Пароль обязателен при создании аккаунта')
                        return redirect(f'/admin-panel/?table={table_name}')
                    data['password'] = make_password(password_value)
                elif action == 'update':
                    if password_field_present and password_value:
                        data['password'] = make_password(password_value)
            
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
                    except Exception:
                        pass
                if 'arrival_time' in data and data['arrival_time']:
                    try:
                        data['arrival_time'] = parse_datetime(data['arrival_time'])
                    except Exception:
                        pass

            # Валидация перед созданием/обновлением
            instance = None
            if action == 'update' and record_id:
                try:
                    instance = model.objects.get(pk=record_id)
                except model.DoesNotExist:
                    pass
            validation_errors = _validate_crud_data(model, data, action, instance=instance)
            if validation_errors:
                for err in validation_errors:
                    messages.error(request, err)
                return redirect(f'/admin-panel/?table={table_name}')

            if action == 'create':
                # Создаем новую запись
                try:
                    obj = model.objects.create(**data)
                    new_data = model_instance_to_audit_dict(obj)
                    rid = get_record_id_for_audit(obj)
                    log_audit(table_name, rid, 'INSERT', account_id, old_data=None, new_data=new_data)
                    messages.success(request, 'Запись успешно создана')
                except Exception as e:
                    messages.error(request, get_user_friendly_message(e, 'create'))
            elif action == 'update':
                # Обновляем существующую запись
                if not record_id:
                    messages.error(request, 'ID записи не указан')
                    return redirect(f'/admin-panel/?table={table_name}')
                try:
                    obj = model.objects.get(pk=record_id)
                    old_data = model_instance_to_audit_dict(obj)
                    for key, value in data.items():
                        setattr(obj, key, value)
                    obj.save()
                    new_data = model_instance_to_audit_dict(obj)
                    rid = get_record_id_for_audit(obj)
                    log_audit(table_name, rid, 'UPDATE', account_id, old_data=old_data, new_data=new_data)
                    messages.success(request, 'Запись успешно обновлена')
                except model.DoesNotExist:
                    messages.error(request, 'Запись не найдена')
                except Exception as e:
                    messages.error(request, get_user_friendly_message(e, 'update'))
            
            return redirect(f'/admin-panel/?table={table_name}')
        
        return redirect('/admin-panel/')
        
    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except Exception as e:
        messages.error(request, get_user_friendly_message(e))
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
        return JsonResponse({'error': get_user_friendly_message(e, 'load')}, status=500)


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
        return JsonResponse({'error': get_user_friendly_message(e, 'load')}, status=500)


def manager_panel(request):
    """Панель менеджера с CRUD для ограниченного набора таблиц"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        messages.error(request, 'Для доступа к панели менеджера необходимо войти в систему')
        return redirect('login')
    
    account_id = request.session['account_id']
    
    try:
        account = Account.objects.get(id_account=account_id)
        # Проверка роли менеджера
        if not account.role_id or account.role_id.role_name != 'MANAGER':
            messages.error(request, 'У вас нет доступа к панели менеджера')
            return redirect('index')
        
        # Определяем доступные модели для менеджера (ограниченный список)
        models_info = {
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
            'Baggage': {
                'model': Baggage,
                'name': 'Багаж',
                'fields': ['id_baggage', 'ticket_id', 'baggage_type_id', 'weight_kg', 'baggage_tag', 'status', 'registered_at'],
                'readonly': False,
            },
        }
        
        # Получаем выбранную таблицу из GET параметра
        selected_table = request.GET.get('table', 'Flight')
        if selected_table not in models_info:
            selected_table = 'Flight'
        
        model_info = models_info[selected_table]
        model = model_info['model']
        
        # Получаем все записи выбранной таблицы
        objects = model.objects.all()
        
        # Применяем select_related для ForeignKey полей
        if selected_table == 'Flight':
            objects = objects.select_related('airplane_id', 'departure_airport_id', 'arrival_airport_id')
        elif selected_table == 'Ticket':
            objects = objects.select_related('flight_id', 'class_id', 'passenger_id', 'payment_id')
        elif selected_table == 'Payment':
            objects = objects.select_related('user_id')
        elif selected_table == 'Baggage':
            objects = objects.select_related('ticket_id', 'baggage_type_id')
        
        # Сортировка по столбцу (из GET: sort_by, order=asc/desc)
        sort_by = request.GET.get('sort_by', '').strip()
        sort_order = request.GET.get('order', 'asc').lower()
        if sort_order not in ('asc', 'desc'):
            sort_order = 'asc'
        if sort_by and sort_by in model_info['fields']:
            order_field = sort_by if sort_order == 'asc' else f'-{sort_by}'
            objects = objects.order_by(order_field)
        else:
            sort_by = ''
            sort_order = 'asc'
            objects = objects.order_by('-pk')
        
        # Пагинация: 10 записей на странице
        paginator = Paginator(objects, 10)
        page_num = request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page_num)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Диапазон страниц для отображения (макс. 10)
        num_pages = paginator.num_pages
        current = page_obj.number
        if num_pages <= 10:
            page_range_display = list(range(1, num_pages + 1))
        else:
            start = max(1, min(current - 4, num_pages - 9))
            end = min(num_pages, start + 9)
            page_range_display = list(range(start, end + 1))
        
        # Удаляем сообщения об успешном входе из панели
        storage = get_messages(request)
        for message in storage:
            if message.message == 'Вы успешно вошли в систему!':
                storage.used = False
                break
        
        context = {
            'models_info': models_info,
            'selected_table': selected_table,
            'model_info': model_info,
            'objects': page_obj.object_list,
            'page_obj': page_obj,
            'page_range_display': page_range_display,
            'fields': model_info['fields'],
            'panel_type': 'manager',
            'sort_by': sort_by,
            'sort_order': sort_order,
        }
        
        return render(request, 'admin_panel.html', context)
        
    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except Exception as e:
        messages.error(request, get_user_friendly_message(e))
        return redirect('index')


def manager_crud(request):
    """Обработка CRUD операций для панели менеджера"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        messages.error(request, 'Для доступа к панели менеджера необходимо войти в систему')
        return redirect('login')
    
    account_id = request.session['account_id']
    
    try:
        account = Account.objects.get(id_account=account_id)
        # Проверка роли менеджера
        if not account.role_id or account.role_id.role_name != 'MANAGER':
            messages.error(request, 'У вас нет доступа к панели менеджера')
            return redirect('index')
        
        table_name = request.POST.get('table_name')
        action = request.POST.get('action')  # create, update, delete
        record_id = request.POST.get('record_id')
        
        # Маппинг имен таблиц на модели (только доступные для менеджера)
        model_map = {
            'Flight': Flight,
            'Passenger': Passenger,
            'Payment': Payment,
            'Ticket': Ticket,
            'Baggage': Baggage,
        }
        
        if table_name not in model_map:
            messages.error(request, 'У вас нет доступа к этой таблице')
            return redirect('manager_panel')
        
        model = model_map[table_name]
        
        if action == 'delete':
            if not record_id:
                messages.error(request, 'ID записи не указан')
                return redirect('manager_panel')
            try:
                obj = model.objects.get(pk=record_id)
                old_data = model_instance_to_audit_dict(obj)
                rid = get_record_id_for_audit(obj)
                obj.delete()
                log_audit(table_name, rid, 'DELETE', account_id, old_data=old_data, new_data=None)
                messages.success(request, 'Запись успешно удалена')
            except model.DoesNotExist:
                messages.error(request, 'Запись не найдена')
            except Exception as e:
                messages.error(request, get_user_friendly_message(e, 'delete'))
            return redirect(f'/manager-panel/?table={table_name}')
        
        elif action in ['create', 'update']:
            # Получаем данные из POST
            data = {}
            for key, value in request.POST.items():
                if key not in ['csrfmiddlewaretoken', 'table_name', 'action', 'record_id']:
                    if value:  # Только непустые значения
                        data[key] = value
            
            # Обрабатываем ForeignKey поля
            fk_fields_map = {
                'airplane_id': Airplane,
                'departure_airport_id': Airport,
                'arrival_airport_id': Airport,
                'user_id': User,
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
                        messages.error(request, 'Связанная запись не найдена. Выберите существующее значение.')
                        return redirect(f'/manager-panel/?table={table_name}')
                elif field_name in data:
                    data[field_name] = None
            
            # Обрабатываем специальные поля
            if 'birthday' in data:
                if data['birthday']:
                    try:
                        from django.utils.dateparse import parse_date
                        data['birthday'] = parse_date(data['birthday'])
                    except:
                        data['birthday'] = None
                else:
                    data['birthday'] = None
            
            # Обрабатываем Decimal поля
            decimal_fields = ['total_cost', 'price', 'weight_kg']
            for field_name in decimal_fields:
                if field_name in data and data[field_name]:
                    try:
                        data[field_name] = Decimal(str(data[field_name]))
                    except:
                        pass
            
            # Обрабатываем datetime поля
            if 'departure_time' in data or 'arrival_time' in data or 'payment_date' in data or 'registered_at' in data:
                from django.utils.dateparse import parse_datetime
                datetime_fields = ['departure_time', 'arrival_time', 'payment_date', 'registered_at']
                for field_name in datetime_fields:
                    if field_name in data and data[field_name]:
                        try:
                            data[field_name] = parse_datetime(data[field_name])
                        except Exception:
                            pass

            # Валидация перед созданием/обновлением
            instance = None
            if action == 'update' and record_id:
                try:
                    instance = model.objects.get(pk=record_id)
                except model.DoesNotExist:
                    pass
            validation_errors = _validate_crud_data(model, data, action, instance=instance)
            if validation_errors:
                for err in validation_errors:
                    messages.error(request, err)
                return redirect(f'/manager-panel/?table={table_name}')

            if action == 'create':
                # Создаем новую запись
                try:
                    obj = model.objects.create(**data)
                    new_data = model_instance_to_audit_dict(obj)
                    rid = get_record_id_for_audit(obj)
                    log_audit(table_name, rid, 'INSERT', account_id, old_data=None, new_data=new_data)
                    messages.success(request, 'Запись успешно создана')
                except Exception as e:
                    messages.error(request, get_user_friendly_message(e, 'create'))
            elif action == 'update':
                # Обновляем существующую запись
                if not record_id:
                    messages.error(request, 'ID записи не указан')
                    return redirect(f'/manager-panel/?table={table_name}')
                try:
                    obj = model.objects.get(pk=record_id)
                    old_data = model_instance_to_audit_dict(obj)
                    for key, value in data.items():
                        setattr(obj, key, value)
                    obj.save()
                    new_data = model_instance_to_audit_dict(obj)
                    rid = get_record_id_for_audit(obj)
                    log_audit(table_name, rid, 'UPDATE', account_id, old_data=old_data, new_data=new_data)
                    messages.success(request, 'Запись успешно обновлена')
                except model.DoesNotExist:
                    messages.error(request, 'Запись не найдена')
                except Exception as e:
                    messages.error(request, get_user_friendly_message(e, 'update'))
            
            return redirect(f'/manager-panel/?table={table_name}')
        
        return redirect('manager_panel')
        
    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except Exception as e:
        messages.error(request, get_user_friendly_message(e))
        return redirect('index')


def manager_get_record(request):
    """Получение данных записи для редактирования (для менеджера)"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        return JsonResponse({'error': 'Не авторизован'}, status=401)
    
    account_id = request.session['account_id']
    
    try:
        account = Account.objects.get(id_account=account_id)
        if not account.role_id or account.role_id.role_name != 'MANAGER':
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        
        table_name = request.GET.get('table')
        record_id = request.GET.get('id')
        
        # Маппинг имен таблиц на модели (только доступные для менеджера)
        model_map = {
            'Flight': Flight,
            'Passenger': Passenger,
            'Payment': Payment,
            'Ticket': Ticket,
            'Baggage': Baggage,
        }
        
        if table_name not in model_map:
            return JsonResponse({'error': 'У вас нет доступа к этой таблице'}, status=403)
        
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
        return JsonResponse({'error': get_user_friendly_message(e, 'load')}, status=500)


def manager_get_options(request):
    """Получение опций для select полей (для менеджера)"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        return JsonResponse({'error': 'Не авторизован'}, status=401)
    
    account_id = request.session['account_id']
    
    try:
        account = Account.objects.get(id_account=account_id)
        if not account.role_id or account.role_id.role_name != 'MANAGER':
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        
        model_name = request.GET.get('model')
        
        # Маппинг для опций (включая связанные модели)
        model_map = {
            'Airplane': (Airplane, 'id_airplane', 'model'),
            'Airport': (Airport, 'id_airport', 'name'),
            'User': (User, 'id_user', lambda x: f"{x.first_name} {x.last_name}"),
            'Class': (Class, 'id_class', 'class_name'),
            'Passenger': (Passenger, 'id_passenger', lambda x: f"{x.first_name} {x.last_name}"),
            'Flight': (Flight, 'id_flight', lambda x: f"GQ{x.id_flight:03d}"),
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
        return JsonResponse({'error': get_user_friendly_message(e, 'load')}, status=500)
