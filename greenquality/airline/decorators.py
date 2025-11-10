from functools import wraps
from django.http import HttpResponseRedirect
from django.urls import reverse


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if 'account_id' not in request.session:
            # Redirect to login page if not authenticated
            return HttpResponseRedirect(reverse('auth:login'))
        return view_func(request, *args, **kwargs)
    return wrapper
