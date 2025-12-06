"""
Custom permissions for fine-grained access control with RBAC support
"""
from rest_framework import permissions


# ========================================
# RBAC Permission Classes
# ========================================

class HasRole(permissions.BasePermission):
    """
    Permission that checks if user has a specific role.
    Usage: Set `required_role` attribute on the viewset or override get_required_role()
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get required role from view
        required_role = getattr(view, 'required_role', None)
        if not required_role:
            return False
        
        return request.user.has_role(required_role)


class HasPermission(permissions.BasePermission):
    """
    Permission that checks if user has a specific permission (resource + action).
    Usage: Set `required_resource` and `required_action` attributes on the viewset
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get required permission from view
        required_resource = getattr(view, 'required_resource', None)
        required_action = getattr(view, 'required_action', None)
        
        if not required_resource or not required_action:
            return False
        
        return request.user.has_permission(required_resource, required_action)


class HasAnyRole(permissions.BasePermission):
    """
    Permission that checks if user has any of the specified roles.
    Usage: Set `allowed_roles` list attribute on the viewset
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        allowed_roles = getattr(view, 'allowed_roles', [])
        if not allowed_roles:
            return False
        
        return any(request.user.has_role(role) for role in allowed_roles)


class CanViewRestaurant(permissions.BasePermission):
    """
    Permission for restaurant viewing (all authenticated users + specific roles can view)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # All authenticated users can view restaurants
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Non-safe methods require restaurant permission
        return request.user.has_permission('restaurant', 'VIEW')


class CanEditRestaurant(permissions.BasePermission):
    """
    Permission for restaurant editing (restaurant owners, managers, staff, admins)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.has_permission('restaurant', 'EDIT')
    
    def has_object_permission(self, request, view, obj):
        # Admins can edit any restaurant
        if (request.user.has_role('super_admin') or 
            request.user.has_role('global_operations') or 
            request.user.has_role('region_admin')):
            return True
        
        # Restaurant owners/managers/staff can only edit their own
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        if hasattr(obj, 'restaurant'):
            return obj.restaurant.user == request.user
        
        return False


class CanApproveRestaurant(permissions.BasePermission):
    """
    Permission for restaurant approval (only approval specialists and admins)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.has_permission('restaurant', 'APPROVE')


class CanModerateReview(permissions.BasePermission):
    """
    Permission for review moderation (content moderators and admins)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.has_permission('review', 'MODERATE')


class CanManageCampaign(permissions.BasePermission):
    """
    Permission for campaign management (campaign managers and admins)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check view method to determine required action
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_permission('campaign', 'VIEW')
        elif request.method == 'POST':
            return request.user.has_permission('campaign', 'CREATE')
        elif request.method in ['PUT', 'PATCH']:
            return request.user.has_permission('campaign', 'EDIT')
        elif request.method == 'DELETE':
            return request.user.has_permission('campaign', 'DELETE')
        
        return False


class CanViewAnalytics(permissions.BasePermission):
    """
    Permission for analytics viewing (admins, analysts, campaign managers)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.has_permission('analytics', 'VIEW')


class CanExportData(permissions.BasePermission):
    """
    Permission for data export (admins, analysts)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has export permission for any resource
        return (
            request.user.has_permission('analytics', 'EXPORT') or
            request.user.has_permission('financial', 'EXPORT')
        )


# ========================================
# Legacy Permission Classes (DEPRECATED - use RBAC classes above)
# ========================================

class IsOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an object to access it
    """
    def has_object_permission(self, request, view, obj):
        # Check if obj has 'user' attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # Check if obj IS the user
        return obj == request.user


class IsCustomer(permissions.BasePermission):
    """
    ⚠️ DEPRECATED: Use HasRole or HasAnyRole with 'customer_*' roles instead
    Permission to only allow customers
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Support both RBAC and legacy user_type
        return (
            request.user.has_role('customer_free') or 
            request.user.has_role('customer_premium') or 
            request.user.has_role('customer_premium_plus') or
            request.user.is_customer  # Fallback to legacy
        )


class IsRestaurant(permissions.BasePermission):
    """
    ⚠️ DEPRECATED: Use HasRole or HasAnyRole with 'restaurant_*' roles instead
    Permission to only allow restaurants
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Support both RBAC and legacy user_type
        return (
            request.user.has_role('restaurant_owner') or 
            request.user.has_role('restaurant_manager') or 
            request.user.has_role('restaurant_staff') or
            request.user.is_restaurant  # Fallback to legacy
        )


class IsAdmin(permissions.BasePermission):
    """
    ⚠️ DEPRECATED: Use HasRole or HasAnyRole with admin roles instead
    Permission to only allow admins
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Support both RBAC and legacy user_type
        return (
            request.user.has_role('super_admin') or 
            request.user.has_role('global_operations') or 
            request.user.has_role('region_admin') or
            request.user.is_admin or  # Fallback to legacy
            request.user.is_staff
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to allow owners or admins
    """
    def has_object_permission(self, request, view, obj):
        # Check RBAC admin roles
        if (request.user.has_role('super_admin') or 
            request.user.has_role('global_operations') or 
            request.user.has_role('region_admin') or
            request.user.is_staff):
            return True
        
        # Check ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


class IsRestaurantOwner(permissions.BasePermission):
    """
    Permission to only allow restaurant owners to access their own restaurant
    """
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check RBAC restaurant roles or admin roles
        return (
            request.user.has_role('restaurant_owner') or 
            request.user.has_role('restaurant_manager') or 
            request.user.has_role('restaurant_staff') or
            request.user.has_role('super_admin') or 
            request.user.has_role('global_operations') or 
            request.user.has_role('region_admin') or
            request.user.is_staff or
            request.user.is_restaurant  # Fallback to legacy
        )
    
    def has_object_permission(self, request, view, obj):
        # Check RBAC admin roles
        if (request.user.has_role('super_admin') or 
            request.user.has_role('global_operations') or 
            request.user.has_role('region_admin') or
            request.user.is_staff):
            return True
        
        # Check if obj is Restaurant
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if obj is Product/Image and belongs to user's restaurant
        if hasattr(obj, 'restaurant'):
            return obj.restaurant.user == request.user
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permission to only allow read operations (GET, HEAD, OPTIONS)
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS