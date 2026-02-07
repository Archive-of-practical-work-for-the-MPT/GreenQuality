"""
Права доступа для REST API.
Доступ к API имеют только авторизованные администраторы.
"""
from rest_framework import permissions

from .models import Account


class IsAdminUser(permissions.BasePermission):
    """
    Разрешение только для администраторов.
    Проверяет, что пользователь авторизован через сессию и имеет роль ADMIN.
    """
    message = 'Доступ к API разрешён только администраторам. Войдите в систему как администратор.'

    def has_permission(self, request, view):
        account_id = request.session.get('account_id')
        if not account_id:
            return False
        try:
            account = Account.objects.get(id_account=account_id)
            return account.role_id and account.role_id.role_name == 'ADMIN'
        except Account.DoesNotExist:
            return False
