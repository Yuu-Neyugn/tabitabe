"""
Custom permissions for fine-grained access control
"""
from rest_framework import permissions


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
    Permission to only allow customers
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_customer


class IsRestaurant(permissions.BasePermission):
    """
    Permission to only allow restaurants
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_restaurant


class IsAdmin(permissions.BasePermission):
    """
    Permission to only allow admins
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to allow owners or admins
    """
    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.is_admin or request.user.is_staff:
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
        # Must be restaurant type or admin
        return request.user.is_restaurant or request.user.is_admin or request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.is_admin or request.user.is_staff:
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
