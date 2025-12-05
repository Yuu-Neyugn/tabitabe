"""
Campaign Signals
Handle campaign-related events
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Stamped, CustomerStamprally, WinPrize
import secrets


@receiver(post_save, sender=Stamped)
def check_stamprally_completion(sender, instance, created, **kwargs):
    """
    Check if customer completed stamp rally after collecting new stamp
    """
    if created:
        customer_stamprally = instance.customer_stamprally
        customer_stamprally.check_completion()
        
        # Auto-create prize if completed
        if customer_stamprally.completed and not hasattr(customer_stamprally, 'prize'):
            WinPrize.objects.create(
                customer_stamprally=customer_stamprally,
                prize_description=customer_stamprally.stamprally.prize_description
            )


def generate_giftcard_code():
    """
    Generate unique gift card code
    """
    return secrets.token_urlsafe(12).upper()[:16]
