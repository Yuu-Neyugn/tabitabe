"""
Campaign Admin Configuration
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    GiftCard,
    MyGiftCard,
    Stamprally,
    JoinShops,
    CustomerStamprally,
    Stamped,
    WinPrize
)


# ===== GIFT CARD ADMIN =====

@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'card_type',
        'price',
        'valid_from',
        'valid_until',
        'purchased_count',
        'remaining_count',
        'is_active'
    ]
    
    list_filter = ['card_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['title', 'description']
    
    filter_horizontal = ['applicable_restaurants']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'description',
                'card_type',
                'image'
            )
        }),
        ('Discount Values', {
            'fields': (
                'discount_percentage',
                'discount_amount',
                'price'
            )
        }),
        ('Validity', {
            'fields': (
                'valid_from',
                'valid_until'
            )
        }),
        ('Usage Restrictions', {
            'fields': (
                'min_purchase_amount',
                'max_uses_per_customer',
                'total_available',
                'applicable_restaurants'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )
    
    def purchased_count(self, obj):
        return obj.purchased_count
    purchased_count.short_description = 'Purchased'
    
    def remaining_count(self, obj):
        return obj.remaining_count
    remaining_count.short_description = 'Remaining'


@admin.register(MyGiftCard)
class MyGiftCardAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'customer_email',
        'giftcard_title',
        'status',
        'purchased_at',
        'used_at'
    ]
    
    list_filter = ['status', 'purchased_at', 'used_at']
    search_fields = ['code', 'customer__email', 'giftcard__title']
    
    readonly_fields = [
        'customer',
        'giftcard',
        'code',
        'purchase_price',
        'purchased_at',
        'used_at',
        'used_at_restaurant',
        'qr_code_preview'
    ]
    
    fieldsets = (
        ('Gift Card Info', {
            'fields': (
                'customer',
                'giftcard',
                'code',
                'status'
            )
        }),
        ('Purchase', {
            'fields': (
                'purchased_at',
                'purchase_price'
            )
        }),
        ('Usage', {
            'fields': (
                'used_at',
                'used_at_restaurant'
            )
        }),
        ('QR Code', {
            'fields': (
                'qr_code',
                'qr_code_preview'
            )
        })
    )
    
    def customer_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer.email)
    customer_email.short_description = 'Customer'
    
    def giftcard_title(self, obj):
        url = reverse('admin:campaigns_giftcard_change', args=[obj.giftcard.id])
        return format_html('<a href="{}">{}</a>', url, obj.giftcard.title)
    giftcard_title.short_description = 'Gift Card'
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return mark_safe(f'<img src="{obj.qr_code.url}" style="max-height: 150px;" />')
        return '-'
    qr_code_preview.short_description = 'QR Code Preview'


# ===== STAMP RALLY ADMIN =====

class JoinShopsInline(admin.TabularInline):
    model = JoinShops
    extra = 1


@admin.register(Stamprally)
class StamprallyAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'status',
        'start_date',
        'end_date',
        'required_stamps',
        'participants_count',
        'max_participants'
    ]
    
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['title', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'description',
                'status'
            )
        }),
        ('Duration', {
            'fields': (
                'start_date',
                'end_date'
            )
        }),
        ('Requirements', {
            'fields': (
                'required_stamps',
                'max_participants'
            )
        }),
        ('Prize', {
            'fields': (
                'prize_description',
                'prize_image'
            )
        }),
        ('Media', {
            'fields': ('banner_image',)
        })
    )
    
    inlines = [JoinShopsInline]
    
    def participants_count(self, obj):
        return obj.participants_count
    participants_count.short_description = 'Participants'


@admin.register(CustomerStamprally)
class CustomerStamprallyAdmin(admin.ModelAdmin):
    list_display = [
        'customer_email',
        'stamprally_title',
        'stamps_collected',
        'completed',
        'prize_received',
        'joined_at'
    ]
    
    list_filter = ['completed', 'prize_received', 'joined_at']
    search_fields = ['customer__email', 'stamprally__title']
    
    readonly_fields = [
        'customer',
        'stamprally',
        'joined_at',
        'completed',
        'completed_at',
        'prize_received',
        'prize_received_at'
    ]
    
    def customer_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer.email)
    customer_email.short_description = 'Customer'
    
    def stamprally_title(self, obj):
        url = reverse('admin:campaigns_stamprally_change', args=[obj.stamprally.id])
        return format_html('<a href="{}">{}</a>', url, obj.stamprally.title)
    stamprally_title.short_description = 'Stamp Rally'
    
    def stamps_collected(self, obj):
        return obj.stamps_collected
    stamps_collected.short_description = 'Stamps'


@admin.register(Stamped)
class StampedAdmin(admin.ModelAdmin):
    list_display = [
        'customer_email',
        'restaurant_name',
        'stamprally_title',
        'stamped_at',
        'verified_by_email'
    ]
    
    list_filter = ['stamped_at']
    search_fields = [
        'customer_stamprally__customer__email',
        'restaurant__name',
        'customer_stamprally__stamprally__title'
    ]
    
    readonly_fields = [
        'customer_stamprally',
        'restaurant',
        'stamped_at',
        'verified_by'
    ]
    
    def customer_email(self, obj):
        return obj.customer_stamprally.customer.email
    customer_email.short_description = 'Customer'
    
    def restaurant_name(self, obj):
        url = reverse('admin:restaurants_restaurant_change', args=[obj.restaurant.id])
        return format_html('<a href="{}">{}</a>', url, obj.restaurant.name)
    restaurant_name.short_description = 'Restaurant'
    
    def stamprally_title(self, obj):
        return obj.customer_stamprally.stamprally.title
    stamprally_title.short_description = 'Stamp Rally'
    
    def verified_by_email(self, obj):
        if obj.verified_by:
            url = reverse('admin:accounts_customuser_change', args=[obj.verified_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.verified_by.email)
        return '-'
    verified_by_email.short_description = 'Verified By'


@admin.register(WinPrize)
class WinPrizeAdmin(admin.ModelAdmin):
    list_display = [
        'customer_email',
        'stamprally_title',
        'awarded_at',
        'delivered',
        'delivered_at',
        'tracking_number'
    ]
    
    list_filter = ['delivered', 'awarded_at', 'delivered_at']
    search_fields = [
        'customer_stamprally__customer__email',
        'customer_stamprally__stamprally__title',
        'tracking_number'
    ]
    
    readonly_fields = ['customer_stamprally', 'prize_description', 'awarded_at']
    
    fieldsets = (
        ('Prize Info', {
            'fields': (
                'customer_stamprally',
                'prize_description',
                'awarded_at'
            )
        }),
        ('Delivery', {
            'fields': (
                'delivered',
                'delivered_at',
                'tracking_number'
            )
        })
    )
    
    def customer_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.customer_stamprally.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer_stamprally.customer.email)
    customer_email.short_description = 'Customer'
    
    def stamprally_title(self, obj):
        return obj.customer_stamprally.stamprally.title
    stamprally_title.short_description = 'Stamp Rally'
