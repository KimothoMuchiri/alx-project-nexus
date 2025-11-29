from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone

from store.models import Order, OrderReminder


class Command(BaseCommand):
    help = "Send reminders for pending orders created within the last 7 days (one reminder per order)."

    def handle(self, *args, **options):
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        # Pending orders created in last 7 days, that haven't had a reminder yet
        pending_orders = (
            Order.objects
            .filter(
                status=Order.Status.PENDING,
                created_at__gte=week_ago,
            )
            .filter(reminder__isnull=True)  # 👈 exclude orders already reminded
            .select_related("user")
        )

        log_path = "/tmp/order_reminders_log.txt"  # adjust on Windows if needed

        with open(log_path, "a", encoding="utf-8") as f:
            for order in pending_orders:
                user = order.user
                customer_email = getattr(user, "email", None)

                if not customer_email:
                    # Skip orders with no email, but don't create a reminder record
                    continue

                timestamp = now.isoformat()
                log_line = (
                    f"[{timestamp}] "
                    f"Order ID: {order.id}, "
                    f"Customer email: {customer_email}\n"
                )
                f.write(log_line)

                # Build a polite email
                subject = "Reminder: Your Duka order is still pending"
                message = (
                    f"Hi {user.username},\n\n"
                    f"We noticed that your order (ID: {order.id}) placed on "
                    f"{order.created_at.strftime('%Y-%m-%d')} is still in a pending state.\n\n"
                    f"If you still intend to complete this order, please log in to your Duka account "
                    f"to review and finalize it.\n\n"
                    f"If you have any questions or this reminder was unexpected, "
                    f"please contact our support team.\n\n"
                    f"Thank you,\n"
                    f"The Duka Team"
                )

                # Send the email
                send_mail(
                    subject,
                    message,
                    None,  # uses DEFAULT_FROM_EMAIL
                    [customer_email],
                    fail_silently=False,
                )

                # Record that we sent a reminder for this order
                OrderReminder.objects.create(
                    order=order,
                    sent_at=now,
                )

        self.stdout.write(self.style.SUCCESS("Order reminders processed!"))
