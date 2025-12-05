"""
Admin API Views
"""
from django.db.models import Q, Count, Avg
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from apps.accounts.models import CustomUser
from apps.restaurants.models import Restaurant, RestaurantStatus
from apps.reviews.models import Review
from apps.campaigns.models import GiftCard, Stamprally
from apps.notifications.tasks.restaurant_tasks import (
    send_restaurant_approval_email,
    send_restaurant_rejection_email,
)

from .serializers import (
    UserListSerializer,
    UserDetailSerializer,
    RestaurantApprovalSerializer,
    RestaurantApprovalActionSerializer,
    AnalyticsSummarySerializer,
)


class RestaurantApprovalViewSet(viewsets.ModelViewSet):
    """
    Restaurant approval management for admin
    
    Endpoints:
    - GET /api/v1/admin/restaurants/ - List all restaurants
    - GET /api/v1/admin/restaurants/pending/ - List pending restaurants
    - GET /api/v1/admin/restaurants/{id}/ - Restaurant details
    - POST /api/v1/admin/restaurants/{id}/approve/ - Approve restaurant
    - POST /api/v1/admin/restaurants/{id}/reject/ - Reject restaurant
    """
    permission_classes = [IsAdminUser]
    serializer_class = RestaurantApprovalSerializer
    queryset = Restaurant.objects.all().select_related('user').order_by('-created_at')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """List pending restaurants"""
        pending_restaurants = self.get_queryset().filter(status=RestaurantStatus.PENDING)
        serializer = self.get_serializer(pending_restaurants, many=True)
        return Response({
            'count': pending_restaurants.count(),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve restaurant"""
        restaurant = self.get_object()
        
        if restaurant.status != RestaurantStatus.PENDING:
            return Response(
                {'error': 'Only pending restaurants can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        restaurant.status = RestaurantStatus.APPROVED
        restaurant.save()
        
        # Send approval email via Celery
        send_restaurant_approval_email.delay(restaurant.id)
        
        serializer = self.get_serializer(restaurant)
        return Response({
            'message': 'Restaurant approved successfully',
            'restaurant': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject restaurant"""
        restaurant = self.get_object()
        action_serializer = RestaurantApprovalActionSerializer(data=request.data)
        
        if not action_serializer.is_valid():
            return Response(action_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if restaurant.status != RestaurantStatus.PENDING:
            return Response(
                {'error': 'Only pending restaurants can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        restaurant.status = RestaurantStatus.REJECTED
        restaurant.save()
        
        # Send rejection email via Celery with reason
        rejection_reason = action_serializer.validated_data.get('rejection_reason')
        send_restaurant_rejection_email.delay(restaurant.id, rejection_reason)
        
        serializer = self.get_serializer(restaurant)
        return Response({
            'message': 'Restaurant rejected successfully',
            'restaurant': serializer.data
        })


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    User management for admin
    
    Endpoints:
    - GET /api/v1/admin/users/ - List all users
    - GET /api/v1/admin/users/{id}/ - User details
    - PATCH /api/v1/admin/users/{id}/ - Update user
    - POST /api/v1/admin/users/{id}/deactivate/ - Deactivate user
    - POST /api/v1/admin/users/{id}/activate/ - Activate user
    """
    permission_classes = [IsAdminUser]
    queryset = CustomUser.objects.all().order_by('-date_joined')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_type = self.request.query_params.get('user_type')
        is_active = self.request.query_params.get('is_active')
        search = self.request.query_params.get('search')
        
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate user account"""
        user = self.get_object()
        
        if not user.is_active:
            return Response(
                {'error': 'User is already inactive'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = False
        user.save()
        
        serializer = self.get_serializer(user)
        return Response({
            'message': 'User deactivated successfully',
            'user': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate user account"""
        user = self.get_object()
        
        if user.is_active:
            return Response(
                {'error': 'User is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = True
        user.save()
        
        serializer = self.get_serializer(user)
        return Response({
            'message': 'User activated successfully',
            'user': serializer.data
        })


class AnalyticsViewSet(viewsets.ViewSet):
    """
    Analytics dashboard for admin
    
    Endpoints:
    - GET /api/v1/admin/analytics/summary/ - Overall summary statistics
    """
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get overall analytics summary"""
        total_users = CustomUser.objects.count()
        total_customers = CustomUser.objects.filter(user_type=1).count()
        total_restaurants = Restaurant.objects.count()
        total_reviews = Review.objects.count()
        pending_restaurants = Restaurant.objects.filter(status=0).count()
        
        active_gift_cards = GiftCard.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).count()
        
        active_stamp_rallies = Stamprally.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).count()
        
        avg_rating = Restaurant.objects.aggregate(
            avg_rating=Avg('average_rating')
        )['avg_rating'] or 0
        
        data = {
            'total_users': total_users,
            'total_customers': total_customers,
            'total_restaurants': total_restaurants,
            'total_reviews': total_reviews,
            'pending_restaurants': pending_restaurants,
            'active_gift_cards': active_gift_cards,
            'active_stamp_rallies': active_stamp_rallies,
            'avg_restaurant_rating': round(avg_rating, 2)
        }
        
        serializer = AnalyticsSummarySerializer(data)
        return Response(serializer.data)
