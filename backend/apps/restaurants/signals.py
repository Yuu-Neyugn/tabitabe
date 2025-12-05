"""
Restaurant Signals
Auto-create restaurant profile when user registers as restaurant owner
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.accounts.models import CustomUser, UserType
from .models import Restaurant, RestaurantStatus


@receiver(post_save, sender=CustomUser)
def create_restaurant_profile(sender, instance, created, **kwargs):
    """
    Auto-create Restaurant profile when user is created with user_type=RESTAURANT
    """
    if created and instance.user_type == UserType.RESTAURANT:
        Restaurant.objects.create(
            user=instance,
            name=f"Restaurant {instance.email}",  # Temporary name
            status=RestaurantStatus.DRAFT,
            is_visible=False,
            is_active=False
        )


@receiver(pre_save, sender=Restaurant)
def restaurant_status_change(sender, instance, **kwargs):
    """
    Handle restaurant status changes and sync is_visible
    """
    if instance.pk:
        try:
            old_instance = Restaurant.objects.get(pk=instance.pk)
            
            # Auto-hide if status changes to non-approved
            if old_instance.status == RestaurantStatus.APPROVED and instance.status != RestaurantStatus.APPROVED:
                instance.is_visible = False
            
            # Auto-show if status changes to approved
            if instance.status == RestaurantStatus.APPROVED and old_instance.status != RestaurantStatus.APPROVED:
                instance.is_visible = True
                
        except Restaurant.DoesNotExist:
            pass
