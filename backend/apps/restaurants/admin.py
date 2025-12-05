"""
Restaurant Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Restaurant,
    ClosedDay,
    Cuisine,
    RestaurantCuisine,
    Product,
    RestaurantView,
    RestaurantStatus
)


class ClosedDayInline(admin.TabularInline):
    model = ClosedDay
    extra = 1
    verbose_name = 'Closed Day'
    verbose_name_plural = 'Closed Days'


class RestaurantCuisineInline(admin.TabularInline):
    model = RestaurantCuisine
    extra = 1
    verbose_name = 'Cuisine'
    verbose_name_plural = 'Cuisines'


class ProductInline(admin.StackedInline):
    model = Product
    extra = 0
    fields = ['name', 'name_en', 'price', 'is_available', 'is_featured', 'display_order']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'status_badge',
        'user_email',
        'phone_number',
        'prefecture',
        'city',
        'is_visible',
        'average_rating',
        'total_reviews',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'is_visible',
        'is_active',
        'prefecture',
        'has_parking',
        'has_wifi',
        'accepts_reservations',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'name_en',
        'user__email',
        'phone_number',
        'address_line',
        'city'
    ]
    
    readonly_fields = [
        'user',
        'approved_at',
        'approved_by',
        'total_reviews',
        'average_rating',
        'total_views',
        'created_at',
        'updated_at',
        'logo_preview',
        'cover_preview'
    ]
    
    fieldsets = (
        ('User & Status', {
            'fields': (
                'user',
                'status',
                'is_visible',
                'is_active',
                'approved_at',
                'approved_by',
                'rejection_reason'
            )
        }),
        ('Basic Information', {
            'fields': (
                'name',
                'name_en',
                'description',
                'description_en'
            )
        }),
        ('Contact', {
            'fields': (
                'phone_number',
                'email',
                'website',
                'facebook_url',
                'instagram_url',
                'twitter_url',
                'line_id'
            )
        }),
        ('Location', {
            'fields': (
                'postal_code',
                'prefecture',
                'city',
                'address_line',
                'building',
                'latitude',
                'longitude'
            )
        }),
        ('Operating Hours', {
            'fields': (
                'opening_time',
                'closing_time'
            )
        }),
        ('Features', {
            'fields': (
                'seating_capacity',
                'has_parking',
                'has_wifi',
                'is_smoking_allowed',
                'accepts_reservations'
            )
        }),
        ('Media', {
            'fields': (
                'logo',
                'logo_preview',
                'cover_image',
                'cover_preview',
                'interior_image1',
                'interior_image2',
                'interior_image3'
            )
        }),
        ('Statistics', {
            'fields': (
                'total_reviews',
                'average_rating',
                'total_views'
            )
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    inlines = [ClosedDayInline, RestaurantCuisineInline, ProductInline]
    
    actions = ['approve_restaurants', 'reject_restaurants', 'suspend_restaurants']
    
    def user_email(self, obj):
        """Display user email with link"""
        url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User Email'
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            RestaurantStatus.DRAFT: 'gray',
            RestaurantStatus.PENDING: 'orange',
            RestaurantStatus.APPROVED: 'green',
            RestaurantStatus.REJECTED: 'red',
            RestaurantStatus.SUSPENDED: 'darkred'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def logo_preview(self, obj):
        """Display logo preview"""
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" style="max-height: 100px;" />')
        return '-'
    logo_preview.short_description = 'Logo Preview'
    
    def cover_preview(self, obj):
        """Display cover image preview"""
        if obj.cover_image:
            return mark_safe(f'<img src="{obj.cover_image.url}" style="max-width: 300px;" />')
        return '-'
    cover_preview.short_description = 'Cover Preview'
    
    def approve_restaurants(self, request, queryset):
        """Bulk approve restaurants"""
        count = 0
        for restaurant in queryset:
            if restaurant.can_be_approved():
                restaurant.approve(request.user)
                count += 1
        self.message_user(request, f'{count} restaurants approved successfully.')
    approve_restaurants.short_description = 'Approve selected restaurants'
    
    def reject_restaurants(self, request, queryset):
        """Bulk reject restaurants"""
        count = queryset.update(
            status=RestaurantStatus.REJECTED,
            is_visible=False
        )
        self.message_user(request, f'{count} restaurants rejected.')
    reject_restaurants.short_description = 'Reject selected restaurants'
    
    def suspend_restaurants(self, request, queryset):
        """Bulk suspend restaurants"""
        count = queryset.update(
            status=RestaurantStatus.SUSPENDED,
            is_visible=False,
            is_active=False
        )
        self.message_user(request, f'{count} restaurants suspended.')
    suspend_restaurants.short_description = 'Suspend selected restaurants'


@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'slug', 'display_order', 'restaurant_count']
    search_fields = ['name', 'name_en']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['display_order']
    
    def restaurant_count(self, obj):
        """Count restaurants with this cuisine"""
        return obj.restaurant_cuisines.count()
    restaurant_count.short_description = 'Restaurants'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'restaurant_link',
        'price',
        'is_available',
        'is_featured',
        'display_order',
        'created_at'
    ]
    
    list_filter = [
        'is_available',
        'is_featured',
        'restaurant',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'name_en',
        'restaurant__name',
        'description'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'restaurant',
                'name',
                'name_en',
                'description',
                'description_en',
                'price'
            )
        }),
        ('Display', {
            'fields': (
                'image',
                'image_preview',
                'is_available',
                'is_featured',
                'display_order'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def restaurant_link(self, obj):
        """Display restaurant name with link"""
        url = reverse('admin:restaurants_restaurant_change', args=[obj.restaurant.id])
        return format_html('<a href="{}">{}</a>', url, obj.restaurant.name)
    restaurant_link.short_description = 'Restaurant'
    
    def image_preview(self, obj):
        """Display product image preview"""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 150px;" />')
        return '-'
    image_preview.short_description = 'Image Preview'


@admin.register(RestaurantView)
class RestaurantViewAdmin(admin.ModelAdmin):
    list_display = [
        'restaurant',
        'user_info',
        'ip_address',
        'created_at'
    ]
    
    list_filter = [
        'restaurant',
        'created_at'
    ]
    
    search_fields = [
        'restaurant__name',
        'user__email',
        'ip_address'
    ]
    
    readonly_fields = ['restaurant', 'user', 'ip_address', 'user_agent', 'created_at', 'updated_at']
    
    def user_info(self, obj):
        """Display user email or IP"""
        if obj.user:
            url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return obj.ip_address or 'Anonymous'
    user_info.short_description = 'User/IP'
    
    def has_add_permission(self, request):
        """Disable manual creation"""
        return False
