"""
Test URLs for OIDC authentication
"""
from django.urls import path
from apps.accounts.views.test_oidc import oidc_test_page, oidc_success
from apps.accounts.views.oidc_logout import oidc_logout_view, clear_session_view
from apps.accounts.views.force_sync import force_sync_roles

app_name = 'oidc_test'

urlpatterns = [
    path('', oidc_test_page, name='page'),
    path('success/', oidc_success, name='success'),
    path('logout/', oidc_logout_view, name='logout'),
    path('clear-session/', clear_session_view, name='clear_session'),
    path('force-sync/', force_sync_roles, name='force_sync'),
]
