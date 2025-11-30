import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import RequestLog, BlacklistedIP, SuspiciousIP


class Command(BaseCommand):
    help = "Seed the core app with sample security data (RequestLog, BlacklistedIP, SuspiciousIP)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--logs",
            type=int,
            default=100,
            help="Number of RequestLog records to create (default: 100)",
        )

    def handle(self, *args, **options):
        num_logs = options["logs"]
        self.stdout.write(self.style.MIGRATE_HEADING(f"Seeding core app with {num_logs} RequestLog entries..."))

        self.create_request_logs(num_logs)
        self.create_blacklisted_ips()
        self.create_suspicious_ips()

        self.stdout.write(self.style.SUCCESS("Core app seeding completed."))

    # ---------- Request logs ----------

    def create_request_logs(self, num_logs):
        User = get_user_model()

        # Grab a few random users if they exist (customers, admins, etc.)
        users = list(User.objects.all())
        methods = ["GET", "POST", "PUT", "DELETE"]
        paths = [
            "/",
            "/admin/login/",
            "/admin/",
            "/api/products/",
            "/api/products/electronics-product-1/",
            "/api/cart/",
            "/api/orders/",
            "/api/auth/login/",
            "/api/auth/register/",
            "/api/security/dashboard/",
        ]
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "curl/8.0.1",
            "PostmanRuntime/7.29.2",
            "Mozilla/5.0 (Linux; Android 12)",
        ]
        referers = [
            "",
            "https://google.com/search?q=duka",
            "https://example.com/",
            "http://localhost:3000/",
        ]
        countries = [
            "Kenya",
            "United States",
            "Germany",
            "India",
            "United Kingdom",
            None,  # Unknown
        ]
        ips = [
            "102.68.1.23",
            "197.248.45.120",
            "41.90.12.200",
            "192.168.1.10",
            "203.0.113.5",
            "198.51.100.42",
            "172.16.0.22",
        ]

        now = timezone.now()
        logs_to_create = []

        for _ in range(num_logs):
            # Random time in the last 14 days
            delta_days = random.randint(0, 14)
            delta_seconds = random.randint(0, 24 * 60 * 60)
            created_at = now - timedelta(days=delta_days, seconds=delta_seconds)

            path = random.choice(paths)
            method = random.choice(methods)
            status_code = random.choice([200, 200, 200, 201, 204, 400, 401, 403, 404, 500])

            # /admin and /api/auth paths considered sensitive
            is_sensitive = path.startswith("/admin") or path.startswith("/api/auth")

            logs_to_create.append(
                RequestLog(
                    user=random.choice(users) if users and random.random() < 0.6 else None,
                    ip_address=random.choice(ips),
                    path=path,
                    method=method,
                    user_agent=random.choice(user_agents),
                    referer=random.choice(referers),
                    status_code=status_code,
                    is_sensitive=is_sensitive,
                    created_at=created_at,
                    country=random.choice(countries),
                    city=None,
                )
            )

        # Bulk create
        RequestLog.objects.bulk_create(logs_to_create)
        self.stdout.write(self.style.SUCCESS(f"Created {num_logs} RequestLog records."))

    # ---------- Blacklisted IPs ----------

    def create_blacklisted_ips(self):
        sample_blacklist = [
            ("198.51.100.42", "Detected scraping behavior and rate limit abuse."),
            ("203.0.113.5", "Multiple failed login attempts on /admin."),
        ]

        created_count = 0
        for ip, reason in sample_blacklist:
            obj, created = BlacklistedIP.objects.get_or_create(
                ip_address=ip,
                defaults={
                    "reason": reason,
                    "active": True,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"BlacklistedIP: {created_count} new entries created (others already existed)."))

    # ---------- Suspicious IPs ----------

    def create_suspicious_ips(self):
        now = timezone.now()
        sample_suspicious = [
            ("192.168.1.10", 150, "High request volume in a short period."),
            ("172.16.0.22", 90, "Repeated access to sensitive endpoints."),
        ]

        created_count = 0
        for ip, count, notes in sample_suspicious:
            obj, created = SuspiciousIP.objects.get_or_create(
                ip_address=ip,
                defaults={
                    "request_count": count,
                    "notes": notes,
                    "first_detected_at": now - timedelta(days=1),
                    "last_detected_at": now,
                },
            )
            if not created:
                # Update counts if it already existed
                obj.request_count = max(obj.request_count, count)
                obj.notes = obj.notes or notes
                obj.last_detected_at = now
                obj.save()
            else:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"SuspiciousIP: {created_count} new entries created (others updated if present)."))
