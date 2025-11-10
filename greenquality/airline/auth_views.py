from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Account, Role


def register_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            role_id = data.get('role_id', 2)  # Default to "user" role

            # Check if account already exists
            if Account.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Аккаунт с таким email уже существует'})

            # Create new account
            account = Account.objects.create(
                email=email,
                password=password,  # In a real app, you should hash the password
                role_id_id=role_id
            )

            return JsonResponse({'success': True, 'message': 'Регистрация успешна!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Ошибка регистрации: ' + str(e)})

    return render(request, 'auth/register.html')


def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            # Find account
            try:
                account = Account.objects.get(email=email)
                # In a real app, you should check the hashed password
                if account.password == password:
                    # Simulate login by storing account ID in session
                    request.session['account_id'] = account.id_account
                    request.session['email'] = account.email
                    return JsonResponse({'success': True, 'message': 'Вход выполнен успешно!'})
                else:
                    return JsonResponse({'success': False, 'message': 'Неверный пароль'})
            except Account.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Аккаунт не найден'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Ошибка входа: ' + str(e)})

    return render(request, 'auth/login.html')


def logout_view(request):
    # Clear session
    if 'account_id' in request.session:
        del request.session['account_id']
    if 'email' in request.session:
        del request.session['email']
    return redirect('index')


@login_required
def profile_view(request):
    account_id = request.session.get('account_id')
    if not account_id:
        return redirect('login')

    try:
        account = Account.objects.get(id_account=account_id)
        return render(request, 'auth/profile.html', {'account': account})
    except Account.DoesNotExist:
        return redirect('login')
