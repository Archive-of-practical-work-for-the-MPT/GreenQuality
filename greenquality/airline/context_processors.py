"""Context processors для добавления данных в контекст всех шаблонов"""
from .models import Account


def admin_status(request):
    """Добавляет is_admin в контекст всех шаблонов"""
    is_admin = False
    
    if 'account_id' in request.session:
        account_id = request.session.get('account_id')
        try:
            account = Account.objects.select_related('role_id').get(id_account=account_id)
            if account.role_id and account.role_id.role_name == 'ADMIN':
                is_admin = True
                # Обновляем сессию для будущих запросов
                request.session['is_admin'] = True
            else:
                request.session['is_admin'] = False
        except Account.DoesNotExist:
            request.session['is_admin'] = False
    else:
        if 'is_admin' in request.session:
            del request.session['is_admin']
    
    return {'is_admin': is_admin}
