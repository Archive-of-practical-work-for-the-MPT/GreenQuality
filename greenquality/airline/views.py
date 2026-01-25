from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Account, Role


def index(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


def contacts(request):
    return render(request, 'contacts.html')


def flights(request):
    return render(request, 'flights.html')


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
