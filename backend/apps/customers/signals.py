"""
Customer Signals
Auto-create customer preferences
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.models import CustomUser, UserType
from .models import CustomerPreference


@receiver(post_save, sender=CustomUser)
def create_customer_preferences(sender, instance, created, **kwargs):
    """
    Auto-create CustomerPreference when user is created with user_type=CUSTOMER
    """
    if created and instance.user_type == UserType.CUSTOMER:
        CustomerPreference.objects.create(customer=instance)
