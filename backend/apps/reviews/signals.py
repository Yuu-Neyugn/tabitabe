"""
Review Signals
Update restaurant statistics when reviews change
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Review, ReviewHelpful


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_restaurant_review_stats(sender, instance, **kwargs):
    """
    Update restaurant review statistics when review is created, updated, or deleted
    """
    restaurant = instance.restaurant
    
    # Calculate stats only for approved and visible reviews
    approved_reviews = Review.objects.filter(
        restaurant=restaurant,
        status=Review.ReviewStatus.APPROVED,
        is_visible=True
    )
    
    stats = approved_reviews.aggregate(
        total=Count('id'),
        avg_rating=Avg('overall_rating')
    )
    
    restaurant.total_reviews = stats['total'] or 0
    restaurant.average_rating = stats['avg_rating'] or 0.00
    restaurant.save(update_fields=['total_reviews', 'average_rating'])


@receiver(post_save, sender=ReviewHelpful)
@receiver(post_delete, sender=ReviewHelpful)
def update_review_helpful_count(sender, instance, **kwargs):
    """
    Update review helpful count
    """
    review = instance.review
    review.helpful_count = review.helpful_marks.count()
    review.save(update_fields=['helpful_count'])
