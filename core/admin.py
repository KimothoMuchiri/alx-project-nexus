from django.contrib import admin
from .models import RequestLog, BlacklistedIP, SuspiciousIP

@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = (
        "ip_address",
        "method",
        "path",
        "status_code",
        "user",
        "country",
        "created_at",
    )
    list_filter = (
        "method",
        "status_code",
        "is_sensitive",
        "country",
        "created_at",
    )
    search_fields = (
        "ip_address",
        "path",
        "user__username",
        "user_agent",
        "referer",
    )
    readonly_fields = (
        "user",
        "ip_address",
        "path",
        "method",
        "user_agent",
        "referer",
        "status_code",
        "is_sensitive",
        "country",
        "city",
        "created_at",
    )
    ordering = ("-created_at",)
    list_per_page = 50


@admin.register(BlacklistedIP)
class BlacklistedIPAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "active", "created_at", "expires_at")
    list_filter = ("active", "created_at")
    search_fields = ("ip_address", "reason")
    ordering = ("-created_at",)


@admin.register(SuspiciousIP)
class SuspiciousIPAdmin(admin.ModelAdmin):
    list_display = (
        "ip_address",
        "request_count",
        "first_detected_at",
        "last_detected_at",
    )
    search_fields = ("ip_address",)
    ordering = ("-last_detected_at",)
