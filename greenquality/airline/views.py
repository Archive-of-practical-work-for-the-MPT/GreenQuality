from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.utils.dateparse import parse_date
from django.db.models import Q
from .models import User, Account, Role, Payment, Ticket, Flight, Passenger, Airport, Class, BaggageType, Baggage, Airplane
from decimal import Decimal


def index(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


def contacts(request):
    return render(request, 'contacts.html')


def flights(request):
    """Отображение страницы рейсов с данными из базы"""
    from django.utils import timezone
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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

    # Формируем номер рейса (GQ + ID рейса)
    flights_with_numbers = []
    for flight in flights_list:
        flight_number_display = f"GQ{flight.id_flight:03d}"
        flights_with_numbers.append({
            'flight': flight,
            'flight_number': flight_number_display,
            'departure_airport': flight.departure_airport_id,
            'arrival_airport': flight.arrival_airport_id,
            'airplane': flight.airplane_id,
        })

    # Пагинация: 10 элементов на страницу
    paginator = Paginator(flights_with_numbers, 10)
    page = request.GET.get('page', 1)

    try:
        flights_page = paginator.page(page)
    except PageNotAnInteger:
        # Если page не является целым числом, показываем первую страницу
        flights_page = paginator.page(1)
    except EmptyPage:
        # Если page выходит за пределы диапазона, показываем последнюю страницу
        flights_page = paginator.page(paginator.num_pages)

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
                messages.success(request, 'Вы успешно вошли в систему!')
                return redirect('index')
            else:
                messages.error(request, 'Неверный email или пароль')
        except Account.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден')
        except Exception as e:
            messages.error(request, f'Ошибка при входе: {str(e)}')

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
            messages.error(request, f'Ошибка при регистрации: {str(e)}')
            return render(request, 'register.html', context)

    return render(request, 'register.html', context)


def logout_view(request):
    """Выход из аккаунта"""
    if 'account_id' in request.session:
        del request.session['account_id']
        del request.session['user_email']
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
            # Получаем данные из формы
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            patronymic = request.POST.get('patronymic', '').strip()
            phone = request.POST.get('phone', '').strip()
            passport_number = request.POST.get('passport_number', '').strip()
            birthday = request.POST.get('birthday', '').strip()
            email = request.POST.get('email', '').strip()

            # Обновляем данные пользователя
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.patronymic = patronymic if patronymic else None
            user.phone = phone if phone else None
            user.passport_number = passport_number if passport_number else None
            # Обрабатываем дату рождения (формат дд.мм.гггг)
            if birthday:
                try:
                    # Пробуем распарсить дату в формате дд.мм.гггг
                    if '.' in birthday:
                        day, month, year = birthday.split('.')
                        birthday = f"{year}-{month}-{day}"
                    user.birthday = parse_date(birthday)
                except (ValueError, TypeError):
                    user.birthday = None
            else:
                user.birthday = None

            # Сохраняем пользователя с обработкой ошибок
            try:
                user.save()
            except Exception as e:
                messages.error(
                    request, f'Ошибка при сохранении данных: {str(e)}')
                # Возвращаем форму с сохраненными данными при ошибке
                context = {
                    'user': user,
                    'account': account,
                    'email': email if email else account.email,
                    'first_name': first_name if first_name else (user.first_name or ''),
                    'last_name': last_name if last_name else (user.last_name or ''),
                    'patronymic': patronymic if patronymic else (user.patronymic or ''),
                    'phone': phone if phone else (user.phone or ''),
                    'passport_number': passport_number if passport_number else (user.passport_number or ''),
                    'birthday': birthday if birthday else (user.birthday.strftime('%d.%m.%Y') if user.birthday else ''),
                }
                return render(request, 'profile.html', context)

            # Обновляем email в аккаунте, если он изменился
            if email and email != account.email:
                # Проверяем, не занят ли новый email
                if Account.objects.filter(email=email).exclude(id_account=account_id).exists():
                    messages.error(
                        request, 'Пользователь с таким email уже существует')
                    # Возвращаем форму с сохраненными данными при ошибке
                    context = {
                        'user': user,
                        'account': account,
                        'email': email,
                        'first_name': first_name if first_name else (user.first_name or ''),
                        'last_name': last_name if last_name else (user.last_name or ''),
                        'patronymic': patronymic if patronymic else (user.patronymic or ''),
                        'phone': phone if phone else (user.phone or ''),
                        'passport_number': passport_number if passport_number else (user.passport_number or ''),
                        'birthday': birthday if birthday else (user.birthday.strftime('%d.%m.%Y') if user.birthday else ''),
                    }
                    return render(request, 'profile.html', context)
                else:
                    account.email = email
                    account.save()
                    request.session['user_email'] = email
                    messages.success(request, 'Email успешно обновлен')

            messages.success(request, 'Профиль успешно обновлен')
            return redirect('profile')

        # Проверяем роль пользователя
        is_admin = account.role_id and account.role_id.role_name == 'ADMIN'
        
        if is_admin:
            # Статистика для администратора
            from django.db.models import Count, Sum, Avg
            from django.utils import timezone
            from datetime import timedelta
            
            # Статистика по пользователям
            total_users = User.objects.count()
            total_accounts = Account.objects.count()
            users_with_tickets = User.objects.filter(
                id_user__in=Payment.objects.values_list('user_id', flat=True).distinct()
            ).count()
            
            # Статистика по самолетам
            total_airplanes = Airplane.objects.count()
            total_capacity = Airplane.objects.aggregate(Sum('capacity'))['capacity__sum'] or 0
            
            # Статистика по рейсам
            total_flights = Flight.objects.count()
            scheduled_flights = Flight.objects.filter(status='SCHEDULED').count()
            completed_flights = Flight.objects.filter(status='COMPLETED').count()
            cancelled_flights = Flight.objects.filter(status='CANCELLED').count()
            
            # Статистика по билетам
            total_tickets = Ticket.objects.count()
            paid_tickets = Ticket.objects.filter(status='PAID').count()
            booked_tickets = Ticket.objects.filter(status='BOOKED').count()
            
            # Статистика по платежам
            total_payments = Payment.objects.count()
            total_revenue = Payment.objects.aggregate(Sum('total_cost'))['total_cost__sum'] or Decimal('0.00')
            completed_payments = Payment.objects.filter(status='COMPLETED').count()
            
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
            
            context = {
                'user': user,
                'account': account,
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
            }
        else:
            # История покупок для обычных пользователей
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

            context = {
                'user': user,
                'account': account,
                'email': account.email,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'patronymic': user.patronymic or '',
                'phone': user.phone or '',
                'passport_number': user.passport_number or '',
                'birthday': user.birthday.strftime('%d.%m.%Y') if user.birthday else '',
                'is_admin': False,
                'tickets': tickets,
                'total_tickets': len(tickets),
            }
        
        return render(request, 'profile.html', context)

    except Account.DoesNotExist:
        messages.error(request, 'Аккаунт не найден')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Ошибка при загрузке профиля: {str(e)}')
        return redirect('index')


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
        messages.error(request, f'Ошибка: {str(e)}')
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
        messages.error(request, f'Ошибка: {str(e)}')
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

            # Создаем билет
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
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('flights')
