from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Logs a heartbeat message to confirm Duka app health."

    def handle(self, *args, **options):
        now = timezone.now().isoformat()
        log_path = "/tmp/duka_heartbeat.log"  # change if needed on Windows

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{now}] Duka heartbeat OK\n")

        self.stdout.write(self.style.SUCCESS("Heartbeat logged."))
