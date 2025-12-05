"""
Restaurant API URLs
"""
from django.urls import path, include
from rest_framework_nested import routers

from .views import RestaurantViewSet, ProductViewSet, MediaFileViewSet

app_name = 'restaurants'

# Main router
router = routers.DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurants')

# Nested routers for products and media
restaurants_router = routers.NestedDefaultRouter(router, r'restaurants', lookup='restaurant')
restaurants_router.register(r'products', ProductViewSet, basename='restaurant-products')
restaurants_router.register(r'media', MediaFileViewSet, basename='restaurant-media')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(restaurants_router.urls)),
]
