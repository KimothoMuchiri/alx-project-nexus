from datetime import timedelta
from decimal import Decimal

from celery import shared_task
from django.utils import timezone

from accounts.models import User
from store.models import Order, Product


@shared_task(name="generate_crm_report")
def generate_crm_report():
    """
    Weekly CRM-style report summarizing:
    - total orders
    - total customers
    - total products
    - number of low-stock products
    - number of pending orders
    Logs the report to a file.
    """

    now = timezone.now()
    one_week_ago = now - timedelta(days=7)

    # Basic stats
    total_orders = Order.objects.count()
    total_orders_last_week = Order.objects.filter(created_at__gte=one_week_ago).count()

    total_customers = User.objects.filter(role=User.Roles.CUSTOMER).count()
    new_customers_last_week = User.objects.filter(
        role=User.Roles.CUSTOMER,
        date_joined__gte=one_week_ago,
    ).count()

    total_products = Product.objects.count()
    low_stock_threshold = 10
    low_stock_count = Product.objects.filter(stock__lt=low_stock_threshold, is_active=True).count()

    pending_orders = Order.objects.filter(status=Order.Status.PENDING).count()

    # Build report text
    report_lines = [
        f"=== Duka Weekly CRM Report ===",
        f"Generated at: {now.isoformat()}",
        "",
        f"Orders:",
        f"  - Total orders: {total_orders}",
        f"  - Orders in last 7 days: {total_orders_last_week}",
        "",
        f"Customers:",
        f"  - Total customers: {total_customers}",
        f"  - New customers in last 7 days: {new_customers_last_week}",
        "",
        f"Products:",
        f"  - Total products: {total_products}",
        f"  - Low-stock products (stock < {low_stock_threshold}): {low_stock_count}",
        "",
        f"Order Status:",
        f"  - Pending orders: {pending_orders}",
        "",
        "==============================",
        "",
    ]

    report_text = "\n".join(report_lines)

    # Log to a file
    log_path = "D:/tmp/duka_weekly_crm_report.log"  # adjust on Windows if needed
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(report_text)

    # Also print to worker log
    print(report_text)

    return {
        "generated_at": now.isoformat(),
        "total_orders": total_orders,
        "total_orders_last_week": total_orders_last_week,
        "total_customers": total_customers,
        "new_customers_last_week": new_customers_last_week,
        "total_products": total_products,
        "low_stock_count": low_stock_count,
        "pending_orders": pending_orders,
    }
