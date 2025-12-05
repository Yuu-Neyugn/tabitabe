"""
Customer Admin Configuration
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    FavoriteRestaurant,
    CustomerPreference,
    CustomerSearchHistory,
    CustomerActivity
)


@admin.register(FavoriteRestaurant)
class FavoriteRestaurantAdmin(admin.ModelAdmin):
    list_display = ['customer_email', 'restaurant_link', 'created_at']
    list_filter = ['created_at']
    search_fields = ['customer__email', 'restaurant__name']
    readonly_fields = ['customer', 'restaurant', 'created_at', 'updated_at']
    
    def customer_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer.email)
    customer_email.short_description = 'Customer'
    
    def restaurant_link(self, obj):
        url = reverse('admin:restaurants_restaurant_change', args=[obj.restaurant.id])
        return format_html('<a href="{}">{}</a>', url, obj.restaurant.name)
    restaurant_link.short_description = 'Restaurant'


@admin.register(CustomerPreference)
class CustomerPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'customer_email',
        'email_notifications',
        'push_notifications',
        'marketing_emails',
        'language'
    ]
    
    list_filter = [
        'email_notifications',
        'push_notifications',
        'marketing_emails',
        'language'
    ]
    
    search_fields = ['customer__email']
    
    fieldsets = (
        ('Customer', {
            'fields': ('customer',)
        }),
        ('Notifications', {
            'fields': (
                'email_notifications',
                'push_notifications',
                'sms_notifications'
            )
        }),
        ('Marketing', {
            'fields': (
                'marketing_emails',
                'newsletter'
            )
        }),
        ('Privacy', {
            'fields': (
                'show_reviews_publicly',
                'share_location'
            )
        }),
        ('Display', {
            'fields': ('language',)
        })
    )
    
    def customer_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer.email)
    customer_email.short_description = 'Customer'


@admin.register(CustomerSearchHistory)
class CustomerSearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['customer_email', 'query', 'results_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['customer__email', 'query']
    readonly_fields = ['customer', 'query', 'filters_used', 'results_count', 'created_at', 'updated_at']
    
    def customer_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer.email)
    customer_email.short_description = 'Customer'
    
    def has_add_permission(self, request):
        return False


@admin.register(CustomerActivity)
class CustomerActivityAdmin(admin.ModelAdmin):
    list_display = [
        'customer_email',
        'activity_type',
        'restaurant_link',
        'created_at'
    ]
    
    list_filter = ['activity_type', 'created_at']
    search_fields = ['customer__email', 'restaurant__name']
    readonly_fields = ['customer', 'activity_type', 'restaurant', 'metadata', 'created_at', 'updated_at']
    
    def customer_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer.email)
    customer_email.short_description = 'Customer'
    
    def restaurant_link(self, obj):
        if obj.restaurant:
            url = reverse('admin:restaurants_restaurant_change', args=[obj.restaurant.id])
            return format_html('<a href="{}">{}</a>', url, obj.restaurant.name)
        return '-'
    restaurant_link.short_description = 'Restaurant'
    
    def has_add_permission(self, request):
        return False
