from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone

from store.models import Product
from accounts.models import User


class Command(BaseCommand):
    help = "Find low-stock products (stock < 10), log them, and email store managers."

    LOW_STOCK_THRESHOLD = 10

    def handle(self, *args, **options):
        now = timezone.now()
        log_path = "/tmp/low_stock_log.txt"  # change path if needed on Windows

        # Find products with stock < threshold
        low_stock_products = (
            Product.objects
            .filter(stock__lt=self.LOW_STOCK_THRESHOLD, is_active=True)
            .select_related("category")
            .order_by("stock")
        )

        # Log to file
        with open(log_path, "a", encoding="utf-8") as f:
            if not low_stock_products.exists():
                f.write(f"[{now.isoformat()}] No low-stock products found.\n")
            else:
                f.write(f"[{now.isoformat()}] Low-stock products (stock < {self.LOW_STOCK_THRESHOLD}):\n")
                for p in low_stock_products:
                    line = (
                        f"  - Product ID: {p.id}, "
                        f"Name: {p.name}, "
                        f"Category: {p.category.name if p.category else 'N/A'}, "
                        f"Stock: {p.stock}\n"
                    )
                    f.write(line)

        # Build email recipients: all store managers with an email
        managers = User.objects.filter(
            role=User.Roles.STORE_MANAGER,
        ).exclude(email__isnull=True).exclude(email__exact="")

        recipients = [m.email for m in managers]

        # If no managers, just log and exit gracefully
        if not recipients:
            self.stdout.write(self.style.WARNING("No store managers with email found. Skipping email."))
            self.stdout.write(self.style.SUCCESS("Low-stock check completed (no email sent)."))
            return

        # If there are low-stock products, send an email summary
        if low_stock_products.exists():
            subject = "Duka: Low-stock products alert"
            lines = [
                "Hello Store Manager,\n",
                f"The following products have low stock (less than {self.LOW_STOCK_THRESHOLD} units):\n",
            ]

            for p in low_stock_products:
                lines.append(
                    f"- [{p.id}] {p.name} "
                    f"(Category: {p.category.name if p.category else 'N/A'}, "
                    f"Stock: {p.stock})"
                )

            lines.append(
                "\nPlease review and restock these items as needed.\n\n"
                "Regards,\n"
                "Duka System"
            )

            message = "\n".join(lines)

            send_mail(
                subject,
                message,
                None,  # uses DEFAULT_FROM_EMAIL
                recipients,
                fail_silently=False,
            )

            self.stdout.write(self.style.SUCCESS(
                f"Low-stock alert email sent to {len(recipients)} store manager(s)."
            ))
        else:
            # No low-stock products = nothing to email
            self.stdout.write(self.style.WARNING("No low-stock products. No email sent."))

        self.stdout.write(self.style.SUCCESS("Low-stock products check completed."))
