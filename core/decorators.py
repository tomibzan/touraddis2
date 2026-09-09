from functools import wraps
from django.http import HttpResponseForbidden
from django_ratelimit.decorators import ratelimit

def anti_spam(group='forms', rate='5/m'):
    """
    Decorator that applies IP-based rate limiting AND a honeypot check.
    Usage: @anti_spam(group='contact', rate='3/m')
    """
    def decorator(view_func):
        @wraps(view_func)
        @ratelimit(key='ip', rate=rate, block=True)
        def _wrapped_view(request, *args, **kwargs):
            # Honeypot check: Look for a field named 'honeypot' in POST data
            # Humans won't fill this (it's hidden via CSS), but bots will.
            if request.method == 'POST' and request.POST.get('honeypot'):
                # Silently return a 200 OK to confuse the bot, but do nothing
                return HttpResponseForbidden() 
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
