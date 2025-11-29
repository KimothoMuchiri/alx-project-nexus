from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count

from core.models import RequestLog, SuspiciousIP, BlacklistedIP


class Command(BaseCommand):
    help = "Analyze request logs to detect suspicious IPs."

    WINDOW_MINUTES = 10
    THRESHOLD_REQUESTS = 200

    def handle(self, *args, **options):
        now = timezone.now()
        window_start = now - timedelta(minutes=self.WINDOW_MINUTES)

        qs = (
            RequestLog.objects
            .filter(created_at__gte=window_start)
            .values("ip_address")
            .annotate(count=Count("id"))
            .filter(count__gte=self.THRESHOLD_REQUESTS)
        )

        for row in qs:
            ip = row["ip_address"]
            count = row["count"]

            suspicious, created = SuspiciousIP.objects.get_or_create(
                ip_address=ip,
                defaults={"request_count": count},
            )
            if not created:
                suspicious.request_count = count
                suspicious.save()

            # Optional: auto-blacklist
            BlacklistedIP.objects.get_or_create(
                ip_address=ip,
                defaults={"reason": f"Auto-blacklisted due to {count} requests in {self.WINDOW_MINUTES} minutes"}
            )

        self.stdout.write(self.style.SUCCESS("Suspicious IP analysis completed."))
