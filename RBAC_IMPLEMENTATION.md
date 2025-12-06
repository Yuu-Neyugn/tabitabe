# 🔐 RBAC Architecture & Implementation Plan

> **Critical Refactoring**: Migrate from `user_type` (integer) to Role-Based Access Control  
> **Priority**: HIGH - Must complete before Advertiser & Government features  
> **Timeline**: 5-6 days implementation

---

## 🚨 Why RBAC is MANDATORY

### Current Problem (user_type system)

```python
class UserType(models.IntegerChoices):
    ADMIN = 0          # ❌ Cannot differentiate: Super Admin, Regional Admin, Moderator, Support Agent
    CUSTOMER = 1       # ❌ Cannot differentiate: Free, Premium, Premium Plus
    RESTAURANT = 2     # ❌ Cannot differentiate: Owner, Manager, Staff, Viewer
    # ❌ Where does GOVERNMENT fit?
    # ❌ Where does ADVERTISER (Basic/Premium/Enterprise) fit?
    # ❌ How to handle region-scoped permissions?
```

### Consequences of NOT migrating:

- ❌ **Cannot implement Government user type** → B2G revenue stream impossible
- ❌ **Cannot differentiate admin staff roles** → Manual workload distribution nightmare at scale
- ❌ **Cannot implement restaurant teams** → Owners can't delegate to staff
- ❌ **Cannot implement customer tiers** → Freemium model impossible
- ❌ **Cannot scale to multi-region** → Each region needs scoped admin access

---

## ✅ RBAC Solution Architecture

### 1. Core Models

```python
# backend/apps/accounts/models.py

from django.db import models
from django.core.exceptions import ValidationError

class Organization(BaseModel):
    """
    Top-level entity (Tabitabe Inc.)
    Singleton - only 1 record
    """
    name = models.CharField('Organization Name', max_length=200)
    slug = models.SlugField('Slug', unique=True, default='tabitabe')
    
    # Global settings
    default_currency = models.CharField('Default Currency', max_length=3, default='JPY')
    supported_currencies = models.JSONField('Supported Currencies', default=list)
    
    # Branding
    logo = models.ImageField('Logo', upload_to='org/', null=True)
    primary_color = models.CharField('Primary Color', max_length=7, default='#FF6B6B')
    
    class Meta:
        db_table = 'organization'
    
    def save(self, *args, **kwargs):
        # Singleton pattern - only 1 organization allowed
        if not self.pk and Organization.objects.exists():
            raise ValidationError("Only one Organization instance allowed")
        super().save(*args, **kwargs)


class Region(BaseModel):
    """
    Regional divisions: Japan, Vietnam, Thailand
    Each region has independent admin team & settings
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    
    name = models.CharField('Region Name', max_length=100)  # 'Japan', 'Vietnam'
    code = models.CharField('Region Code', max_length=10, unique=True)  # 'JP', 'VN'
    
    # Localization
    default_language = models.CharField('Default Language', max_length=10, default='ja')
    timezone = models.CharField('Timezone', max_length=50, default='Asia/Tokyo')
    currency = models.CharField('Currency', max_length=3, default='JPY')
    
    # Infrastructure
    cloudfront_distribution = models.CharField('CloudFront Distribution ID', max_length=100, blank=True)
    s3_bucket_region = models.CharField('S3 Bucket Region', max_length=50, default='ap-northeast-1')
    
    # Contact
    support_email = models.EmailField('Support Email')
    support_phone = models.CharField('Support Phone', max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField('Active', default=True)
    launched_at = models.DateField('Launch Date', null=True, blank=True)
    
    class Meta:
        db_table = 'regions'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Market(BaseModel):
    """
    Sub-regions or cities within a region (Optional)
    Example: Tokyo, Osaka, Kyoto within Japan region
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='markets')
    
    name = models.CharField('Market Name', max_length=100)  # 'Tokyo', 'Osaka'
    code = models.CharField('Market Code', max_length=20)  # 'JP-TKY', 'JP-OSA'
    
    # Geographic center
    latitude = models.DecimalField('Latitude', max_digits=10, decimal_places=8)
    longitude = models.DecimalField('Longitude', max_digits=11, decimal_places=8)
    
    is_active = models.BooleanField('Active', default=True)
    
    class Meta:
        db_table = 'markets'
        unique_together = [['region', 'code']]
        ordering = ['region', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Role(BaseModel):
    """
    Role definitions with scope levels
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
        ENTITY = 'entity', 'Entity'      # Access own entity only
    
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
        default=ScopeLevel.ENTITY
    )
    
    # Permissions
    permissions = models.ManyToManyField('Permission', related_name='roles', blank=True)
    
    # Status
    is_active = models.BooleanField('Active', default=True)
    is_system_role = models.BooleanField('System Role', default=True, help_text='Cannot be deleted')
    
    class Meta:
        db_table = 'roles'
        ordering = ['display_name']
    
    def __str__(self):
        return self.display_name


class Permission(BaseModel):
    """
    Granular permissions (resource + action)
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
    requires_global_scope = models.BooleanField('Requires Global Scope', default=False)
    
    class Meta:
        db_table = 'permissions'
        unique_together = [['resource', 'action']]
        ordering = ['resource', 'action']
    
    def __str__(self):
        return f"{self.get_action_display()} {self.get_resource_display()}"


class CustomUser(AbstractUser):
    """
    Enhanced User model with RBAC support
    """
    
    # Remove username field
    username = None
    
    # Primary identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('Email Address', unique=True, db_index=True)
    
    # ✅ NEW: Multiple roles per user
    roles = models.ManyToManyField(
        Role,
        through='UserRole',
        related_name='users',
        blank=True
    )
    
    # ⚠️ DEPRECATED: Keep for backward compatibility during migration
    user_type = models.IntegerField(
        'User Type (DEPRECATED)',
        null=True,
        blank=True,
        help_text='Legacy field. Use roles instead. Will be removed in v2.0'
    )
    
    # OIDC fields
    oidc_subject = models.CharField(
        'OIDC Subject (sub)',
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    
    # ... rest of fields
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    # ✅ NEW: Role checking methods
    def has_role(self, role_name):
        """Check if user has specific role"""
        return self.roles.filter(
            name=role_name,
            userrole__is_active=True
        ).exists()
    
    def has_permission(self, resource, action):
        """Check if user has permission for resource + action"""
        return Permission.objects.filter(
            roles__users=self,
            resource=resource,
            action=action,
            roles__userrole__is_active=True
        ).exists()
    
    def get_active_roles(self):
        """Get all active roles for user"""
        from django.utils import timezone
        now = timezone.now()
        
        return self.roles.filter(
            userrole__is_active=True
        ).filter(
            models.Q(userrole__expires_at__isnull=True) |
            models.Q(userrole__expires_at__gt=now)
        ).distinct()
    
    # Convenience properties
    @property
    def is_super_admin(self):
        return self.has_role(Role.RoleType.SUPER_ADMIN)
    
    @property
    def is_government(self):
        return self.has_role(Role.RoleType.GOVERNMENT_ADMIN) or \
               self.has_role(Role.RoleType.GOVERNMENT_ANALYST)
    
    @property
    def is_restaurant_owner(self):
        return self.has_role(Role.RoleType.RESTAURANT_OWNER)
    
    @property
    def is_customer_premium(self):
        return self.has_role(Role.RoleType.CUSTOMER_PREMIUM) or \
               self.has_role(Role.RoleType.CUSTOMER_PREMIUM_PLUS)


class UserRole(BaseModel):
    """
    Through model for User ↔ Role relationship with scope
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    
    # Scope constraints (optional, depends on role's scope_level)
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Required if role scope is REGION'
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
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_user_roles'
    )
    
    # Optional: Role expiry (for temporary access)
    expires_at = models.DateTimeField('Expires At', null=True, blank=True)
    
    is_active = models.BooleanField('Active', default=True)
    
    class Meta:
        db_table = 'user_roles'
        unique_together = [['user', 'role', 'region', 'market']]
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['role', 'region']),
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
        if self.role.scope_level == Role.ScopeLevel.REGION and not self.region:
            raise ValidationError("Region-scoped role requires region")
        
        if self.role.scope_level == Role.ScopeLevel.MARKET and not self.market:
            raise ValidationError("Market-scoped role requires market")
        
        if self.role.scope_level == Role.ScopeLevel.GLOBAL:
            if self.region or self.market:
                raise ValidationError("Global-scoped role cannot have region/market")
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at
```

---

## 📋 Migration Plan (5-6 Days)

### Day 1-2: Create New Models

**Tasks:**
1. Create Organization, Region, Market models
2. Create Role, Permission models
3. Create UserRole through model
4. Update CustomUser (add roles ManyToMany, deprecate user_type)
5. Write migrations

**Deliverables:**
- ✅ All new models created
- ✅ Migrations generated
- ✅ Models registered in admin

### Day 3: Data Migration

**Tasks:**
1. Create initial data migration
2. Seed roles and permissions
3. Migrate existing users from user_type → roles
4. Create default regions (Japan)

```python
# Migration script pseudocode
def migrate_user_types_to_roles(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    Role = apps.get_model('accounts', 'Role')
    UserRole = apps.get_model('accounts', 'UserRole')
    
    # Get roles
    customer_free = Role.objects.get(name='customer_free')
    restaurant_owner = Role.objects.get(name='restaurant_owner')
    super_admin = Role.objects.get(name='super_admin')
    
    # Migrate users
    for user in CustomUser.objects.all():
        if user.user_type == 0:  # ADMIN
            UserRole.objects.create(user=user, role=super_admin)
        elif user.user_type == 1:  # CUSTOMER
            UserRole.objects.create(user=user, role=customer_free)
        elif user.user_type == 2:  # RESTAURANT
            UserRole.objects.create(user=user, role=restaurant_owner)
```

**Deliverables:**
- ✅ Data successfully migrated
- ✅ All existing users have roles assigned
- ✅ No data loss

### Day 4: Update Permission Classes

**Tasks:**
1. Create new DRF permission classes using RBAC
2. Replace old `user_type` checks with `has_role()` checks
3. Update existing viewsets
4. Add region-scoped filtering

```python
# New permission class
class HasRolePermission(permissions.BasePermission):
    required_roles = []
    required_permission = None
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check role
        if self.required_roles:
            user_roles = request.user.get_active_roles().values_list('name', flat=True)
            if not any(role in user_roles for role in self.required_roles):
                return False
        
        # Check permission
        if self.required_permission:
            resource, action = self.required_permission
            if not request.user.has_permission(resource, action):
                return False
        
        return True

class IsRestaurantOwner(HasRolePermission):
    required_roles = [Role.RoleType.RESTAURANT_OWNER]

class IsGovernmentOfficial(HasRolePermission):
    required_roles = [
        Role.RoleType.GOVERNMENT_ADMIN,
        Role.RoleType.GOVERNMENT_ANALYST
    ]
```

**Deliverables:**
- ✅ All permission classes updated
- ✅ Backward compatibility maintained

### Day 5: Update Tests

**Tasks:**
1. Update existing tests (17 admin tests)
2. Add new RBAC-specific tests
3. Test role assignment/removal
4. Test scope filtering

**Deliverables:**
- ✅ All 17+ existing tests passing
- ✅ 10+ new RBAC tests added
- ✅ Test coverage > 75%

### Day 6: Documentation & Cleanup

**Tasks:**
1. Update API documentation (Swagger/drf-spectacular)
2. Add migration guide for API consumers
3. Mark user_type as deprecated (add warnings)
4. Update README

**Deliverables:**
- ✅ Documentation complete
- ✅ Deprecation warnings in place
- ✅ README updated

---

## ✅ Validation Checklist

- [ ] All models created and migrated
- [ ] Existing users migrated to roles (no data loss)
- [ ] All existing tests passing
- [ ] New RBAC tests added (10+)
- [ ] Permission classes updated
- [ ] API endpoints working with new RBAC
- [ ] Documentation updated
- [ ] Backward compatibility maintained (user_type still works but deprecated)
- [ ] Admin interface shows roles correctly
- [ ] Region-scoped permissions working

---

**Ready to implement? Confirm and I'll start with Day 1!** 🚀
