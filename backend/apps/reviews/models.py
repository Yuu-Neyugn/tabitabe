"""
Review Models
Customer reviews and ratings for restaurants
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.core.models import BaseModel
from apps.accounts.models import CustomUser
from apps.restaurants.models import Restaurant


class Review(BaseModel):
    """
    Customer reviews for restaurants
    """
    
    class ReviewStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Moderation')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        FLAGGED = 'flagged', _('Flagged')
    
    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    # Ratings
    overall_rating = models.DecimalField(
        'Overall Rating',
        max_digits=2,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('1.0')),
            MaxValueValidator(Decimal('5.0'))
        ]
    )
    
    food_rating = models.DecimalField(
        'Food Rating',
        max_digits=2,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('1.0')),
            MaxValueValidator(Decimal('5.0'))
        ],
        null=True,
        blank=True
    )
    
    service_rating = models.DecimalField(
        'Service Rating',
        max_digits=2,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('1.0')),
            MaxValueValidator(Decimal('5.0'))
        ],
        null=True,
        blank=True
    )
    
    atmosphere_rating = models.DecimalField(
        'Atmosphere Rating',
        max_digits=2,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('1.0')),
            MaxValueValidator(Decimal('5.0'))
        ],
        null=True,
        blank=True
    )
    
    value_rating = models.DecimalField(
        'Value for Money Rating',
        max_digits=2,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('1.0')),
            MaxValueValidator(Decimal('5.0'))
        ],
        null=True,
        blank=True
    )
    
    # Content
    title = models.CharField('Review Title', max_length=200, blank=True)
    comment = models.TextField('Comment', max_length=2000)
    
    # Visit Info
    visit_date = models.DateField('Visit Date', null=True, blank=True)
    
    # Media
    image1 = models.ImageField('Photo 1', upload_to='reviews/', null=True, blank=True)
    image2 = models.ImageField('Photo 2', upload_to='reviews/', null=True, blank=True)
    image3 = models.ImageField('Photo 3', upload_to='reviews/', null=True, blank=True)
    
    # Moderation
    status = models.CharField(
        'Status',
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        db_index=True
    )
    
    is_visible = models.BooleanField('Visible', default=False)
    
    moderated_at = models.DateTimeField('Moderated At', null=True, blank=True)
    moderated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews'
    )
    moderation_note = models.TextField('Moderation Note', blank=True)
    
    # Engagement
    helpful_count = models.PositiveIntegerField('Helpful Count', default=0)
    
    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['customer', 'restaurant']  # One review per customer per restaurant
        indexes = [
            models.Index(fields=['restaurant', 'status', '-created_at']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['overall_rating']),
        ]
    
    def __str__(self):
        return f"{self.customer.email} -> {self.restaurant.name} ({self.overall_rating}★)"
    
    def approve(self, admin_user):
        """Approve review"""
        from django.utils import timezone
        self.status = self.ReviewStatus.APPROVED
        self.is_visible = True
        self.moderated_at = timezone.now()
        self.moderated_by = admin_user
        self.save()
        
        # Update restaurant stats
        self.restaurant.update_review_stats()
    
    def reject(self, admin_user, reason=''):
        """Reject review"""
        from django.utils import timezone
        self.status = self.ReviewStatus.REJECTED
        self.is_visible = False
        self.moderated_at = timezone.now()
        self.moderated_by = admin_user
        self.moderation_note = reason
        self.save()


class ReviewHelpful(models.Model):
    """
    Track which users found reviews helpful
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpful_marks'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='helpful_reviews'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_helpful'
        unique_together = ['review', 'user']
    
    def __str__(self):
        return f"{self.user.email} found {self.review.id} helpful"


class ReviewFlag(models.Model):
    """
    User flags for inappropriate reviews
    """
    
    class FlagReason(models.TextChoices):
        SPAM = 'spam', _('Spam')
        OFFENSIVE = 'offensive', _('Offensive Language')
        FAKE = 'fake', _('Fake Review')
        MISLEADING = 'misleading', _('Misleading Information')
        OTHER = 'other', _('Other')
    
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='flags'
    )
    reporter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='review_flags'
    )
    reason = models.CharField(
        'Reason',
        max_length=20,
        choices=FlagReason.choices
    )
    description = models.TextField('Description', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField('Resolved', default=False)
    resolved_at = models.DateTimeField('Resolved At', null=True, blank=True)
    resolved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_flags'
    )
    
    class Meta:
        db_table = 'review_flags'
        unique_together = ['review', 'reporter']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Flag on {self.review.id} by {self.reporter.email}"


class RestaurantResponse(BaseModel):
    """
    Restaurant owner responses to reviews
    """
    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,
        related_name='restaurant_response'
    )
    
    restaurant_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='review_responses'
    )
    
    response = models.TextField('Response', max_length=1000)
    
    class Meta:
        db_table = 'restaurant_responses'
        verbose_name = 'Restaurant Response'
        verbose_name_plural = 'Restaurant Responses'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Response to review {self.review.id}"
