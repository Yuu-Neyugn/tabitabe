"""
API v1 URL Configuration
"""
from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

app_name = 'api_v1'


@api_view(['GET'])
def api_root(request, format=None):
    """API Root - List all available endpoints"""
    return Response({
        'message': 'Welcome to Tabitabe API v1',
        'endpoints': {
            'schema': reverse('schema', request=request, format=format),
            'docs': reverse('swagger-ui', request=request, format=format),
            'redoc': reverse('redoc', request=request, format=format),
            'admin': '/admin/',
        },
        'status': 'operational'
    })


urlpatterns = [
    # API Root
    path('', api_root, name='api-root'),
    
    # Authentication endpoints (commented until implemented)
    # path('auth/', include('api.v1.auth.urls')),
    
    # Customer endpoints
    # path('customers/', include('api.v1.customers.urls')),
    
    # Restaurant endpoints
    # path('restaurants/', include('api.v1.restaurants.urls')),
    
    # Admin endpoints
    path('admin/', include('api.v1.admin.urls')),
]
