from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
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

        try:
            account = Account.objects.get(email=email)
            if account.password == password:  # В реальном проекте используйте хэширование
                # Здесь должна быть логика установки сессии
                messages.success(request, 'Вы успешно вошли в систему!')
                return redirect('index')
            else:
                messages.error(request, 'Неверный email или пароль')
        except Account.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден')

    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        # Получаем данные из формы
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        patronymic = request.POST.get('patronymic', '')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Проверка совпадения паролей
        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'register.html')

        # Проверка уникальности email
        if Account.objects.filter(email=email).exists():
            messages.error(
                request, 'Пользователь с таким email уже существует')
            return render(request, 'register.html')

        try:
            # Создаем аккаунт
            # Предполагаем, что роль USER существует
            role = Role.objects.get(role_name='USER')
            account = Account.objects.create(
                email=email,
                password=password,  # В реальном проекте используйте make_password()
                role_id=role
            )

            # Создаем пользователя (остальные поля будут заполнены в профиле)
            user = User.objects.create(
                account_id=account,
                first_name=first_name,
                last_name=last_name,
                patronymic=patronymic,
                phone='',  # Будет заполнено в профиле
                passport_number='',  # Будет заполнено в профиле
                birthday=None  # Будет заполнено в профиле
            )

            messages.success(
                request, 'Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Ошибка при регистрации: {str(e)}')

    return render(request, 'register.html')
