"""
Force sync view - Manually trigger OIDC user and role synchronization
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
@login_required
def force_sync_roles(request):
    """
    Force synchronization of roles from OIDC tokens
    
    This is useful when:
    - User roles changed in Keycloak but session is still active
    - Need to manually trigger role sync without re-login
    
    Returns:
        JSON response with sync status
    """
    user = request.user
    
    # Get OIDC tokens from session
    id_token = request.session.get('oidc_id_token')
    access_token = request.session.get('oidc_access_token')
    
    if not id_token:
        return JsonResponse({
            'success': False,
            'error': 'No OIDC tokens found in session',
            'message': 'User not authenticated via OIDC'
        }, status=400)
    
    try:
        # Decode ID token to get claims
        from apps.accounts.oidc_backend import TabitabeOIDCBackend
        import json
        import base64
        
        # Parse JWT manually (simple decode without verification since it's from our session)
        parts = id_token.split('.')
        if len(parts) != 3:
            raise ValueError('Invalid JWT format')
        
        # Decode payload (add padding if needed)
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        claims = json.loads(base64.urlsafe_b64decode(payload))
        
        logger.info(f"Force syncing roles for {user.email}")
        logger.info(f"Claims from ID token: {claims}")
        
        # Use backend's sync method
        backend = TabitabeOIDCBackend()
        backend._sync_roles_from_claims(user, claims)
        
        # Get updated roles
        from apps.accounts.rbac_models import UserRole
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        roles_data = [
            {
                'name': ur.role.name,
                'scope_level': ur.role.scope_level,
                'region': ur.region.code if ur.region else None
            }
            for ur in user_roles
        ]
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully synced {len(roles_data)} roles',
            'user': user.email,
            'roles': roles_data,
            'claims_preview': {
                'email': claims.get('email'),
                'roles': claims.get('roles', []),
                'region': claims.get('region', 'JP')
            }
        })
        
    except Exception as e:
        logger.error(f"Error force syncing roles: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Failed to sync roles'
        }, status=500)
