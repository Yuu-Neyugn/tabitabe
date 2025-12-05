"""
Review Admin Configuration
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Review, ReviewHelpful, ReviewFlag, RestaurantResponse


class RestaurantResponseInline(admin.StackedInline):
    model = RestaurantResponse
    extra = 0
    readonly_fields = ['restaurant_user', 'created_at', 'updated_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'customer_email',
        'restaurant_link',
        'overall_rating',
        'status_badge',
        'is_visible',
        'helpful_count',
        'has_response',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'is_visible',
        'overall_rating',
        'created_at',
        'visit_date'
    ]
    
    search_fields = [
        'customer__email',
        'restaurant__name',
        'title',
        'comment'
    ]
    
    readonly_fields = [
        'customer',
        'restaurant',
        'helpful_count',
        'moderated_at',
        'moderated_by',
        'created_at',
        'updated_at',
        'image1_preview',
        'image2_preview',
        'image3_preview'
    ]
    
    fieldsets = (
        ('Review Info', {
            'fields': (
                'customer',
                'restaurant',
                'visit_date',
                'status',
                'is_visible'
            )
        }),
        ('Ratings', {
            'fields': (
                'overall_rating',
                'food_rating',
                'service_rating',
                'atmosphere_rating',
                'value_rating'
            )
        }),
        ('Content', {
            'fields': (
                'title',
                'comment'
            )
        }),
        ('Photos', {
            'fields': (
                'image1',
                'image1_preview',
                'image2',
                'image2_preview',
                'image3',
                'image3_preview'
            )
        }),
        ('Moderation', {
            'fields': (
                'moderated_at',
                'moderated_by',
                'moderation_note'
            )
        }),
        ('Engagement', {
            'fields': ('helpful_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    inlines = [RestaurantResponseInline]
    
    actions = ['approve_reviews', 'reject_reviews', 'hide_reviews']
    
    def customer_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer.email)
    customer_email.short_description = 'Customer'
    
    def restaurant_link(self, obj):
        url = reverse('admin:restaurants_restaurant_change', args=[obj.restaurant.id])
        return format_html('<a href="{}">{}</a>', url, obj.restaurant.name)
    restaurant_link.short_description = 'Restaurant'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'flagged': 'darkred'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_response(self, obj):
        return hasattr(obj, 'restaurant_response')
    has_response.boolean = True
    has_response.short_description = 'Response'
    
    def image1_preview(self, obj):
        if obj.image1:
            return mark_safe(f'<img src="{obj.image1.url}" style="max-height: 150px;" />')
        return '-'
    image1_preview.short_description = 'Photo 1 Preview'
    
    def image2_preview(self, obj):
        if obj.image2:
            return mark_safe(f'<img src="{obj.image2.url}" style="max-height: 150px;" />')
        return '-'
    image2_preview.short_description = 'Photo 2 Preview'
    
    def image3_preview(self, obj):
        if obj.image3:
            return mark_safe(f'<img src="{obj.image3.url}" style="max-height: 150px;" />')
        return '-'
    image3_preview.short_description = 'Photo 3 Preview'
    
    def approve_reviews(self, request, queryset):
        count = 0
        for review in queryset:
            if review.status == Review.ReviewStatus.PENDING:
                review.approve(request.user)
                count += 1
        self.message_user(request, f'{count} reviews approved.')
    approve_reviews.short_description = 'Approve selected reviews'
    
    def reject_reviews(self, request, queryset):
        count = 0
        for review in queryset:
            review.reject(request.user)
            count += 1
        self.message_user(request, f'{count} reviews rejected.')
    reject_reviews.short_description = 'Reject selected reviews'
    
    def hide_reviews(self, request, queryset):
        count = queryset.update(is_visible=False)
        self.message_user(request, f'{count} reviews hidden.')
    hide_reviews.short_description = 'Hide selected reviews'


@admin.register(ReviewFlag)
class ReviewFlagAdmin(admin.ModelAdmin):
    list_display = [
        'review_link',
        'reporter_email',
        'reason',
        'resolved',
        'created_at'
    ]
    
    list_filter = ['reason', 'resolved', 'created_at']
    search_fields = ['review__id', 'reporter__email', 'description']
    
    readonly_fields = [
        'review',
        'reporter',
        'reason',
        'description',
        'created_at',
        'resolved_at',
        'resolved_by'
    ]
    
    actions = ['mark_resolved']
    
    def review_link(self, obj):
        url = reverse('admin:reviews_review_change', args=[obj.review.id])
        return format_html('<a href="{}">Review #{}</a>', url, obj.review.id)
    review_link.short_description = 'Review'
    
    def reporter_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.reporter.id])
        return format_html('<a href="{}">{}</a>', url, obj.reporter.email)
    reporter_email.short_description = 'Reporter'
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(
            resolved=True,
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        self.message_user(request, f'{count} flags marked as resolved.')
    mark_resolved.short_description = 'Mark selected flags as resolved'


@admin.register(RestaurantResponse)
class RestaurantResponseAdmin(admin.ModelAdmin):
    list_display = [
        'review_link',
        'restaurant_user_email',
        'response_preview',
        'created_at'
    ]
    
    list_filter = ['created_at']
    search_fields = ['review__id', 'restaurant_user__email', 'response']
    
    readonly_fields = ['review', 'restaurant_user', 'created_at', 'updated_at']
    
    def review_link(self, obj):
        url = reverse('admin:reviews_review_change', args=[obj.review.id])
        return format_html('<a href="{}">Review #{}</a>', url, obj.review.id)
    review_link.short_description = 'Review'
    
    def restaurant_user_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.restaurant_user.id])
        return format_html('<a href="{}">{}</a>', url, obj.restaurant_user.email)
    restaurant_user_email.short_description = 'Restaurant User'
    
    def response_preview(self, obj):
        return obj.response[:100] + '...' if len(obj.response) > 100 else obj.response
    response_preview.short_description = 'Response'
