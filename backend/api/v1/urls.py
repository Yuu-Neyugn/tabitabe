"""
API v1 URL Configuration
"""
from django.urls import path, include

app_name = 'api_v1'

urlpatterns = [
    # Authentication endpoints
    path('auth/', include('api.v1.auth.urls')),
    
    # Customer endpoints
    # path('customers/', include('api.v1.customers.urls')),
    
    # Restaurant endpoints
    # path('restaurants/', include('api.v1.restaurants.urls')),
    
    # Admin endpoints
    # path('admin/', include('api.v1.admin.urls')),
]
