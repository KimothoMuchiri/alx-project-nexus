from datetime import datetime, time, timedelta

from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.core.cache import cache
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.models import RequestLog, BlacklistedIP, SuspiciousIP
from core.serializers import SecurityDashboardSerializer


class SecurityDashboardView(APIView):
    """
    Admin-only security dashboard.

    Supports:
    - Date range filtering via ?from=YYYY-MM-DD&to=YYYY-MM-DD
    - Configurable number of top IPs via ?top_n=10
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Security dashboard overview",
        description=(
            "Returns aggregated security metrics including requests per country, "
            "top IPs by volume, and counts of blacklisted & suspicious IPs. "
            "Can be filtered by date range using 'from' and 'to' query parameters "
            "(format: YYYY-MM-DD)."
        ),
        responses={200: SecurityDashboardSerializer},
        parameters=[
            OpenApiParameter(
                name="from",
                description="Start date (inclusive), format YYYY-MM-DD. Defaults to 7 days ago if omitted.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="to",
                description="End date (inclusive), format YYYY-MM-DD. Defaults to today if omitted.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="top_n",
                description="Number of top IPs to return (default: 10).",
                required=False,
                type=int,
            ),
        ],
    )
    def get(self, request):
        # ----- Parse query parameters -----
        from_param = request.query_params.get("from")
        to_param = request.query_params.get("to")
        top_n = request.query_params.get("top_n")

        # Default: last 7 days window
        now = timezone.now()
        default_start = now - timedelta(days=7)
        default_end = now

        # Parse from/to dates (YYYY-MM-DD)
        window_start = self._parse_date_to_start(from_param) or default_start
        window_end = self._parse_date_to_end(to_param) or default_end

        # top_n handling
        try:
            top_n = int(top_n) if top_n is not None else 10
        except ValueError:
            top_n = 10

        # ----- Caching: key based on date range + top_n -----
        cache_key = f"security_dashboard:{window_start.date()}:{window_end.date()}:{top_n}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        # ----- Base queryset filtered by date range -----
        logs_qs = RequestLog.objects.filter(
            created_at__gte=window_start,
            created_at__lte=window_end,
        )

        # Total requests in window
        total_requests = logs_qs.count()

        # Requests per country
        country_rows = (
            logs_qs
            .values("country")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        requests_per_country = [
            {"country": row["country"] or "Unknown", "count": row["count"]}
            for row in country_rows
        ]

        # Top IPs by volume (within window)
        ip_rows = (
            logs_qs
            .values("ip_address")
            .annotate(count=Count("id"))
            .order_by("-count")[:top_n]
        )
        top_ips = [
            {"ip_address": row["ip_address"], "count": row["count"]}
            for row in ip_rows
        ]

        # Blacklisted & suspicious counts are global
        blacklisted_count = BlacklistedIP.objects.filter(active=True).count()
        suspicious_count = SuspiciousIP.objects.count()

        payload = {
            "total_requests": total_requests,
            "requests_per_country": requests_per_country,
            "top_ips": top_ips,
            "blacklisted_count": blacklisted_count,
            "suspicious_count": suspicious_count,
        }

        serializer = SecurityDashboardSerializer(payload)
        data = serializer.data

        # Cache for a short time so repeated dashboard hits don't pound the DB
        timeout = getattr(settings, "CACHE_TTL_5_MIN", 300)
        cache.set(cache_key, data, timeout=timeout)

        return Response(data)

    @staticmethod
    def _parse_date_to_start(date_str):
        """
        Convert 'YYYY-MM-DD' to an aware datetime at start of the day.
        """
        if not date_str:
            return None
        d = parse_date(date_str)
        if not d:
            return None
        dt = datetime.combine(d, time.min)
        return timezone.make_aware(dt)

    @staticmethod
    def _parse_date_to_end(date_str):
        """
        Convert 'YYYY-MM-DD' to an aware datetime at end of the day.
        """
        if not date_str:
            return None
        d = parse_date(date_str)
        if not d:
            return None
        dt = datetime.combine(d, time.max)
        return timezone.make_aware(dt)
