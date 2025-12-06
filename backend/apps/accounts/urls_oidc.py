"""
OIDC Authentication URLs for Tabitabe
Provides Keycloak login/logout endpoints
"""
from django.urls import path
from mozilla_django_oidc import views as oidc_views

app_name = 'oidc'

urlpatterns = [
    # OIDC Login - redirects to Keycloak
    path('login/', oidc_views.OIDCAuthenticationRequestView.as_view(), name='login'),
    
    # OIDC Callback - Keycloak redirects here after authentication
    path('callback/', oidc_views.OIDCAuthenticationCallbackView.as_view(), name='callback'),
    
    # OIDC Logout
    path('logout/', oidc_views.OIDCLogoutView.as_view(), name='logout'),
]
