"""
Admin API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RestaurantApprovalViewSet,
    UserManagementViewSet,
    AnalyticsViewSet,
)

router = DefaultRouter()
router.register(r'restaurants', RestaurantApprovalViewSet, basename='admin-restaurants')
router.register(r'users', UserManagementViewSet, basename='admin-users')
router.register(r'analytics', AnalyticsViewSet, basename='admin-analytics')

app_name = 'admin'

urlpatterns = [
    path('', include(router.urls)),
]
