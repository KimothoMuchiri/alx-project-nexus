from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import RequestLog


class Command(BaseCommand):
    help = "Delete old request logs for data retention compliance."

    RETENTION_DAYS = 90  

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=self.RETENTION_DAYS)
        deleted, _ = RequestLog.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} old request logs."))
