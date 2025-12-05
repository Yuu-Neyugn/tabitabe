"""
Customer Models
Customer-specific features and preferences
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel, TimestampedModel
from apps.accounts.models import CustomUser
from apps.restaurants.models import Restaurant


class FavoriteRestaurant(TimestampedModel):
    """
    Customer's favorite restaurants
    """
    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorite_restaurants'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    
    class Meta:
        db_table = 'favorite_restaurants'
        verbose_name = 'Favorite Restaurant'
        verbose_name_plural = 'Favorite Restaurants'
        unique_together = ['customer', 'restaurant']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.email} -> {self.restaurant.name}"


class CustomerPreference(models.Model):
    """
    Customer preferences and settings
    """
    customer = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    
    # Notification Preferences
    email_notifications = models.BooleanField('Email Notifications', default=True)
    push_notifications = models.BooleanField('Push Notifications', default=True)
    sms_notifications = models.BooleanField('SMS Notifications', default=False)
    
    # Marketing
    marketing_emails = models.BooleanField('Marketing Emails', default=False)
    newsletter = models.BooleanField('Newsletter', default=False)
    
    # Privacy
    show_reviews_publicly = models.BooleanField('Show Reviews Publicly', default=True)
    share_location = models.BooleanField('Share Location', default=False)
    
    # Display
    language = models.CharField(
        'Language',
        max_length=10,
        choices=[('ja', 'Japanese'), ('en', 'English')],
        default='ja'
    )
    
    class Meta:
        db_table = 'customer_preferences'
        verbose_name = 'Customer Preference'
        verbose_name_plural = 'Customer Preferences'
    
    def __str__(self):
        return f"Preferences for {self.customer.email}"


class CustomerSearchHistory(TimestampedModel):
    """
    Track customer search queries for recommendations
    """
    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='search_history'
    )
    query = models.CharField('Search Query', max_length=200)
    filters_used = models.JSONField('Filters Used', default=dict, blank=True)
    results_count = models.PositiveIntegerField('Results Count', default=0)
    
    class Meta:
        db_table = 'customer_search_history'
        verbose_name = 'Search History'
        verbose_name_plural = 'Search History'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.customer.email}: {self.query}"


class CustomerActivity(TimestampedModel):
    """
    Track customer activities for analytics
    """
    
    class ActivityType(models.TextChoices):
        RESTAURANT_VIEW = 'restaurant_view', _('Restaurant View')
        REVIEW_CREATE = 'review_create', _('Review Created')
        REVIEW_UPDATE = 'review_update', _('Review Updated')
        FAVORITE_ADD = 'favorite_add', _('Favorite Added')
        FAVORITE_REMOVE = 'favorite_remove', _('Favorite Removed')
        GIFTCARD_PURCHASE = 'giftcard_purchase', _('Gift Card Purchased')
        GIFTCARD_USE = 'giftcard_use', _('Gift Card Used')
        STAMPRALLY_JOIN = 'stamprally_join', _('Stamp Rally Joined')
        STAMP_COLLECT = 'stamp_collect', _('Stamp Collected')
    
    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        'Activity Type',
        max_length=30,
        choices=ActivityType.choices
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_activities'
    )
    metadata = models.JSONField('Metadata', default=dict, blank=True)
    
    class Meta:
        db_table = 'customer_activities'
        verbose_name = 'Customer Activity'
        verbose_name_plural = 'Customer Activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.customer.email} - {self.get_activity_type_display()}"
