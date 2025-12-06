# RBAC Permission Classes Documentation

## Overview

Tabitabe's RBAC (Role-Based Access Control) system provides fine-grained permissions for API endpoints. This document explains how to use the new permission classes in your Django REST Framework viewsets.

## Quick Start

### 1. Role-Based Permissions

Use `HasRole` or `HasAnyRole` when you want to restrict access based on user roles.

```python
from rest_framework import viewsets, permissions
from apps.core.permissions import HasAnyRole

class RestaurantViewSet(viewsets.ModelViewSet):
    allowed_roles = [
        'restaurant_owner',
        'restaurant_manager',
        'super_admin',
        'region_admin'
    ]
    permission_classes = [permissions.IsAuthenticated, HasAnyRole]
```

### 2. Permission-Based Access (Resource + Action)

Use `HasPermission` when you want to check if user has a specific permission (e.g., `restaurant.EDIT`).

```python
from apps.core.permissions import HasPermission

class UserManagementViewSet(viewsets.ModelViewSet):
    required_resource = 'user'
    required_action = 'VIEW'
    permission_classes = [permissions.IsAuthenticated, HasPermission]
```

### 3. Pre-built Permission Classes

Use domain-specific permission classes for common scenarios:

```python
from apps.core.permissions import (
    CanViewRestaurant, 
    CanEditRestaurant, 
    CanApproveRestaurant,
    CanModerateReview
)

class RestaurantViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CanViewRestaurant]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), CanEditRestaurant()]
        elif self.action == 'approve':
            return [permissions.IsAuthenticated(), CanApproveRestaurant()]
        return super().get_permissions()
```

## Available Permission Classes

### Core RBAC Classes

| Class | Description | Usage |
|-------|-------------|-------|
| `HasRole` | Checks if user has a specific role | Set `required_role` attribute on viewset |
| `HasPermission` | Checks if user has a permission (resource + action) | Set `required_resource` and `required_action` on viewset |
| `HasAnyRole` | Checks if user has any of the allowed roles | Set `allowed_roles` list on viewset |

### Domain-Specific Permission Classes

| Class | Description | Who Has Access |
|-------|-------------|----------------|
| `CanViewRestaurant` | View restaurant data | All authenticated users (read), restaurant roles + admins (write) |
| `CanEditRestaurant` | Edit restaurant data | restaurant_owner, restaurant_manager, restaurant_staff, admins |
| `CanApproveRestaurant` | Approve restaurant registration | restaurant_approval_specialist, region_admin, super_admin |
| `CanModerateReview` | Moderate reviews | content_moderator, region_admin, super_admin |
| `CanManageCampaign` | Manage campaigns | campaign_manager, region_admin, super_admin |
| `CanViewAnalytics` | View analytics dashboard | government_analyst, campaign_manager, region_admin, super_admin |
| `CanExportData` | Export data to CSV/Excel | government_analyst, region_admin, super_admin |

### Legacy Classes (Deprecated)

| Class | Status | Replacement |
|-------|--------|-------------|
| `IsCustomer` | ⚠️ Deprecated | Use `HasAnyRole` with `['customer_free', 'customer_premium', 'customer_premium_plus']` |
| `IsRestaurant` | ⚠️ Deprecated | Use `HasAnyRole` with `['restaurant_owner', 'restaurant_manager', 'restaurant_staff']` |
| `IsAdmin` | ⚠️ Deprecated | Use `HasAnyRole` with `['super_admin', 'global_operations', 'region_admin']` |

## Roles & Permissions

### Available Roles

**Global Admin Roles:**
- `super_admin` - Full system access
- `global_operations` - Global operations management

**Regional Admin Roles:**
- `region_admin` - Regional administration
- `restaurant_approval_specialist` - Approve restaurant registrations
- `content_moderator` - Moderate reviews and content
- `customer_support_agent` - Handle customer support
- `campaign_manager` - Manage campaigns

**Government Roles:**
- `government_admin` - Government campaign management
- `government_analyst` - View analytics and export data

**Restaurant Roles:**
- `restaurant_owner` - Full access to own restaurant
- `restaurant_manager` - Manage restaurant operations
- `restaurant_staff` - Limited restaurant access
- `restaurant_viewer` - View-only access

**Customer Roles:**
- `customer_premium_plus` - Premium+ tier customer
- `customer_premium` - Premium tier customer
- `customer_free` - Free tier customer

### Permission Resources & Actions

**Resources:**
- `organization`, `region`, `role`, `user`
- `restaurant`, `review`, `campaign`, `government_campaign`
- `advertisement`, `badge`, `leaderboard`, `checkin`
- `analytics`, `financial`, `audit_log`

**Actions:**
- `VIEW`, `CREATE`, `EDIT`, `DELETE`
- `APPROVE`, `MODERATE`, `EXPORT`, `ASSIGN`

## Migration from user_type to RBAC

### Before (Legacy):

```python
class RestaurantViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsRestaurant]
    
    def get_queryset(self):
        if self.request.user.is_admin:
            return Restaurant.objects.all()
        return Restaurant.objects.filter(user=self.request.user)
```

### After (RBAC):

```python
class RestaurantViewSet(viewsets.ModelViewSet):
    allowed_roles = [
        'restaurant_owner', 'restaurant_manager', 'restaurant_staff',
        'super_admin', 'region_admin'
    ]
    permission_classes = [permissions.IsAuthenticated, HasAnyRole]
    
    def get_queryset(self):
        user = self.request.user
        if user.has_role('super_admin') or user.has_role('region_admin'):
            return Restaurant.objects.all()
        return Restaurant.objects.filter(user=user)
```

## Advanced Usage

### Dynamic Permissions per Action

```python
class ReviewViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        
        elif self.action == 'create':
            # Only customers can create reviews
            return [permissions.IsAuthenticated(), HasAnyRole()]
        
        elif self.action == 'moderate':
            return [permissions.IsAuthenticated(), CanModerateReview()]
        
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
    def moderate(self, request, pk=None):
        review = self.get_object()
        # Moderate review logic
        return Response({'status': 'moderated'})
```

### Region-Scoped Queries

```python
class CampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CanManageCampaign]
    
    def get_queryset(self):
        user = self.request.user
        
        # Super admins see all campaigns
        if user.has_role('super_admin') or user.has_role('global_operations'):
            return Campaign.objects.all()
        
        # Regional admins/managers see only their region's campaigns
        user_regions = user.get_regions()
        return Campaign.objects.filter(region__in=user_regions)
```

### Custom Permission Actions

```python
class RestaurantViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'], 
            permission_classes=[permissions.IsAuthenticated, CanApproveRestaurant])
    def approve(self, request, pk=None):
        """
        Custom action: Approve restaurant
        Only approval specialists and admins can access
        """
        restaurant = self.get_object()
        restaurant.is_approved = True
        restaurant.save()
        return Response({'status': 'approved'})
```

## Testing Permissions

### Unit Tests

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.rbac_models import Role, Permission, UserRole

User = get_user_model()

class RBACPermissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.com')
        self.role = Role.objects.get(name='restaurant_owner')
        UserRole.objects.create(user=self.user, role=self.role, is_active=True)
    
    def test_has_role(self):
        self.assertTrue(self.user.has_role('restaurant_owner'))
        self.assertFalse(self.user.has_role('super_admin'))
    
    def test_has_permission(self):
        self.assertTrue(self.user.has_permission('restaurant', 'EDIT'))
        self.assertFalse(self.user.has_permission('user', 'DELETE'))
```

### API Tests

```python
from rest_framework.test import APITestCase
from rest_framework import status

class RestaurantAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='owner@test.com')
        role = Role.objects.get(name='restaurant_owner')
        UserRole.objects.create(user=self.user, role=role, is_active=True)
        self.client.force_authenticate(user=self.user)
    
    def test_restaurant_owner_can_edit(self):
        response = self.client.patch(f'/api/restaurants/{self.restaurant.id}/', {
            'name': 'Updated Name'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

## Troubleshooting

### User doesn't have expected permissions

1. Check if user has the role:
   ```python
   user.get_active_roles()  # Returns list of role objects
   ```

2. Check if role has the permission:
   ```python
   role = Role.objects.get(name='restaurant_owner')
   role.permissions.filter(resource='restaurant', action='EDIT').exists()
   ```

3. Check if UserRole is active and not expired:
   ```python
   UserRole.objects.filter(user=user, role=role, is_active=True)
   ```

### Permission denied errors

Make sure:
- User is authenticated
- User has active roles (not expired)
- Role has the required permission
- Viewset has correct `allowed_roles`, `required_resource`, or `required_action` set

## Best Practices

1. **Use domain-specific permission classes** (e.g., `CanEditRestaurant`) instead of generic `HasPermission` when possible
2. **Override `get_permissions()`** to set different permissions per action
3. **Filter querysets** based on user roles to ensure users only see authorized data
4. **Use region scoping** for regional admins and managers
5. **Test permission logic** thoroughly with unit and API tests
6. **Log permission checks** in production for debugging and audit trails

## See Also

- [RBAC Models Documentation](../accounts/rbac_models.py)
- [Permission Examples](./permissions_examples.py)
- [CustomUser RBAC Methods](../accounts/models.py)
- [VISION.md](../../docs/VISION.md) - Full RBAC system architecture

## Support

For questions or issues with RBAC permissions, contact:
- Backend Team: backend@tabitabe.com
- Documentation: docs@tabitabe.com
