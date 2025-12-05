"""
Signals for accounts app
Auto-create CustomerProfile when user with user_type=CUSTOMER is created
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, CustomerProfile, UserType


@receiver(post_save, sender=CustomUser)
def create_customer_profile(sender, instance, created, **kwargs):
    """
    Automatically create CustomerProfile when a CUSTOMER user is created
    """
    if created and instance.user_type == UserType.CUSTOMER:
        CustomerProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def update_password_changed_at(sender, instance, **kwargs):
    """
    Update password_changed_at when password is changed
    """
    if instance.pk:
        try:
            old_instance = CustomUser.objects.get(pk=instance.pk)
            if old_instance.password != instance.password:
                from django.utils import timezone
                instance.password_changed_at = timezone.now()
                instance.save(update_fields=['password_changed_at'])
        except CustomUser.DoesNotExist:
            pass
