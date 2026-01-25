from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.utils.dateparse import parse_date
from django.db.models import Q
from .models import User, Account, Role, Payment, Ticket, Flight, Passenger, Airport


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
            flights_list = flights_list.filter(status=status_map[status_filter])
    
    if date_filter:
        try:
            filter_date = timezone.datetime.strptime(date_filter, '%Y-%m-%d').date()
            flights_list = flights_list.filter(departure_time__date=filter_date)
        except ValueError:
            pass  # Игнорируем неверный формат даты
    
    # Получаем уникальные города для фильтров
    departure_cities = Airport.objects.values_list('city', flat=True).distinct().order_by('city')
    arrival_cities = Airport.objects.values_list('city', flat=True).distinct().order_by('city')
    
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
        table_html = render_to_string('flights_table.html', {'flights': flights_page}, request=request)
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
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
            return render(request, 'register.html', context)

        # Проверка минимальной длины пароля
        if len(password) < 6:
            messages.error(request, 'Пароль должен содержать минимум 6 символов')
            return render(request, 'register.html', context)

        # Проверка совпадения паролей
        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'register.html', context)

        # Проверка уникальности email
        if Account.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
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
        messages.error(request, 'Для доступа к профилю необходимо войти в систему')
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
                messages.error(request, f'Ошибка при сохранении данных: {str(e)}')
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
                    messages.error(request, 'Пользователь с таким email уже существует')
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
        
        # Получаем историю покупок пользователя
        # Находим все платежи пользователя
        payments = Payment.objects.filter(user_id=user).order_by('-payment_date')
        
        # Получаем все билеты, связанные с этими платежами
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
        
        # Сортируем билеты по дате платежа (новые сначала)
        tickets.sort(key=lambda x: x['payment'].payment_date, reverse=True)
        
        # Подготавливаем контекст для отображения
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
