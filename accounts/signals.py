from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomerProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_profile(sender, instance, created, **kwargs):
    if not created:
        return

    # Only create profile automatically for customers
    try:
        role = instance.role
    except AttributeError:
        role = None

    if role == instance.Roles.CUSTOMER:
        CustomerProfile.objects.get_or_create(user=instance)
