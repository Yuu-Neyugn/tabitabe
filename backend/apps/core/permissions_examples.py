"""
Example usage of RBAC permission classes in viewsets

This file provides examples of how to use the new RBAC permission classes.
These examples can be copied to actual viewsets when implementing RBAC.
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.permissions import (
    HasRole, HasPermission, HasAnyRole,
    CanViewRestaurant, CanEditRestaurant, CanApproveRestaurant,
    CanModerateReview, CanManageCampaign, CanViewAnalytics, CanExportData
)


# ========================================
# Example 1: Simple Role-Based Access
# ========================================

class RestaurantViewSetExample(viewsets.ModelViewSet):
    """
    Example: Restaurant viewset with RBAC permissions
    """
    # Option A: Use role-based permission
    allowed_roles = [
        'restaurant_owner',
        'restaurant_manager', 
        'restaurant_staff',
        'super_admin',
        'region_admin'
    ]
    permission_classes = [permissions.IsAuthenticated, HasAnyRole]
    
    def get_queryset(self):
        """
        Restaurant owners see only their restaurants
        Admins see all restaurants
        """
        user = self.request.user
        
        # Admins see everything
        if user.has_role('super_admin') or user.has_role('region_admin'):
            return Restaurant.objects.all()
        
        # Restaurant staff see only their own
        return Restaurant.objects.filter(user=user)


# ========================================
# Example 2: Permission-Based Access (Resource + Action)
# ========================================

class RestaurantViewSetWithPermissions(viewsets.ModelViewSet):
    """
    Example: Restaurant viewset using permission-based access control
    """
    permission_classes = [permissions.IsAuthenticated, CanViewRestaurant]
    
    def get_permissions(self):
        """
        Different permissions for different actions
        """
        if self.action == 'list' or self.action == 'retrieve':
            return [permissions.IsAuthenticated(), CanViewRestaurant()]
        elif self.action in ['create', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), CanEditRestaurant()]
        elif self.action == 'destroy':
            return [permissions.IsAuthenticated(), CanEditRestaurant()]
        elif self.action == 'approve':
            return [permissions.IsAuthenticated(), CanApproveRestaurant()]
        
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Custom action: Approve restaurant (only approval specialists and admins)
        """
        restaurant = self.get_object()
        restaurant.is_approved = True
        restaurant.save()
        return Response({'status': 'approved'})


# ========================================
# Example 3: Multiple Permission Classes
# ========================================

class ReviewViewSetExample(viewsets.ModelViewSet):
    """
    Example: Review viewset with multiple permission checks
    """
    def get_permissions(self):
        """
        View: Anyone authenticated
        Create: Only customers
        Edit: Owner or moderator
        Delete: Owner or moderator
        Moderate: Only moderators
        """
        if self.action == 'list' or self.action == 'retrieve':
            return [permissions.IsAuthenticated()]
        
        elif self.action == 'create':
            # Only customers can create reviews
            return [
                permissions.IsAuthenticated(),
                HasAnyRole()
            ]
        
        elif self.action in ['update', 'partial_update']:
            # Owner can edit their own, moderators can edit any
            return [permissions.IsAuthenticated()]
        
        elif self.action == 'destroy':
            # Owner can delete their own, moderators can delete any
            return [permissions.IsAuthenticated()]
        
        elif self.action == 'moderate':
            return [permissions.IsAuthenticated(), CanModerateReview()]
        
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
    def moderate(self, request, pk=None):
        """
        Custom action: Moderate review (only content moderators and admins)
        """
        review = self.get_object()
        action = request.data.get('action')  # 'approve', 'reject', 'hide'
        
        if action == 'approve':
            review.is_approved = True
        elif action == 'reject':
            review.is_approved = False
        elif action == 'hide':
            review.is_visible = False
        
        review.save()
        return Response({'status': 'moderated', 'action': action})


# ========================================
# Example 4: Campaign Management
# ========================================

class CampaignViewSetExample(viewsets.ModelViewSet):
    """
    Example: Campaign viewset with role-based permissions
    """
    permission_classes = [permissions.IsAuthenticated, CanManageCampaign]
    
    def get_queryset(self):
        """
        Campaign managers see campaigns in their region
        Super admins see all campaigns
        """
        user = self.request.user
        
        if user.has_role('super_admin') or user.has_role('global_operations'):
            return Campaign.objects.all()
        
        # Campaign managers see only their region's campaigns
        if user.has_role('campaign_manager'):
            user_regions = user.get_regions()
            return Campaign.objects.filter(region__in=user_regions)
        
        return Campaign.objects.none()


# ========================================
# Example 5: Analytics & Data Export
# ========================================

class AnalyticsViewSetExample(viewsets.ViewSet):
    """
    Example: Analytics viewset with export capability
    """
    permission_classes = [permissions.IsAuthenticated, CanViewAnalytics]
    
    def list(self, request):
        """
        View analytics (admins, analysts, campaign managers)
        """
        # Return analytics data
        return Response({
            'total_restaurants': 150,
            'total_reviews': 3240,
            'total_customers': 8500
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, CanExportData])
    def export(self, request):
        """
        Export analytics data (only admins and analysts with export permission)
        """
        # Generate CSV or Excel file
        return Response({'export_url': '/downloads/analytics_2024.csv'})


# ========================================
# Example 6: User Management (Admin Only)
# ========================================

class UserManagementViewSetExample(viewsets.ModelViewSet):
    """
    Example: User management viewset (admin only)
    """
    required_resource = 'user'
    required_action = 'VIEW'
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    
    def get_permissions(self):
        """
        Different permissions for different actions
        """
        action_map = {
            'list': ('user', 'VIEW'),
            'retrieve': ('user', 'VIEW'),
            'create': ('user', 'CREATE'),
            'update': ('user', 'EDIT'),
            'partial_update': ('user', 'EDIT'),
            'destroy': ('user', 'DELETE'),
        }
        
        if self.action in action_map:
            resource, action = action_map[self.action]
            # Dynamically set required resource and action
            self.required_resource = resource
            self.required_action = action
        
        return super().get_permissions()


# ========================================
# Example 7: Government Campaign Management
# ========================================

class GovernmentCampaignViewSetExample(viewsets.ModelViewSet):
    """
    Example: Government campaign viewset (government admins only)
    """
    allowed_roles = [
        'government_admin',
        'government_analyst',
        'super_admin',
        'region_admin'
    ]
    permission_classes = [permissions.IsAuthenticated, HasAnyRole]
    
    def get_queryset(self):
        """
        Government admins see campaigns in their region
        Super admins see all campaigns
        """
        user = self.request.user
        
        if user.has_role('super_admin'):
            return GovernmentCampaign.objects.all()
        
        # Government users see only their region's campaigns
        user_regions = user.get_regions()
        return GovernmentCampaign.objects.filter(region__in=user_regions)


# ========================================
# Example 8: Mixed Permissions (Owner OR Admin)
# ========================================

class RestaurantProductViewSetExample(viewsets.ModelViewSet):
    """
    Example: Restaurant product viewset (owner can edit their own, admins can edit any)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        View: Anyone authenticated
        Create/Edit/Delete: Restaurant owner or admin
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanEditRestaurant()]
        
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """
        Restaurant owners see only their products
        Admins see all products
        """
        user = self.request.user
        
        # Admins see everything
        if (user.has_role('super_admin') or 
            user.has_role('global_operations') or 
            user.has_role('region_admin')):
            return RestaurantProduct.objects.all()
        
        # Restaurant owners see only their own
        return RestaurantProduct.objects.filter(restaurant__user=user)


# ========================================
# Migration Guide: Converting Legacy to RBAC
# ========================================

"""
BEFORE (Legacy user_type):
--------------------------
class RestaurantViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsRestaurant]
    
    def get_queryset(self):
        if self.request.user.is_admin:
            return Restaurant.objects.all()
        return Restaurant.objects.filter(user=self.request.user)


AFTER (RBAC):
-------------
class RestaurantViewSet(viewsets.ModelViewSet):
    allowed_roles = [
        'restaurant_owner', 'restaurant_manager', 'restaurant_staff',
        'super_admin', 'region_admin'
    ]
    permission_classes = [permissions.IsAuthenticated, HasAnyRole]
    
    def get_queryset(self):
        if self.request.user.has_role('super_admin') or self.request.user.has_role('region_admin'):
            return Restaurant.objects.all()
        return Restaurant.objects.filter(user=self.request.user)


ALTERNATIVE (Permission-based):
--------------------------------
class RestaurantViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CanViewRestaurant]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanEditRestaurant()]
        return super().get_permissions()
    
    def get_queryset(self):
        user = self.request.user
        if user.has_permission('restaurant', 'VIEW'):
            # Admins can view all
            if user.has_role('super_admin') or user.has_role('region_admin'):
                return Restaurant.objects.all()
        return Restaurant.objects.filter(user=user)
"""
