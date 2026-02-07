from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import csv
import json
import logging
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)
from .models import User, Account, Role, Payment, Ticket, Flight, Passenger, Airport, Class, BaggageType, Baggage, Airplane, AuditLog
from .admin_views import (
    admin_panel, admin_crud, admin_get_record, admin_get_options,
    manager_panel, manager_crud, manager_get_record, manager_get_options
)
from .exceptions_utils import get_user_friendly_message
from . import db_reports
from .forms import ProfileForm
from decimal import Decimal


def index(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


def contacts(request):
    return render(request, 'contacts.html')


def privacy(request):
    """Страница политики обработки персональных данных."""
    return render(request, 'privacy.html')


def flights(request):
    """Отображение страницы рейсов с данными из базы"""
    from django.utils import timezone
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, Page
    from django.http import JsonResponse
    from django.template.loader import render_to_string

    # Получаем все рейсы с связанными данными
    flights_list = Flight.objects.select_related(
        'departure_airport_id', 'arrival_airport_id', 'airplane_id'
    ).order_by('departure_time')

    # Фильтрация по параметрам запроса
    departure_city = request.GET.get('departure', '')
    arrival_city = request.GET.get('arrival', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    flight_number = request.GET.get('flight_number', '')

    if departure_city:
        flights_list = flights_list.filter(
            departure_airport_id__city__icontains=departure_city
        )

    if arrival_city:
        flights_list = flights_list.filter(
            arrival_airport_id__city__icontains=arrival_city
        )

    if status_filter:
        # Преобразуем статус из формы в статус модели
        status_map = {
            'scheduled': 'SCHEDULED',
            'delayed': 'DELAYED',
            'departed': 'COMPLETED',  # В модели нет DEPARTED, используем COMPLETED
            'arrived': 'COMPLETED',
            'cancelled': 'CANCELLED'
        }
        if status_filter in status_map:
            flights_list = flights_list.filter(
                status=status_map[status_filter])

    if date_filter:
        try:
            filter_date = timezone.datetime.strptime(
                date_filter, '%Y-%m-%d').date()
            flights_list = flights_list.filter(
                departure_time__date=filter_date)
        except ValueError:
            pass  # Игнорируем неверный формат даты

    # Получаем уникальные города для фильтров
    departure_cities = Airport.objects.values_list(
        'city', flat=True).distinct().order_by('city')
    arrival_cities = Airport.objects.values_list(
        'city', flat=True).distinct().order_by('city')

    # Пагинация: 10 элементов на страницу (по queryset)
    paginator = Paginator(flights_list, 10)
    page = request.GET.get('page', 1)

    try:
        flights_page = paginator.page(page)
    except PageNotAnInteger:
        flights_page = paginator.page(1)
    except EmptyPage:
        flights_page = paginator.page(paginator.num_pages)

    # Данные из процедур БД (выручка, загрузка) только для рейсов на текущей странице
    flight_ids = [f.id_flight for f in flights_page.object_list]
    revenue_occupancy = db_reports.get_revenue_occupancy_for_flights(flight_ids)

    flights_with_numbers = []
    for flight in flights_page.object_list:
        rev_occ = revenue_occupancy.get(flight.id_flight, (Decimal('0'), Decimal('0')))
        flight_number_display = f"GQ{flight.id_flight:03d}"
        flights_with_numbers.append({
            'flight': flight,
            'flight_number': flight_number_display,
            'departure_airport': flight.departure_airport_id,
            'arrival_airport': flight.arrival_airport_id,
            'airplane': flight.airplane_id,
            'revenue': rev_occ[0],
            'occupancy': rev_occ[1],
        })

    # Страница с готовыми данными для таблицы (итерация по ней даёт item с .flight, .revenue и т.д.)
    flights_page = Page(flights_with_numbers, flights_page.number, paginator)

    context = {
        'flights': flights_page,
        'departure_cities': departure_cities,
        'arrival_cities': arrival_cities,
        'current_filters': {
            'departure': departure_city,
            'arrival': arrival_city,
            'status': status_filter,
            'date': date_filter,
            'flight_number': flight_number,
        }
    }

    # Если это AJAX запрос, возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Рендерим таблицу и пагинацию в HTML
        table_html = render_to_string(
            'flights_table.html', {'flights': flights_page}, request=request)
        pagination_html = render_to_string('flights_pagination.html', {
            'flights': flights_page,
            'current_filters': context['current_filters']
        }, request=request)

        return JsonResponse({
            'table_html': table_html,
            'pagination_html': pagination_html,
            'page': flights_page.number,
            'total_pages': paginator.num_pages
        })

    return render(request, 'flights.html', context)


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Проверка заполненности полей
        if not email or not password:
            messages.error(request, 'Пожалуйста, заполните все поля')
            return render(request, 'login.html')

        try:
            # Получаем аккаунт по email
            account = Account.objects.get(email=email)

            # Проверяем пароль с использованием хэширования
            if check_password(password, account.password):
                # Сохраняем ID аккаунта в сессии для отслеживания входа пользователя
                request.session['account_id'] = account.id_account
                request.session['user_email'] = account.email
                # Проверяем, является ли пользователь администратором
                if account.role_id and account.role_id.role_name == 'ADMIN':
                    request.session['is_admin'] = True
                else:
                    request.session['is_admin'] = False
                messages.success(request, 'Вы успешно вошли в систему!')
                return redirect('index')
            else:
                messages.error(request, 'Неверный email или пароль')
        except Account.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден')
        except Exception as e:
            messages.error(request, get_user_friendly_message(e, 'login'))

    return render(request, 'login.html')


def register_view(request):
    # Контекст для сохранения значений полей при ошибках
    context = {
        'first_name': '',
        'last_name': '',
        'patronymic': '',
        'email': '',
    }

    if request.method == 'POST':
        # Получаем данные из формы
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        patronymic = request.POST.get('patronymic', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Сохраняем значения полей в контексте для отображения в форме
        context['first_name'] = first_name
        context['last_name'] = last_name
        context['patronymic'] = patronymic
        context['email'] = email

        # Валидация обязательных полей
        if not first_name or not last_name or not email or not password:
            messages.error(
                request, 'Пожалуйста, заполните все обязательные поля')
            return render(request, 'register.html', context)

        # Проверка минимальной длины пароля
        if len(password) < 6:
            messages.error(
                request, 'Пароль должен содержать минимум 6 символов')
            return render(request, 'register.html', context)

        # Проверка совпадения паролей
        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'register.html', context)

        # Проверка уникальности email
        if Account.objects.filter(email=email).exists():
            messages.error(
                request, 'Пользователь с таким email уже существует')
            return render(request, 'register.html', context)

        try:
            # Получаем или создаем роль USER
            role, created = Role.objects.get_or_create(
                role_name='USER'
            )

            # Хэшируем пароль перед сохранением
            hashed_password = make_password(password)

            # Создаем аккаунт с хэшированным паролем
            account = Account.objects.create(
                email=email,
                password=hashed_password,
                role_id=role
            )

            # Создаем пользователя (остальные поля необязательны)
            user = User.objects.create(
                account_id=account,
                first_name=first_name,
                last_name=last_name,
                patronymic=patronymic if patronymic else None,
                phone=None,  # Необязательное поле
                passport_number=None,  # Необязательное поле
                birthday=None  # Необязательное поле
            )

            messages.success(
                request, 'Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect('login')

        except Role.DoesNotExist:
            messages.error(request, 'Ошибка: роль USER не найдена в системе')
            return render(request, 'register.html', context)
        except Exception as e:
            messages.error(request, get_user_friendly_message(e, 'register'))
            return render(request, 'register.html', context)

    return render(request, 'register.html', context)


def logout_view(request):
    """Выход из аккаунта"""
    if 'account_id' in request.session:
        del request.session['account_id']
        del request.session['user_email']
        if 'is_admin' in request.session:
            del request.session['is_admin']
        messages.success(request, 'Вы успешно вышли из системы')
    return redirect('index')


def profile_view(request):
    """Просмотр и редактирование профиля пользователя"""
    # Проверяем, авторизован ли пользователь
    if 'account_id' not in request.session:
        messages.error(
            request, 'Для доступа к профилю необходимо войти в систему')
        return redirect('login')

    account_id = request.session['account_id']

    try:
        account = Account.objects.get(id_account=account_id)
        try:
            user = User.objects.get(account_id=account)
        except User.DoesNotExist:
            # Если пользователь не существует, создаем его с базовыми данными
            user = User.objects.create(
                account_id=account,
                first_name='',
                last_name='',
                patronymic=None,
                phone=None,
                passport_number=None,
                birthday=None
            )

        if request.method == 'POST':
            form = ProfileForm(request.POST)
            if not form.is_valid():
                # Собираем контекст для повторного отображения формы с ошибками
                cd = form.cleaned_data
                err_ctx = {
                    'user': user,
                    'account': account,
                    'profile_form': form,
                    'email': request.POST.get('email', '').strip() or account.email,
                    'first_name': request.POST.get('first_name', '').strip() or (user.first_name or ''),
                    'last_name': request.POST.get('last_name', '').strip() or (user.last_name or ''),
                    'patronymic': request.POST.get('patronymic', '').strip() or (user.patronymic or ''),
                    'phone': request.POST.get('phone', '').strip() or (user.phone or ''),
                    'passport_number': request.POST.get('passport_number', '').strip() or (user.passport_number or ''),
                    'birthday': request.POST.get('birthday', '').strip() or (user.birthday.strftime('%d.%m.%Y') if user.birthday else ''),
                    'is_admin': False,
                    'is_manager': False,
                    'tickets': [],
                    'total_tickets': 0,
                    'user_payments_30d': Decimal('0'),
                }
                return render(request, 'profile.html', err_ctx)

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            patronymic = form.cleaned_data.get('patronymic') or None
            phone = form.cleaned_data.get('phone') or None
            passport_number = form.cleaned_data.get('passport_number') or None
            birthday_str = form.cleaned_data.get('birthday') or ''
            email = form.cleaned_data['email']

            user.first_name = first_name
            user.last_name = last_name
            user.patronymic = patronymic
            user.phone = phone
            user.passport_number = passport_number
            if birthday_str:
                try:
                    parts = birthday_str.split('.')
                    user.birthday = parse_date(f"{parts[2]}-{parts[1]}-{parts[0]}")
                except (ValueError, TypeError, IndexError):
                    user.birthday = None
            else:
                user.birthday = None

            try:
                user.save()
            except Exception as e:
                messages.error(request, get_user_friendly_message(e, 'save'))
                err_ctx = {
                    'user': user,
                    'account': account,
                    'profile_form': form,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'patronymic': patronymic or '',
                    'phone': phone or '',
                    'passport_number': passport_number or '',
                    'birthday': birthday_str,
                    'is_admin': False,
                    'is_manager': False,
                    'tickets': [],
                    'total_tickets': 0,
                    'user_payments_30d': Decimal('0'),
                }
                return render(request, 'profile.html', err_ctx)

            if email and email != account.email:
                if Account.objects.filter(email=email).exclude(id_account=account_id).exists():
                    messages.error(request, 'Пользователь с таким email уже существует')
                    err_ctx = {
                        'user': user,
                        'account': account,
                        'profile_form': form,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'patronymic': patronymic or '',
                        'phone': phone or '',
                        'passport_number': passport_number or '',
                        'birthday': birthday_str,
                        'is_admin': False,
                        'is_manager': False,
                        'tickets': [],
                        'total_tickets': 0,
                        'user_payments_30d': Decimal('0'),
                    }
                    return render(request, 'profile.html', err_ctx)
                account.email = email
                account.save()
                request.session['user_email'] = email
                messages.success(request, 'Email успешно обновлен')

            messages.success(request, 'Профиль успешно обновлен')
            return redirect('profile')

        # Проверяем роль пользователя (безопасно при отсутствии или удалённой роли)
        try:
            role_name = account.role_id.role_name if getattr(account, 'role_id', None) else None
        except Exception:
            role_name = None
        is_admin = role_name == 'ADMIN'
        is_manager = role_name == 'MANAGER'

        if is_admin:
            # Статистика для администратора
            from django.db.models import Count, Sum, Avg

            # Статистика по пользователям
            total_users = User.objects.count()
            total_accounts = Account.objects.count()
            users_with_tickets = User.objects.filter(
                id_user__in=Payment.objects.values_list(
                    'user_id', flat=True).distinct()
            ).count()

            # Статистика по самолетам
            total_airplanes = Airplane.objects.count()
            total_capacity = Airplane.objects.aggregate(
                Sum('capacity'))['capacity__sum'] or 0

            # Статистика по рейсам
            total_flights = Flight.objects.count()
            scheduled_flights = Flight.objects.filter(
                status='SCHEDULED').count()
            completed_flights = Flight.objects.filter(
                status='COMPLETED').count()
            cancelled_flights = Flight.objects.filter(
                status='CANCELLED').count()

            # Статистика по билетам
            total_tickets = Ticket.objects.count()
            paid_tickets = Ticket.objects.filter(status='PAID').count()
            booked_tickets = Ticket.objects.filter(status='BOOKED').count()

            # Статистика по платежам
            total_payments = Payment.objects.count()
            total_revenue = Payment.objects.aggregate(
                Sum('total_cost'))['total_cost__sum'] or Decimal('0.00')
            completed_payments = Payment.objects.filter(
                status='COMPLETED').count()

            # Статистика по аэропортам
            total_airports = Airport.objects.count()

            # Статистика за последние 30 дней
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_tickets = Ticket.objects.filter(
                payment_id__payment_date__gte=thirty_days_ago
            ).count()
            recent_revenue = Payment.objects.filter(
                payment_date__gte=thirty_days_ago,
                status='COMPLETED'
            ).aggregate(Sum('total_cost'))['total_cost__sum'] or Decimal('0.00')

            # Популярные направления
            popular_routes = Flight.objects.values(
                'departure_airport_id__city',
                'arrival_airport_id__city'
            ).annotate(
                ticket_count=Count('ticket')
            ).order_by('-ticket_count')[:5]

            # Данные для вкладки «Отчётность»
            flights_report = db_reports.get_flights_report(limit=100)
            airports_report = db_reports.get_airports_revenue_report()
            audit_report = db_reports.get_audit_operations_report()

            context = {
                'user': user,
                'account': account,
                'profile_form': None,
                'email': account.email,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'patronymic': user.patronymic or '',
                'phone': user.phone or '',
                'passport_number': user.passport_number or '',
                'birthday': user.birthday.strftime('%d.%m.%Y') if user.birthday else '',
                'is_admin': True,
                # Статистика
                'total_users': total_users,
                'total_accounts': total_accounts,
                'users_with_tickets': users_with_tickets,
                'total_airplanes': total_airplanes,
                'total_capacity': total_capacity,
                'total_flights': total_flights,
                'scheduled_flights': scheduled_flights,
                'completed_flights': completed_flights,
                'cancelled_flights': cancelled_flights,
                'total_tickets': total_tickets,
                'paid_tickets': paid_tickets,
                'booked_tickets': booked_tickets,
                'total_payments': total_payments,
                'total_revenue': total_revenue,
                'completed_payments': completed_payments,
                'total_airports': total_airports,
                'recent_tickets': recent_tickets,
                'recent_revenue': recent_revenue,
                'popular_routes': popular_routes,
                # Отчётность
                'flights_report': flights_report,
                'airports_report': airports_report,
                'audit_report': audit_report,
                'show_audit': True,
            }
        elif is_manager:
            # Статистика для менеджера
            from django.db.models import Count, Sum
            from django.db.models.functions import TruncMonth

            # Статистика по статусам билетов для круговой диаграммы
            ticket_statuses = Ticket.objects.values('status').annotate(
                count=Count('id_ticket')
            ).order_by('status')

            # Подготовка данных для круговой диаграммы
            ticket_status_data = {
                'labels': [],
                'data': [],
                'colors': []
            }
            status_colors = {
                'BOOKED': '#3498db',
                'PAID': '#2ecc71',
                'CHECKED_IN': '#9b59b6',
                'CANCELLED': '#e74c3c'
            }
            status_labels = {
                'BOOKED': 'Забронирован',
                'PAID': 'Оплачен',
                'CHECKED_IN': 'Зарегистрирован',
                'CANCELLED': 'Отменен'
            }

            for status_info in ticket_statuses:
                status = status_info['status']
                ticket_status_data['labels'].append(
                    status_labels.get(status, status))
                ticket_status_data['data'].append(status_info['count'])
                ticket_status_data['colors'].append(
                    status_colors.get(status, '#95a5a6'))

            # Статистика выручки по месяцам для bar диаграммы
            # Получаем данные за последние 12 месяцев
            twelve_months_ago = timezone.now() - timedelta(days=365)
            monthly_revenue = Payment.objects.filter(
                payment_date__gte=twelve_months_ago,
                status='COMPLETED'
            ).annotate(
                month=TruncMonth('payment_date')
            ).values('month').annotate(
                total=Sum('total_cost')
            ).order_by('month')

            # Подготовка данных для bar диаграммы
            revenue_data = {
                'labels': [],
                'data': []
            }

            # Создаем словарь для всех месяцев
            months_dict = {}
            for revenue_info in monthly_revenue:
                if revenue_info['month']:
                    month_key = revenue_info['month'].strftime('%Y-%m')
                    months_dict[month_key] = float(revenue_info['total'] or 0)

            # Заполняем данные за последние 12 месяцев
            current_date = timezone.now()
            for i in range(11, -1, -1):
                month_date = current_date - timedelta(days=30*i)
                month_key = month_date.strftime('%Y-%m')
                month_label = month_date.strftime('%B %Y')
                # Преобразуем название месяца на русский
                month_names = {
                    'January': 'Январь', 'February': 'Февраль', 'March': 'Март',
                    'April': 'Апрель', 'May': 'Май', 'June': 'Июнь',
                    'July': 'Июль', 'August': 'Август', 'September': 'Сентябрь',
                    'October': 'Октябрь', 'November': 'Ноябрь', 'December': 'Декабрь'
                }
                for eng, rus in month_names.items():
                    month_label = month_label.replace(eng, rus)

                revenue_data['labels'].append(month_label)
                revenue_data['data'].append(months_dict.get(month_key, 0))

            # Подсчитываем общее количество билетов для боковой панели
            total_tickets_count = Ticket.objects.count()

            # Данные для вкладки «Отчётность»
            flights_report = db_reports.get_flights_report(limit=100)
            airports_report = db_reports.get_airports_revenue_report()
            audit_report = []

            context = {
                'user': user,
                'account': account,
                'profile_form': None,
                'email': account.email,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'patronymic': user.patronymic or '',
                'phone': user.phone or '',
                'passport_number': user.passport_number or '',
                'birthday': user.birthday.strftime('%d.%m.%Y') if user.birthday else '',
                'is_manager': True,
                'total_tickets': total_tickets_count,
                'ticket_status_data': json.dumps(ticket_status_data, ensure_ascii=False),
                'revenue_data': json.dumps(revenue_data, ensure_ascii=False),
                # Отчётность
                'flights_report': flights_report,
                'airports_report': airports_report,
                'audit_report': audit_report,
                'show_audit': False,
            }
        else:
            # История покупок для обычных пользователей + сумма платежей за период (процедура БД)
            payments = Payment.objects.filter(
                user_id=user).order_by('-payment_date')

            tickets = []
            for payment in payments:
                payment_tickets = Ticket.objects.filter(payment_id=payment).select_related(
                    'flight_id', 'flight_id__departure_airport_id',
                    'flight_id__arrival_airport_id', 'class_id', 'passenger_id'
                )
                for ticket in payment_tickets:
                    tickets.append({
                        'ticket': ticket,
                        'payment': payment,
                        'flight': ticket.flight_id,
                        'class_name': ticket.class_id.class_name,
                        'passenger': ticket.passenger_id,
                    })

            tickets.sort(key=lambda x: x['payment'].payment_date, reverse=True)

            date_to = timezone.now()
            date_from_30 = date_to - timedelta(days=30)
            try:
                user_payments_30d = db_reports.get_user_payments_in_period(
                    user.id_user, date_from_30, date_to
                )
            except Exception:
                user_payments_30d = Decimal('0')

            context = {
                'user': user,
                'account': account,
                'profile_form': None,
                'email': account.email,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'patronymic': user.patronymic or '',
                'phone': user.phone or '',
                'passport_number': user.passport_number or '',
                'birthday': user.birthday.strftime('%d.%m.%Y') if user.birthday else '',
                'is_admin': False,
                'is_manager': False,
                'tickets': tickets,
                'total_tickets': len(tickets),
                'user_payments_30d': user_payments_30d,
            }

        return render(request, 'profile.html', context)

    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except Exception as e:
        logger.exception('Ошибка при открытии профиля: %s', e)
        messages.error(request, get_user_friendly_message(e, 'load'))
        return redirect('index')


def reports_view(request):
    """Перенаправление на профиль с открытой вкладкой «Отчётность»."""
    if 'account_id' not in request.session:
        messages.error(request, 'Для доступа необходимо войти в систему')
        return redirect('login')
    from urllib.parse import urlencode
    return redirect('profile' + '?' + urlencode({'tab': 'reports'}))


def export_statistics(request, format_type):
    """Экспорт статистики для менеджера в CSV или PDF"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        messages.error(request, 'Для доступа необходимо войти в систему')
        return redirect('login')

    account_id = request.session['account_id']

    try:
        account = Account.objects.get(id_account=account_id)
        # Проверка роли менеджера
        if not account.role_id or account.role_id.role_name != 'MANAGER':
            messages.error(request, 'У вас нет доступа к этой функции')
            return redirect('profile')

        # Импортируем необходимые функции для статистики
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncMonth
        from django.utils import timezone
        from datetime import timedelta

        # Получаем данные для экспорта
        ticket_statuses = Ticket.objects.values('status').annotate(
            count=Count('id_ticket')
        ).order_by('status')

        twelve_months_ago = timezone.now() - timedelta(days=365)
        monthly_revenue = Payment.objects.filter(
            payment_date__gte=twelve_months_ago,
            status='COMPLETED'
        ).annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('total_cost')
        ).order_by('month')

        status_labels = {
            'BOOKED': 'Забронирован',
            'PAID': 'Оплачен',
            'CHECKED_IN': 'Зарегистрирован',
            'CANCELLED': 'Отменен'
        }

        if format_type == 'csv':
            # Экспорт в CSV
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="statistics.csv"'

            # Добавляем BOM для правильного отображения кириллицы в Excel
            response.write('\ufeff')

            writer = csv.writer(response)

            # Записываем статистику по статусам билетов
            writer.writerow(['Статистика по статусам билетов'])
            writer.writerow(['Статус', 'Количество'])
            for status_info in ticket_statuses:
                status = status_info['status']
                label = status_labels.get(status, status)
                writer.writerow([label, status_info['count']])

            writer.writerow([])

            # Записываем выручку по месяцам
            writer.writerow(['Выручка по месяцам'])
            writer.writerow(['Месяц', 'Выручка (руб.)'])
            for revenue_info in monthly_revenue:
                month_str = revenue_info['month'].strftime('%B %Y')
                # Преобразуем название месяца на русский
                month_names = {
                    'January': 'Январь', 'February': 'Февраль', 'March': 'Март',
                    'April': 'Апрель', 'May': 'Май', 'June': 'Июнь',
                    'July': 'Июль', 'August': 'Август', 'September': 'Сентябрь',
                    'October': 'Октябрь', 'November': 'Ноябрь', 'December': 'Декабрь'
                }
                for eng, rus in month_names.items():
                    month_str = month_str.replace(eng, rus)
                writer.writerow([month_str, float(revenue_info['total'] or 0)])

            return response

        elif format_type == 'pdf':
            # Экспорт в PDF (HTML формат для печати в PDF)
            from django.template.loader import render_to_string

            # Вычисляем общую выручку
            total_revenue = sum(float(r['total'] or 0)
                                for r in monthly_revenue)

            html_content = render_to_string('statistics_export.html', {
                'ticket_statuses': ticket_statuses,
                'monthly_revenue': monthly_revenue,
                'status_labels': status_labels,
                'export_date': timezone.now(),
                'total_revenue': total_revenue,
            })

            # Возвращаем HTML, который можно сохранить как PDF через браузер
            response = HttpResponse(content_type='text/html; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="statistics.html"'
            response.write(html_content.encode('utf-8'))
            return response

        else:
            messages.error(request, 'Неподдерживаемый формат экспорта')
            return redirect('profile')

    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except Exception as e:
        messages.error(request, get_user_friendly_message(e, 'export'))
        return redirect('profile')


def backup_database(request):
    """Создание резервной копии БД (только для администратора)"""
    if 'account_id' not in request.session:
        messages.error(request, 'Для доступа необходимо войти в систему')
        return redirect('login')

    try:
        account = Account.objects.get(id_account=request.session['account_id'])
        if not account.role_id or account.role_id.role_name != 'ADMIN':
            messages.error(request, 'Доступ только для администратора')
            return redirect('profile')

        db = settings.DATABASES['default']
        dbname = db['NAME']
        user = db['USER']
        password = db.get('PASSWORD', '')
        host = db.get('HOST', 'localhost')
        port = db.get('PORT', '5432')

        env = os.environ.copy()
        if password:
            env['PGPASSWORD'] = str(password)
        env['PGCLIENTENCODING'] = 'UTF8'

        pg_bin = getattr(settings, 'PG_BIN_PATH', '') or ''
        pg_dump_cmd = os.path.join(pg_bin, 'pg_dump.exe' if os.name == 'nt' else 'pg_dump') if pg_bin else 'pg_dump'

        result = subprocess.run(
            [pg_dump_cmd, '-U', user, '-h', host, '-p', str(port), '-F', 'p',
             '--clean', '--if-exists', '--no-owner', '--no-acl', dbname],
            env=env,
            capture_output=True,
            timeout=120,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) if os.name == 'nt' else 0,
        )

        if result.returncode != 0:
            err = (result.stderr or result.stdout or b'')
            raise Exception(err.decode('utf-8', errors='replace'))

        content = result.stdout or b''
        filename = f'greenquality_backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.sql'
        response = HttpResponse(content, content_type='application/sql; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except subprocess.TimeoutExpired:
        messages.error(request, 'Превышено время ожидания при создании резервной копии')
        return redirect('profile')
    except FileNotFoundError:
        messages.error(
            request,
            'pg_dump не найден. Добавьте PG_BIN_PATH в .env (например: PG_BIN_PATH=C:\\Program Files\\PostgreSQL\\18\\bin)'
        )
        return redirect('profile')
    except Exception as e:
        messages.error(request, f'Ошибка создания резервной копии: {str(e)}')
        return redirect('profile')


def restore_database(request):
    """Восстановление БД из резервной копии (только для администратора)"""
    if 'account_id' not in request.session:
        messages.error(request, 'Для доступа необходимо войти в систему')
        return redirect('login')

    if request.method != 'POST':
        return redirect('profile')

    try:
        account = Account.objects.get(id_account=request.session['account_id'])
        if not account.role_id or account.role_id.role_name != 'ADMIN':
            messages.error(request, 'Доступ только для администратора')
            return redirect('profile')

        backup_file = request.FILES.get('backup_file')
        if not backup_file:
            messages.error(request, 'Выберите файл резервной копии (.sql)')
            return redirect('profile')

        if not backup_file.name.endswith('.sql'):
            messages.error(request, 'Файл должен иметь расширение .sql')
            return redirect('profile')

        db = settings.DATABASES['default']
        dbname = db['NAME']
        user = db['USER']
        password = db.get('PASSWORD', '')
        host = db.get('HOST', 'localhost')
        port = db.get('PORT', '5432')

        env = os.environ.copy()
        if password:
            env['PGPASSWORD'] = str(password)
        env['PGCLIENTENCODING'] = 'UTF8'

        pg_bin = getattr(settings, 'PG_BIN_PATH', '') or ''
        psql_cmd = os.path.join(pg_bin, 'psql.exe' if os.name == 'nt' else 'psql') if pg_bin else 'psql'

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.sql', delete=False) as tmp:
            for chunk in backup_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            from django.db import connection
            connection.close()

            result = subprocess.run(
                [psql_cmd, '-U', user, '-h', host, '-p', str(port), '-d', dbname,
                 '-f', tmp_path, '-v', 'ON_ERROR_STOP=1'],
                env=env,
                capture_output=True,
                timeout=300,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) if os.name == 'nt' else 0,
            )

            if result.returncode != 0:
                err_raw = result.stderr or result.stdout or b''
                err_msg = err_raw.decode('utf-8', errors='replace')[:500]
                raise Exception(err_msg)

            messages.success(request, 'База данных успешно восстановлена')
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except subprocess.TimeoutExpired:
        messages.error(request, 'Превышено время ожидания при восстановлении')
        return redirect('profile')
    except FileNotFoundError:
        messages.error(
            request,
            'psql не найден. Добавьте PG_BIN_PATH в .env (например: PG_BIN_PATH=C:\\Program Files\\PostgreSQL\\18\\bin)'
        )
        return redirect('profile')
    except Exception as e:
        messages.error(request, f'Ошибка восстановления: {str(e)}')
        return redirect('profile')

    return redirect('profile')


def buy_ticket(request, flight_id):
    """Процесс покупки билета - шаг 1: выбор параметров"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        messages.error(
            request, 'Для покупки билета необходимо войти в систему')
        return redirect('login')

    account_id = request.session['account_id']

    try:
        # Получаем рейс
        flight = Flight.objects.select_related(
            'airplane_id', 'departure_airport_id', 'arrival_airport_id'
        ).get(id_flight=flight_id)

        # Получаем пользователя
        account = Account.objects.get(id_account=account_id)
        try:
            user = User.objects.get(account_id=account)
        except User.DoesNotExist:
            messages.error(request, 'Профиль пользователя не найден')
            return redirect('profile')

        # Проверяем заполненность паспортных данных
        if not user.passport_number:
            messages.error(
                request, 'Для покупки билета необходимо заполнить паспортные данные в профиле')
            return redirect('profile')

        # Получаем доступные классы и типы багажа
        classes = Class.objects.all()
        baggage_types = BaggageType.objects.all()

        if request.method == 'POST':
            # Получаем выбранные параметры
            class_id = request.POST.get('class_id')
            baggage_type_id = request.POST.get('baggage_type_id')

            if not class_id:
                messages.error(request, 'Выберите класс обслуживания')
            else:
                # Сохраняем выбранные параметры в сессии для следующего шага
                request.session['booking_class_id'] = int(class_id)
                if baggage_type_id:
                    request.session['booking_baggage_type_id'] = int(
                        baggage_type_id)
                else:
                    request.session['booking_baggage_type_id'] = None
                request.session['booking_flight_id'] = flight_id

                # Переходим к выбору места
                return redirect('buy_ticket_seat', flight_id=flight_id)

        context = {
            'flight': flight,
            'classes': classes,
            'baggage_types': baggage_types,
            'user': user,
        }

        return render(request, 'buy_ticket_step1.html', context)

    except Flight.DoesNotExist:
        messages.error(request, 'Рейс не найден')
        return redirect('flights')
    except Exception as e:
        messages.error(request, get_user_friendly_message(e))
        return redirect('flights')


def buy_ticket_seat(request, flight_id):
    """Процесс покупки билета - шаг 2: выбор места"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        messages.error(
            request, 'Для покупки билета необходимо войти в систему')
        return redirect('login')

    # Проверяем, что параметры выбраны
    if 'booking_class_id' not in request.session or request.session.get('booking_flight_id') != flight_id:
        messages.error(request, 'Пожалуйста, начните процесс покупки с начала')
        return redirect('buy_ticket', flight_id=flight_id)

    try:
        # Получаем рейс и самолет
        flight = Flight.objects.select_related(
            'airplane_id').get(id_flight=flight_id)
        airplane = flight.airplane_id

        # Получаем занятые места для этого рейса
        booked_seats = set(
            Ticket.objects.filter(
                flight_id=flight,
                status__in=['BOOKED', 'PAID', 'CHECKED_IN']
            ).values_list('seat_number', flat=True)
        )

        # Генерируем карту мест
        rows = airplane.rows or 30  # По умолчанию 30 рядов
        seats_per_row = airplane.seats_row or 6  # По умолчанию 6 мест в ряду

        # Определяем расположение мест (например, A-B-C D-E-F для 6 мест)
        seat_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        if seats_per_row <= 6:
            seat_letters = ['A', 'B', 'C', 'D', 'E', 'F'][:seats_per_row]
        elif seats_per_row <= 8:
            seat_letters = ['A', 'B', 'C', 'D',
                            'E', 'F', 'G', 'H'][:seats_per_row]

        # Разделяем места на левую и правую стороны
        left_seats = seat_letters[:len(
            seat_letters)//2] if len(seat_letters) > 3 else seat_letters[:3]
        right_seats = seat_letters[len(
            seat_letters)//2:] if len(seat_letters) > 3 else seat_letters[3:]

        seats_map = []
        for row in range(1, rows + 1):
            left_row_seats = []
            right_row_seats = []

            # Левая сторона
            for seat_letter in left_seats:
                seat_number = f"{row}{seat_letter}"
                is_booked = seat_number in booked_seats
                left_row_seats.append({
                    'number': seat_number,
                    'booked': is_booked,
                })

            # Правая сторона
            for seat_letter in right_seats:
                seat_number = f"{row}{seat_letter}"
                is_booked = seat_number in booked_seats
                right_row_seats.append({
                    'number': seat_number,
                    'booked': is_booked,
                })

            seats_map.append({
                'row': row,
                'left_seats': left_row_seats,
                'right_seats': right_row_seats,
            })

        if request.method == 'POST':
            seat_number = request.POST.get('seat_number')

            if not seat_number:
                messages.error(request, 'Выберите место')
            elif seat_number in booked_seats:
                messages.error(request, 'Это место уже занято')
            else:
                # Сохраняем выбранное место в сессии
                request.session['booking_seat_number'] = seat_number

                # Переходим к подтверждению
                return redirect('buy_ticket_confirm', flight_id=flight_id)

        context = {
            'flight': flight,
            'airplane': airplane,
            'seats_map': seats_map,
            'rows': rows,
            'seats_per_row': seats_per_row,
            'booked_seats': booked_seats,
            'left_seat_letters': left_seats,
            'right_seat_letters': right_seats,
        }

        return render(request, 'buy_ticket_step2.html', context)

    except Flight.DoesNotExist:
        messages.error(request, 'Рейс не найден')
        return redirect('flights')
    except Exception as e:
        messages.error(request, get_user_friendly_message(e))
        return redirect('flights')


def buy_ticket_confirm(request, flight_id):
    """Процесс покупки билета - шаг 3: подтверждение и покупка"""
    # Проверка авторизации
    if 'account_id' not in request.session:
        messages.error(
            request, 'Для покупки билета необходимо войти в систему')
        return redirect('login')

    # Проверяем, что все параметры выбраны
    if ('booking_class_id' not in request.session or
        'booking_seat_number' not in request.session or
            request.session.get('booking_flight_id') != flight_id):
        messages.error(
            request, 'Пожалуйста, завершите процесс выбора параметров')
        return redirect('buy_ticket', flight_id=flight_id)

    account_id = request.session['account_id']

    try:
        # Получаем данные
        flight = Flight.objects.select_related(
            'airplane_id', 'departure_airport_id', 'arrival_airport_id'
        ).get(id_flight=flight_id)

        account = Account.objects.get(id_account=account_id)
        user = User.objects.get(account_id=account)

        class_obj = Class.objects.get(
            id_class=request.session['booking_class_id'])
        seat_number = request.session['booking_seat_number']
        baggage_type_id = request.session.get('booking_baggage_type_id')

        # Проверяем, что место все еще свободно
        if Ticket.objects.filter(flight_id=flight, seat_number=seat_number,
                                 status__in=['BOOKED', 'PAID', 'CHECKED_IN']).exists():
            messages.error(
                request, 'Это место уже занято. Пожалуйста, выберите другое место.')
            return redirect('buy_ticket_seat', flight_id=flight_id)

        # Ищем существующий свободный билет (созданный триггером при добавлении рейса)
        existing_ticket = Ticket.objects.filter(
            flight_id=flight, seat_number=seat_number, status='AVAILABLE'
        ).first()

        # Рассчитываем цену (базовая цена зависит от класса)
        base_prices = {
            'ECONOMY': Decimal('5000.00'),
            'BUSINESS': Decimal('15000.00'),
            'FIRST': Decimal('30000.00'),
        }
        base_price = base_prices.get(class_obj.class_name, Decimal('5000.00'))

        # Добавляем стоимость багажа, если выбран
        baggage_price = Decimal('0.00')
        if baggage_type_id:
            try:
                baggage_type = BaggageType.objects.get(
                    id_baggage_type=baggage_type_id)
                baggage_price = baggage_type.base_price
            except BaggageType.DoesNotExist:
                pass

        total_price = base_price + baggage_price

        if request.method == 'POST':
            # Создаем или обновляем пассажира из данных пользователя
            passenger, created = Passenger.objects.get_or_create(
                passport_number=user.passport_number,
                defaults={
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'patronymic': user.patronymic or '',
                    'birthday': user.birthday if user.birthday else '2000-01-01',
                }
            )
            # Обновляем данные пассажира, если они изменились
            if not created:
                passenger.first_name = user.first_name
                passenger.last_name = user.last_name
                passenger.patronymic = user.patronymic or ''
                if user.birthday:
                    passenger.birthday = user.birthday
                passenger.save()

            # Создаем платеж
            payment = Payment.objects.create(
                user_id=user,
                total_cost=total_price,
                payment_method='ONLINE',
                status='COMPLETED',  # Пока автоматически завершаем платеж
            )

            # Обновляем существующий билет или создаём новый (для старых рейсов без триггера)
            if existing_ticket:
                existing_ticket.class_id = class_obj
                existing_ticket.price = total_price
                existing_ticket.status = 'PAID'
                existing_ticket.passenger_id = passenger
                existing_ticket.payment_id = payment
                existing_ticket.save()
                ticket = existing_ticket
            else:
                ticket = Ticket.objects.create(
                    flight_id=flight,
                    class_id=class_obj,
                    seat_number=seat_number,
                    price=total_price,
                    status='PAID',
                    passenger_id=passenger,
                    payment_id=payment,
                )

            # Создаем багаж, если выбран
            if baggage_type_id:
                import random
                import string

                baggage_type = BaggageType.objects.get(
                    id_baggage_type=baggage_type_id)
                # Генерируем уникальный номер багажной бирки
                baggage_tag = ''.join(random.choices(
                    string.ascii_uppercase + string.digits, k=12))

                # Проверяем уникальность
                while Baggage.objects.filter(baggage_tag=baggage_tag).exists():
                    baggage_tag = ''.join(random.choices(
                        string.ascii_uppercase + string.digits, k=12))

                Baggage.objects.create(
                    ticket_id=ticket,
                    baggage_type_id=baggage_type,
                    weight_kg=Decimal('20.00'),  # По умолчанию 20 кг
                    baggage_tag=baggage_tag,
                )

            # Очищаем данные сессии
            del request.session['booking_class_id']
            del request.session['booking_seat_number']
            del request.session['booking_flight_id']
            if 'booking_baggage_type_id' in request.session:
                del request.session['booking_baggage_type_id']

            messages.success(
                request, f'Билет успешно куплен! Номер билета: {ticket.id_ticket}')
            return redirect('profile')

        context = {
            'flight': flight,
            'class_obj': class_obj,
            'seat_number': seat_number,
            'baggage_type': BaggageType.objects.get(id_baggage_type=baggage_type_id) if baggage_type_id else None,
            'base_price': base_price,
            'baggage_price': baggage_price,
            'total_price': total_price,
            'user': user,
        }

        return render(request, 'buy_ticket_step3.html', context)

    except Flight.DoesNotExist:
        messages.error(request, 'Рейс не найден')
        return redirect('flights')
    except Exception as e:
        messages.error(request, get_user_friendly_message(e))
        return redirect('flights')


def custom_page_not_found(request, exception):
    """Обработчик 404 — страница не найдена (понятное сообщение на русском)."""
    return render(request, '404.html', status=404)


def page_not_found_catchall(request, path):
    """
    Запасной маршрут для неизвестных URL.
    При DEBUG=True Django не вызывает handler404, поэтому показываем нашу 404 сами.
    """
    return render(request, '404.html', status=404)


def custom_server_error(request):
    """Обработчик 500 — внутренняя ошибка сервера (понятное сообщение на русском)."""
    return render(request, '500.html', status=500)
