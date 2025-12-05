from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import CustomUser, CustomerProfile, UserType


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    
    list_display = [
        'email', 'user_type_badge', 'is_active', 
        'is_staff', 'is_email_verified', 'date_joined'
    ]
    list_filter = ['user_type', 'is_active', 'is_staff', 'is_email_verified', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'oidc_subject']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('User Type', {'fields': ('user_type',)}),
        ('OIDC', {'fields': ('oidc_subject',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'password_changed_at')}),
        ('Metadata', {'fields': ('is_email_verified', 'last_login_ip')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type'),
        }),
    )
    
    def user_type_badge(self, obj):
        """Display user type as colored badge"""
        colors = {
            UserType.CUSTOMER: '#10b981',
            UserType.RESTAURANT: '#f59e0b',
            UserType.ADMIN: '#ef4444',
        }
        color = colors.get(obj.user_type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 12px;">{}</span>',
            color,
            obj.get_user_type_display()
        )
    user_type_badge.short_description = 'Type'


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """Customer Profile Admin"""
    
    list_display = [
        'customer_number', 'user_email', 'phone_number',
        'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'language', 'created_at']
    search_fields = [
        'customer_number', 'user__email', 'phone_number',
        'prefecture', 'city'
    ]
    readonly_fields = ['customer_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User', {'fields': ('user', 'customer_number')}),
        ('Contact', {'fields': ('phone_number',)}),
        ('Personal', {'fields': ('birth_date', 'avatar', 'bio')}),
        ('Address', {
            'fields': ('postal_code', 'prefecture', 'city', 'address_line')
        }),
        ('Preferences', {
            'fields': ('language', 'receive_newsletter', 'receive_push_notifications')
        }),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
