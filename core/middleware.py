import re
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings
from .models import RequestLog, BlacklistedIP
from .utils import get_client_ip, anonymize_ip
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseForbidden

SENSITIVE_PATHS = [
    re.compile(r"^/admin"),
    re.compile(r"^/api/auth"),
]

class IPBlacklistMiddleware(MiddlewareMixin):
    """
    Blocks requests from blacklisted IPs.
    """

    def process_request(self, request):
        ip = get_client_ip(request)

        try:
            entry = BlacklistedIP.objects.get(ip_address=ip, active=True)
        except BlacklistedIP.DoesNotExist:
            return None

        # Optional: auto-deactivate expired entries
        if entry.expires_at and entry.expires_at < timezone.now():
            entry.active = False
            entry.save()
            return None

        return HttpResponseForbidden("Access denied.")

class IPRateLimitMiddleware(MiddlewareMixin):
    """
    IP-based rate limiting for non-API views like /admin.
    Example: max 50 requests per 10 minutes per IP.
    """

    WINDOW_SECONDS = 600  # 10 minutes
    MAX_REQUESTS = 30

    def process_request(self, request):
        path = request.path
        # Only apply to admin -can add other sensitive paths
        if not path.startswith("/admin"):
            return None

        ip = get_client_ip(request)
        key = f"rate:{ip}"

        count = cache.get(key, 0)
        if count >= self.MAX_REQUESTS:
            return HttpResponse("Too many requests. Please try again later.", status=429)

        # Increment
        if count == 0:
            cache.set(key, 1, timeout=self.WINDOW_SECONDS)
        else:
            cache.incr(key)

        return None

class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Logs IP, request path, method, UA, status.
    Flags sensitive endpoints like /admin.
    Supports IP anonymization for GDPR.
    """

    def process_request(self, request):
        # Attach metadata for use in process_response
        request._client_ip = get_client_ip(request)
        request._requested_at = timezone.now()
        return None

    def process_response(self, request, response):
        try:
            ip = getattr(request, "_client_ip", None) or get_client_ip(request)
            path = request.path
            method = request.method
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            referer = request.META.get("HTTP_REFERER", "")
            status_code = response.status_code
            user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None

            is_sensitive = any(pattern.match(path) for pattern in SENSITIVE_PATHS)

            # GDPR-friendly IP
            if getattr(settings, "ANONYMIZE_IP", True):
                ip_to_store = anonymize_ip(ip)
            else:
                ip_to_store = ip

            # Use django-ip-geolocation’s geolocation object
            geo = getattr(request, "geolocation", None)
            country = getattr(geo, "country", None) if geo else None
            country_code = getattr(geo, "country_code", None) if geo else None
            # IPinfo Lite doesn’t give city in Lite bundle, but it gives continent + ASN.:contentReference[oaicite:6]{index=6}
            city = None

            RequestLog.objects.create(
                user=user,
                ip_address=ip_to_store,
                path=path,
                method=method,
                user_agent=user_agent[:500],
                referer=referer[:500],
                status_code=status_code,
                is_sensitive=is_sensitive,
                country=country or country_code,
                city=city,
            )
        except Exception:
            pass

        return response
