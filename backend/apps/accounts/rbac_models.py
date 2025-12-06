"""
RBAC Models: Role-Based Access Control
Organization → Region → Market → Role → Permission → UserRole
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    """Abstract base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField('Created At', auto_now_add=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)
    
    class Meta:
        abstract = True


class Organization(BaseModel):
    """
    Top-level entity (Tabitabe Inc.)
    Singleton - only 1 record allowed
    """
    name = models.CharField('Organization Name', max_length=200)
    slug = models.SlugField('Slug', unique=True, default='tabitabe')
    
    # Global settings
    default_currency = models.CharField('Default Currency', max_length=3, default='JPY')
    supported_currencies = models.JSONField(
        'Supported Currencies',
        default=list,
        help_text='List of supported currency codes (e.g., ["JPY", "USD", "VND"])'
    )
    
    # Branding
    logo = models.ImageField('Logo', upload_to='org/', null=True, blank=True)
    primary_color = models.CharField('Primary Color', max_length=7, default='#FF6B6B')
    
    # Contact
    support_email = models.EmailField('Support Email', default='support@tabitabe.com')
    support_phone = models.CharField('Support Phone', max_length=20, blank=True)
    
    class Meta:
        db_table = 'organization'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Singleton pattern - only 1 organization allowed
        if not self.pk and Organization.objects.exists():
            raise ValidationError("Only one Organization instance is allowed")
        super().save(*args, **kwargs)


class Region(BaseModel):
    """
    Regional divisions: Japan, Vietnam, Thailand
    Each region has independent admin team & settings
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='regions'
    )
    
    name = models.CharField('Region Name', max_length=100)  # 'Japan', 'Vietnam'
    code = models.CharField('Region Code', max_length=10, unique=True)  # 'JP', 'VN'
    
    # Localization
    default_language = models.CharField('Default Language', max_length=10, default='ja')
    timezone = models.CharField('Timezone', max_length=50, default='Asia/Tokyo')
    currency = models.CharField('Currency', max_length=3, default='JPY')
    
    # Infrastructure (for future multi-region deployment)
    cloudfront_distribution = models.CharField(
        'CloudFront Distribution ID',
        max_length=100,
        blank=True,
        help_text='AWS CloudFront distribution for this region'
    )
    s3_bucket_region = models.CharField(
        'S3 Bucket Region',
        max_length=50,
        default='ap-northeast-1'
    )
    
    # Contact
    support_email = models.EmailField('Support Email')
    support_phone = models.CharField('Support Phone', max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField('Active', default=True)
    launched_at = models.DateField('Launch Date', null=True, blank=True)
    
    class Meta:
        db_table = 'regions'
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Market(BaseModel):
    """
    Sub-regions or cities within a region (Optional)
    Example: Tokyo, Osaka, Kyoto within Japan region
    """
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='markets'
    )
    
    name = models.CharField('Market Name', max_length=100)  # 'Tokyo', 'Osaka'
    code = models.CharField('Market Code', max_length=20)  # 'JP-TKY', 'JP-OSA'
    
    # Geographic center (for distance calculations)
    latitude = models.DecimalField(
        'Latitude',
        max_digits=10,
        decimal_places=8,
        help_text='Market center latitude'
    )
    longitude = models.DecimalField(
        'Longitude',
        max_digits=11,
        decimal_places=8,
        help_text='Market center longitude'
    )
    
    # Status
    is_active = models.BooleanField('Active', default=True)
    
    class Meta:
        db_table = 'markets'
        verbose_name = 'Market'
        verbose_name_plural = 'Markets'
        unique_together = [['region', 'code']]
        ordering = ['region', 'name']
        indexes = [
            models.Index(fields=['region', 'is_active']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Role(BaseModel):
    """
    Role definitions with scope levels
    System roles that define user permissions and access levels
    """
    
    class RoleType(models.TextChoices):
        # === GLOBAL ADMIN ROLES ===
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        GLOBAL_OPERATIONS = 'global_operations', 'Global Operations Manager'
        
        # === REGIONAL ADMIN ROLES ===
        REGION_ADMIN = 'region_admin', 'Regional Admin'
        RESTAURANT_APPROVAL_SPECIALIST = 'restaurant_approval_specialist', 'Restaurant Approval Specialist'
        CONTENT_MODERATOR = 'content_moderator', 'Content Moderator'
        CUSTOMER_SUPPORT_AGENT = 'customer_support_agent', 'Customer Support Agent'
        CAMPAIGN_MANAGER = 'campaign_manager', 'Campaign Manager'
        
        # === GOVERNMENT ROLES ===
        GOVERNMENT_ADMIN = 'government_admin', 'Government Administrator'
        GOVERNMENT_ANALYST = 'government_analyst', 'Government Analyst'
        
        # === RESTAURANT ROLES ===
        RESTAURANT_OWNER = 'restaurant_owner', 'Restaurant Owner'
        RESTAURANT_MANAGER = 'restaurant_manager', 'Restaurant Manager'
        RESTAURANT_STAFF = 'restaurant_staff', 'Restaurant Staff'
        RESTAURANT_VIEWER = 'restaurant_viewer', 'Restaurant Viewer'
        
        # === ADVERTISER ROLES (Phase 3) ===
        ADVERTISER_ENTERPRISE = 'advertiser_enterprise', 'Enterprise Advertiser'
        ADVERTISER_PREMIUM = 'advertiser_premium', 'Premium Advertiser'
        ADVERTISER_BASIC = 'advertiser_basic', 'Basic Advertiser'
        
        # === CUSTOMER ROLES ===
        CUSTOMER_PREMIUM_PLUS = 'customer_premium_plus', 'Premium Plus Customer'
        CUSTOMER_PREMIUM = 'customer_premium', 'Premium Customer'
        CUSTOMER_FREE = 'customer_free', 'Free Customer'
    
    class ScopeLevel(models.TextChoices):
        GLOBAL = 'global', 'Global'      # Access all regions
        REGION = 'region', 'Regional'    # Access one region
        MARKET = 'market', 'Market'      # Access one market/city
        ENTITY = 'entity', 'Entity'      # Access own entity only (restaurant/customer)
    
    name = models.CharField(
        'Role Name',
        max_length=50,
        choices=RoleType.choices,
        unique=True
    )
    display_name = models.CharField('Display Name', max_length=100)
    description = models.TextField('Description', blank=True)
    
    # Scope requirement
    scope_level = models.CharField(
        'Scope Level',
        max_length=20,
        choices=ScopeLevel.choices,
        default=ScopeLevel.ENTITY,
        help_text='Defines the access scope for this role'
    )
    
    # Permissions (ManyToMany)
    permissions = models.ManyToManyField(
        'Permission',
        related_name='roles',
        blank=True
    )
    
    # Status
    is_active = models.BooleanField('Active', default=True)
    is_system_role = models.BooleanField(
        'System Role',
        default=True,
        help_text='System roles cannot be deleted'
    )
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['display_name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.display_name


class Permission(BaseModel):
    """
    Granular permissions (resource + action)
    Defines what actions can be performed on which resources
    """
    
    class Resource(models.TextChoices):
        # System
        ORGANIZATION = 'organization', 'Organization Settings'
        REGION = 'region', 'Region Management'
        ROLE = 'role', 'Role Management'
        USER = 'user', 'User Management'
        
        # Business
        RESTAURANT = 'restaurant', 'Restaurant'
        REVIEW = 'review', 'Review'
        CAMPAIGN = 'campaign', 'Campaign'
        GOVERNMENT_CAMPAIGN = 'government_campaign', 'Government Campaign'
        ADVERTISEMENT = 'advertisement', 'Advertisement'
        
        # Gamification
        BADGE = 'badge', 'Badge'
        LEADERBOARD = 'leaderboard', 'Leaderboard'
        CHECKIN = 'checkin', 'Check-in'
        
        # Analytics
        ANALYTICS = 'analytics', 'Analytics'
        FINANCIAL = 'financial', 'Financial Reports'
        AUDIT_LOG = 'audit_log', 'Audit Log'
    
    class Action(models.TextChoices):
        VIEW = 'view', 'View'
        CREATE = 'create', 'Create'
        EDIT = 'edit', 'Edit'
        DELETE = 'delete', 'Delete'
        APPROVE = 'approve', 'Approve'
        MODERATE = 'moderate', 'Moderate'
        EXPORT = 'export', 'Export Data'
        ASSIGN = 'assign', 'Assign'
    
    resource = models.CharField(
        'Resource',
        max_length=50,
        choices=Resource.choices
    )
    action = models.CharField(
        'Action',
        max_length=20,
        choices=Action.choices
    )
    description = models.CharField('Description', max_length=200, blank=True)
    
    # Scope requirements
    requires_global_scope = models.BooleanField(
        'Requires Global Scope',
        default=False,
        help_text='If True, permission requires GLOBAL scope level'
    )
    
    class Meta:
        db_table = 'permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        unique_together = [['resource', 'action']]
        ordering = ['resource', 'action']
        indexes = [
            models.Index(fields=['resource', 'action']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} {self.get_resource_display()}"


class UserRole(BaseModel):
    """
    Through model for User ↔ Role relationship with scope
    Defines which users have which roles and in what scope (region/market)
    """
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    
    # Scope constraints (optional, depends on role's scope_level)
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Required if role scope is REGION or MARKET'
    )
    
    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Required if role scope is MARKET'
    )
    
    # Assignment metadata
    assigned_at = models.DateTimeField('Assigned At', auto_now_add=True)
    assigned_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_user_roles',
        help_text='Admin who assigned this role'
    )
    
    # Optional: Role expiry (for temporary access)
    expires_at = models.DateTimeField(
        'Expires At',
        null=True,
        blank=True,
        help_text='If set, role will expire after this date'
    )
    
    is_active = models.BooleanField('Active', default=True)
    
    class Meta:
        db_table = 'user_roles'
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
        unique_together = [['user', 'role', 'region', 'market']]
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['role', 'region']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        scope = ''
        if self.region:
            scope = f" ({self.region.code})"
        elif self.market:
            scope = f" ({self.market.code})"
        return f"{self.user.email} - {self.role.name}{scope}"
    
    def clean(self):
        """Validate scope matches role requirements"""
        if self.role.scope_level == Role.ScopeLevel.REGION:
            if not self.region:
                raise ValidationError("Region-scoped role requires region")
            if self.market:
                raise ValidationError("Region-scoped role cannot have market")
        
        if self.role.scope_level == Role.ScopeLevel.MARKET:
            if not self.market:
                raise ValidationError("Market-scoped role requires market")
            if not self.region:
                raise ValidationError("Market-scoped role requires region")
        
        if self.role.scope_level == Role.ScopeLevel.GLOBAL:
            if self.region or self.market:
                raise ValidationError("Global-scoped role cannot have region/market")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if role assignment has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
