from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from .models import RateLimitRecord

def get_client_ip(request):
    """Get the real client IP, handling Render/Cloudflare proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')

def anti_spam(action='default', max_requests=5, window_minutes=1):
    """
    Custom database-backed rate limiter + honeypot trap.
    No Redis required! Uses your existing PostgreSQL database.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.method == 'POST':
                # 1. Honeypot check (bots fill this, humans don't)
                if request.POST.get('honeypot'):
                    return HttpResponseForbidden()
                
                # 2. Rate limit check
                ip = get_client_ip(request)
                cutoff = timezone.now() - timedelta(minutes=window_minutes)
                
                # Count recent submissions from this IP for this specific action
                count = RateLimitRecord.objects.filter(
                    ip=ip, 
                    action=action, 
                    timestamp__gte=cutoff
                ).count()
                
                if count >= max_requests:
                    return HttpResponseForbidden("Too many requests. Please wait a moment before trying again.")
                
                # Record this valid request
                RateLimitRecord.objects.create(ip=ip, action=action)
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
