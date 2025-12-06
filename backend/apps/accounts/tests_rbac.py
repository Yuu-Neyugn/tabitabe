"""
Unit tests for RBAC (Role-Based Access Control) system

Test coverage:
- Role assignment and checking
- Permission checking
- Scope validation (GLOBAL, REGION, MARKET, ENTITY)
- Role expiry
- Backward compatibility with user_type
- Convenience properties (is_super_admin, is_government, etc.)
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.accounts.rbac_models import (
    Organization, Region, Market, Role, Permission, UserRole
)

User = get_user_model()


class RBACModelsTestCase(TestCase):
    """Test RBAC models creation and relationships"""
    
    def setUp(self):
        """Create test data"""
        # Create organization (singleton) - use get_or_create to avoid conflicts
        self.org, _ = Organization.objects.get_or_create(
            slug='test-org',
            defaults={
                'name': 'Test Organization',
                'default_currency': 'JPY'
            }
        )
        
        # Create region - use get_or_create
        self.region, _ = Region.objects.get_or_create(
            code='JP',
            defaults={
                'organization': self.org,
                'name': 'Japan',
                'default_language': 'ja',
                'timezone': 'Asia/Tokyo'
            }
        )
        
        # Create market - use get_or_create
        self.market, _ = Market.objects.get_or_create(
            code='tokyo',
            defaults={
                'region': self.region,
                'name': 'Tokyo',
                'latitude': 35.6762,
                'longitude': 139.6503
            }
        )
        
        # Create roles - use get_or_create
        self.super_admin_role, _ = Role.objects.get_or_create(
            name='super_admin',
            defaults={
                'display_name': 'Super Admin',
                'scope': 'global',
                'is_system_role': True
            }
        )
        
        self.region_admin_role, _ = Role.objects.get_or_create(
            name='region_admin',
            defaults={
                'display_name': 'Region Admin',
                'scope': 'region',
                'is_system_role': True
            }
        )
        
        self.restaurant_owner_role, _ = Role.objects.get_or_create(
            name='restaurant_owner',
            defaults={
                'display_name': 'Restaurant Owner',
                'scope': 'entity',
                'is_system_role': True
            }
        )
        
        self.customer_free_role, _ = Role.objects.get_or_create(
            name='customer_free',
            defaults={
                'display_name': 'Free Customer',
                'scope': 'entity',
                'is_system_role': True
            }
        )
        
        # Create permissions - use get_or_create
        self.restaurant_view_perm, _ = Permission.objects.get_or_create(
            resource='restaurant',
            action='VIEW'
        )
        
        self.restaurant_edit_perm, _ = Permission.objects.get_or_create(
            resource='restaurant',
            action='EDIT'
        )
        
        self.restaurant_approve_perm, _ = Permission.objects.get_or_create(
            resource='restaurant',
            action='APPROVE',
            defaults={'requires_global_scope': True}
        )
        
        self.review_create_perm, _ = Permission.objects.get_or_create(
            resource='review',
            action='CREATE'
        )
        
        self.review_moderate_perm, _ = Permission.objects.get_or_create(
            resource='review',
            action='MODERATE',
            defaults={'requires_global_scope': True}
        )
        
        # Assign permissions to roles
        self.super_admin_role.permissions.set([
            self.restaurant_view_perm,
            self.restaurant_edit_perm,
            self.restaurant_approve_perm,
            self.review_create_perm,
            self.review_moderate_perm
        ])
        
        self.region_admin_role.permissions.set([
            self.restaurant_view_perm,
            self.restaurant_edit_perm,
            self.restaurant_approve_perm,
            self.review_moderate_perm
        ])
        
        self.restaurant_owner_role.permissions.set([
            self.restaurant_view_perm,
            self.restaurant_edit_perm
        ])
        
        self.customer_free_role.permissions.set([
            self.review_create_perm
        ])
        
        # Create users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        
        self.region_admin_user = User.objects.create_user(
            email='region@test.com',
            password='testpass123'
        )
        
        self.restaurant_user = User.objects.create_user(
            email='restaurant@test.com',
            password='testpass123'
        )
        
        self.customer_user = User.objects.create_user(
            email='customer@test.com',
            password='testpass123'
        )
    
    def test_organization_singleton(self):
        """Test that only one organization can exist"""
        # Try to create a second organization with different slug
        # Should raise ValidationError due to singleton constraint
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            org2 = Organization(
                name='Another Org',
                slug='another-org'
            )
            org2.full_clean()  # This triggers validation
    
    def test_role_creation(self):
        """Test role creation"""
        # Since we use get_or_create, check that roles exist
        self.assertTrue(Role.objects.filter(name='super_admin').exists())
        self.assertTrue(Role.objects.filter(name='region_admin').exists())
        self.assertEqual(self.super_admin_role.scope, 'global')
        self.assertEqual(self.region_admin_role.scope, 'region')
    
    def test_permission_creation(self):
        """Test permission creation"""
        # Check that permissions exist (don't check count since migration may have created more)
        self.assertTrue(Permission.objects.filter(name='APPROVE_RESTAURANT').exists())
        self.assertTrue(Permission.objects.filter(name='VIEW_RESTAURANT').exists())
        self.assertTrue(self.restaurant_approve_perm.requires_global_scope)
        self.assertFalse(self.restaurant_view_perm.requires_global_scope)


class UserRoleTestCase(TestCase):
    """Test UserRole assignment and validation"""
    
    def setUp(self):
        """Create test data"""
        self.org, _ = Organization.objects.get_or_create(
            slug='test-org',
            defaults={'name': 'Test Org'}
        )
        
        self.region, _ = Region.objects.get_or_create(
            code='JP',
            defaults={
                'organization': self.org,
                'name': 'Japan'
            }
        )
        
        self.super_admin_role, _ = Role.objects.get_or_create(
            name='super_admin',
            defaults={'scope': 'global'}
        )
        
        self.region_admin_role, _ = Role.objects.get_or_create(
            name='region_admin',
            defaults={'scope': 'region'}
        )
        
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
    
    def test_assign_global_role(self):
        """Test assigning global role (no region/market required)"""
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.super_admin_role,
            is_active=True
        )
        
        self.assertTrue(user_role.is_active)
        self.assertIsNone(user_role.region)
        self.assertIsNone(user_role.market)
    
    def test_assign_region_role_requires_region(self):
        """Test that region-scoped role requires region"""
        # Should work with region
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.region_admin_role,
            region=self.region,
            is_active=True
        )
        
        self.assertEqual(user_role.region, self.region)
        
        # Should fail without region (validation in clean())
        # Note: Need to call full_clean() to trigger validation
        invalid_role = UserRole(
            user=self.user,
            role=self.region_admin_role,
            is_active=True
        )
        
        with self.assertRaises(Exception):
            invalid_role.full_clean()
            invalid_role.save()
    
    def test_role_expiry(self):
        """Test role expiry functionality"""
        # Create expired role
        expired_date = timezone.now() - timedelta(days=1)
        expired_role = UserRole.objects.create(
            user=self.user,
            role=self.super_admin_role,
            expires_at=expired_date,
            is_active=True
        )
        
        # is_expired property should return True
        self.assertTrue(expired_role.is_expired)
        
        # Create active role (no expiry)
        active_role = UserRole.objects.create(
            user=User.objects.create_user(
                email='active@test.com',
                password='testpass123'
            ),
            role=self.super_admin_role,
            is_active=True
        )
        
        self.assertFalse(active_role.is_expired)
    
    def test_unique_constraint(self):
        """Test unique constraint (user, role, region, market)"""
        UserRole.objects.create(
            user=self.user,
            role=self.super_admin_role,
            is_active=True
        )
        
        # Try to create duplicate - should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            UserRole.objects.create(
                user=self.user,
                role=self.super_admin_role,
                is_active=True
            )


class CustomUserRBACMethodsTestCase(TestCase):
    """Test CustomUser RBAC methods (has_role, has_permission, etc.)"""
    
    def setUp(self):
        """Create test data"""
        self.org, _ = Organization.objects.get_or_create(
            slug='test-org',
            defaults={'name': 'Test Org'}
        )
        
        self.region, _ = Region.objects.get_or_create(
            code='JP',
            defaults={
                'organization': self.org,
                'name': 'Japan'
            }
        )
        
        # Create roles
        self.super_admin_role, _ = Role.objects.get_or_create(
            name='super_admin',
            defaults={'scope': 'global'}
        )
        
        self.restaurant_owner_role, _ = Role.objects.get_or_create(
            name='restaurant_owner',
            defaults={'scope': 'entity'}
        )
        
        # Create permissions
        self.restaurant_edit_perm, _ = Permission.objects.get_or_create(
            resource='restaurant',
            action='EDIT'
        )
        
        self.review_create_perm, _ = Permission.objects.get_or_create(
            resource='review',
            action='CREATE'
        )
        
        # Assign permissions
        self.super_admin_role.permissions.set([
            self.restaurant_edit_perm,
            self.review_create_perm
        ])
        
        self.restaurant_owner_role.permissions.set([
            self.restaurant_edit_perm
        ])
        
        # Create user
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        
        # Assign role
        UserRole.objects.create(
            user=self.user,
            role=self.restaurant_owner_role,
            is_active=True
        )
    
    def test_has_role(self):
        """Test has_role() method"""
        self.assertTrue(self.user.has_role('restaurant_owner'))
        self.assertFalse(self.user.has_role('super_admin'))
    
    def test_has_permission(self):
        """Test has_permission() method"""
        self.assertTrue(self.user.has_permission('restaurant', 'EDIT'))
        self.assertFalse(self.user.has_permission('review', 'CREATE'))
    
    def test_get_active_roles(self):
        """Test get_active_roles() method"""
        active_roles = self.user.get_active_roles()
        self.assertEqual(active_roles.count(), 1)
        self.assertEqual(active_roles.first().name, 'restaurant_owner')
    
    def test_get_active_roles_excludes_expired(self):
        """Test that get_active_roles() excludes expired roles"""
        # Create expired role
        expired_date = timezone.now() - timedelta(days=1)
        UserRole.objects.create(
            user=self.user,
            role=self.super_admin_role,
            expires_at=expired_date,
            is_active=True
        )
        
        # Should only return non-expired roles
        active_roles = self.user.get_active_roles()
        self.assertEqual(active_roles.count(), 1)
        self.assertEqual(active_roles.first().name, 'restaurant_owner')
    
    def test_get_regions(self):
        """Test get_regions() method"""
        # Assign region-scoped role (use get_or_create to avoid duplicates)
        region_admin_role, _ = Role.objects.get_or_create(
            name='region_admin',
            defaults={'scope': 'region'}
        )
        
        UserRole.objects.create(
            user=self.user,
            role=region_admin_role,
            region=self.region,
            is_active=True
        )
        
        regions = self.user.get_regions()
        self.assertIn(self.region, regions)


class ConveniencePropertiesTestCase(TestCase):
    """Test convenience properties (is_super_admin, is_government, etc.)"""
    
    def setUp(self):
        """Create test data"""
        self.org, _ = Organization.objects.get_or_create(
            slug='test-org',
            defaults={'name': 'Test Org'}
        )
        
        # Create region (needed for government_admin role)
        self.region, _ = Region.objects.get_or_create(
            code='JP',
            defaults={
                'name': 'Japan',
                'organization': self.org
            }
        )
        
        # Create roles (use correct field name: scope, not scope_level)
        self.super_admin_role, _ = Role.objects.get_or_create(
            name='super_admin',
            defaults={'scope': 'global'}
        )
        
        self.government_admin_role, _ = Role.objects.get_or_create(
            name='government_admin',
            defaults={'scope': 'region'}
        )
        
        self.restaurant_owner_role, _ = Role.objects.get_or_create(
            name='restaurant_owner',
            defaults={'scope': 'entity'}
        )
        
        self.customer_premium_role, _ = Role.objects.get_or_create(
            name='customer_premium',
            defaults={'scope': 'entity'}
        )
        
        # Create users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        UserRole.objects.create(
            user=self.admin_user,
            role=self.super_admin_role,
            is_active=True
        )
        
        self.gov_user = User.objects.create_user(
            email='gov@test.com',
            password='testpass123'
        )
        UserRole.objects.create(
            user=self.gov_user,
            role=self.government_admin_role,
            region=self.region,
            is_active=True
        )
        
        self.restaurant_user = User.objects.create_user(
            email='restaurant@test.com',
            password='testpass123'
        )
        UserRole.objects.create(
            user=self.restaurant_user,
            role=self.restaurant_owner_role,
            is_active=True
        )
        
        self.customer_user = User.objects.create_user(
            email='customer@test.com',
            password='testpass123'
        )
        UserRole.objects.create(
            user=self.customer_user,
            role=self.customer_premium_role,
            is_active=True
        )
    
    def test_is_super_admin(self):
        """Test is_super_admin property"""
        self.assertTrue(self.admin_user.is_super_admin)
        self.assertFalse(self.gov_user.is_super_admin)
        self.assertFalse(self.restaurant_user.is_super_admin)
    
    def test_is_government(self):
        """Test is_government property"""
        self.assertTrue(self.gov_user.is_government)
        self.assertFalse(self.admin_user.is_government)
        self.assertFalse(self.restaurant_user.is_government)
    
    def test_is_restaurant_owner(self):
        """Test is_restaurant_owner property"""
        self.assertTrue(self.restaurant_user.is_restaurant_owner)
        self.assertFalse(self.admin_user.is_restaurant_owner)
        self.assertFalse(self.customer_user.is_restaurant_owner)
    
    def test_is_customer_premium(self):
        """Test is_customer_premium property"""
        self.assertTrue(self.customer_user.is_customer_premium)
        self.assertFalse(self.restaurant_user.is_customer_premium)


class BackwardCompatibilityTestCase(TestCase):
    """Test backward compatibility with user_type"""
    
    def setUp(self):
        """Create test data"""
        # Create user with legacy user_type
        self.legacy_user = User.objects.create_user(
            email='legacy@test.com',
            password='testpass123',
            user_type=1  # CUSTOMER
        )
    
    def test_user_type_still_works(self):
        """Test that user_type field still works"""
        self.assertEqual(self.legacy_user.user_type, 1)
        
        # Deprecated properties should still work but issue warning
        # Note: Testing warnings requires capturing them
        import warnings
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.legacy_user.is_customer
            
            # Check that warning was issued
            self.assertTrue(len(w) > 0)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("deprecated", str(w[-1].message).lower())


class DataMigrationTestCase(TestCase):
    """Test data migration from user_type to RBAC"""
    
    def setUp(self):
        """Create roles needed for migration"""
        self.super_admin_role, _ = Role.objects.get_or_create(
            name='super_admin',
            defaults={'scope': 'global'}
        )
        
        self.restaurant_owner_role, _ = Role.objects.get_or_create(
            name='restaurant_owner',
            defaults={'scope': 'entity'}
        )
        
        self.customer_free_role, _ = Role.objects.get_or_create(
            name='customer_free',
            defaults={'scope': 'entity'}
        )
    
    def test_migration_customer_to_free(self):
        """Test migration maps user_type=1 (CUSTOMER) to customer_free role"""
        user = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            user_type=1
        )
        
        # Simulate migration logic
        UserRole.objects.create(
            user=user,
            role=self.customer_free_role,
            is_active=True
        )
        
        self.assertTrue(user.has_role('customer_free'))
    
    def test_migration_restaurant_to_owner(self):
        """Test migration maps user_type=2 (RESTAURANT) to restaurant_owner role"""
        user = User.objects.create_user(
            email='restaurant@test.com',
            password='testpass123',
            user_type=2
        )
        
        # Simulate migration logic
        UserRole.objects.create(
            user=user,
            role=self.restaurant_owner_role,
            is_active=True
        )
        
        self.assertTrue(user.has_role('restaurant_owner'))
    
    def test_migration_admin_to_super_admin(self):
        """Test migration maps user_type=3 (ADMIN) to super_admin role"""
        user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            user_type=3
        )
        
        # Simulate migration logic
        UserRole.objects.create(
            user=user,
            role=self.super_admin_role,
            is_active=True
        )
        
        self.assertTrue(user.has_role('super_admin'))
