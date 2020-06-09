from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect

from functools import wraps

def activation_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    @wraps(function)
    def decorator(request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.verified():
            return redirect('zoom_converter:profile')
        return function(request, *args, **kwargs)
    return decorator
