from django.db import models
from django.conf import settings


class RequestLog(models.Model):
    """
    Request logging for security & analytics.
    IP can be anonymized depending on settings.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='request_logs'
    )
    ip_address = models.CharField(max_length=64, db_index=True)
    path = models.CharField(max_length=255, db_index=True)
    method = models.CharField(max_length=10)
    user_agent = models.TextField(blank=True, null=True)
    referer = models.TextField(blank=True, null=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    is_sensitive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Geolocation fields
    country = models.CharField(max_length=64, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f"{self.ip_address} {self.method} {self.path} [{self.status_code}]"

class BlacklistedIP(models.Model):
    ip_address = models.CharField(max_length=64, unique=True)
    reason = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.ip_address} (active={self.active})"

class SuspiciousIP(models.Model):
    ip_address = models.CharField(max_length=64, unique=True)
    first_detected_at = models.DateTimeField(auto_now_add=True)
    last_detected_at = models.DateTimeField(auto_now=True)
    request_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Suspicious {self.ip_address} ({self.request_count} requests)"

