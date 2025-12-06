from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import CustomUser, CustomerProfile, UserType
from .rbac_models import Organization, Region, Market, Role, Permission, UserRole


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


# ============================================
# ✅ RBAC Admin Interfaces
# ============================================

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Organization Admin (Singleton)"""
    
    list_display = ['name', 'slug', 'default_currency', 'support_email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'slug')}),
        ('Currencies', {'fields': ('default_currency', 'supported_currencies')}),
        ('Branding', {'fields': ('logo', 'primary_color')}),
        ('Contact', {'fields': ('support_email', 'support_phone')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def has_add_permission(self, request):
        # Only allow creating 1 organization
        return not Organization.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Cannot delete organization
        return False


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    """Region Admin"""
    
    list_display = [
        'name', 'code', 'default_language', 'currency',
        'is_active', 'launched_at'
    ]
    list_filter = ['is_active', 'default_language', 'currency']
    search_fields = ['name', 'code', 'support_email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {'fields': ('organization', 'name', 'code')}),
        ('Localization', {'fields': ('default_language', 'timezone', 'currency')}),
        ('Infrastructure', {'fields': ('cloudfront_distribution', 's3_bucket_region')}),
        ('Contact', {'fields': ('support_email', 'support_phone')}),
        ('Status', {'fields': ('is_active', 'launched_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    """Market Admin"""
    
    list_display = ['name', 'code', 'region', 'is_active']
    list_filter = ['region', 'is_active']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {'fields': ('region', 'name', 'code')}),
        ('Geographic', {'fields': ('latitude', 'longitude')}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


class RolePermissionInline(admin.TabularInline):
    """Inline for Role <-> Permission"""
    model = Role.permissions.through
    extra = 1
    verbose_name = 'Permission'
    verbose_name_plural = 'Permissions'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Role Admin"""
    
    list_display = [
        'display_name', 'name', 'scope_level',
        'is_active', 'is_system_role'
    ]
    list_filter = ['scope_level', 'is_active', 'is_system_role']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'display_name', 'description')}),
        ('Scope', {'fields': ('scope_level',)}),
        ('Status', {'fields': ('is_active', 'is_system_role')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    inlines = [RolePermissionInline]
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system_role:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Permission Admin"""
    
    list_display = [
        'resource', 'action', 'requires_global_scope', 'description'
    ]
    list_filter = ['resource', 'action', 'requires_global_scope']
    search_fields = ['resource', 'action', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Permission', {'fields': ('resource', 'action', 'description')}),
        ('Scope', {'fields': ('requires_global_scope',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """User Role Admin"""
    
    list_display = [
        'user_email', 'role_display', 'region', 'market',
        'is_active', 'expires_at', 'assigned_at'
    ]
    list_filter = ['role', 'region', 'is_active', 'assigned_at']
    search_fields = ['user__email', 'role__display_name']
    readonly_fields = ['assigned_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Assignment', {'fields': ('user', 'role', 'assigned_by')}),
        ('Scope', {'fields': ('region', 'market')}),
        ('Validity', {'fields': ('is_active', 'expires_at')}),
        ('Timestamps', {'fields': ('assigned_at', 'created_at', 'updated_at')}),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def role_display(self, obj):
        return obj.role.display_name
    role_display.short_description = 'Role'
    role_display.admin_order_field = 'role__display_name'

