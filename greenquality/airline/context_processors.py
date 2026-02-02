"""Context processors для добавления данных в контекст всех шаблонов"""
from .models import Account


def admin_status(request):
    """Добавляет is_admin, is_manager и is_authenticated в контекст всех шаблонов"""
    is_admin = False
    is_manager = False
    is_authenticated = 'account_id' in request.session

    if 'account_id' in request.session:
        account_id = request.session.get('account_id')
        try:
            account = Account.objects.select_related('role_id').get(id_account=account_id)
            if account.role_id:
                if account.role_id.role_name == 'ADMIN':
                    is_admin = True
                    request.session['is_admin'] = True
                elif account.role_id.role_name == 'MANAGER':
                    is_manager = True
                    request.session['is_manager'] = True
                else:
                    request.session['is_admin'] = False
                    request.session['is_manager'] = False
            else:
                request.session['is_admin'] = False
                request.session['is_manager'] = False
        except Account.DoesNotExist:
            request.session['is_admin'] = False
            request.session['is_manager'] = False
    else:
        if 'is_admin' in request.session:
            del request.session['is_admin']
        if 'is_manager' in request.session:
            del request.session['is_manager']

    return {'is_admin': is_admin, 'is_manager': is_manager, 'is_authenticated': is_authenticated}
