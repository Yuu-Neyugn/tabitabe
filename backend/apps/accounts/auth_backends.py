"""
Authentication Backends - Extensible design for future OIDC/OAuth2 integration
Current: Email/Password authentication
Future: OIDC providers (Keycloak, Google, Line, etc.)
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from typing import Optional
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Email-based authentication backend
    
    This is the primary authentication method for now.
    Future: Will coexist with OIDCAuthenticationBackend
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user by email and password
        
        Args:
            request: HTTP request object
            username: Email address (we use 'username' param for compatibility)
            password: User password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        email = kwargs.get('email', username)
        
        if email is None or password is None:
            return None
        
        try:
            # Find user by email (case-insensitive)
            user = User.objects.get(
                Q(email__iexact=email) | Q(username__iexact=email)
            )
            
            # Check password
            if user.check_password(password):
                # Check if user is active
                if not user.is_active:
                    logger.warning(f"Inactive user attempted login: {email}")
                    return None
                
                logger.info(f"Successful authentication: {email}")
                return user
            else:
                logger.warning(f"Invalid password for user: {email}")
                return None
                
        except User.DoesNotExist:
            logger.warning(f"User not found: {email}")
            # Run default password hasher to mitigate timing attacks
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            logger.error(f"Multiple users found for email: {email}")
            return None
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class RBACPermissionBackend:
    """
    RBAC-based permission backend
    
    This backend checks permissions based on user's assigned roles.
    Works alongside EmailBackend for authentication.
    
    Future: Will integrate with OIDC claims/scopes when migrating to OAuth2
    """
    
    def authenticate(self, request, **kwargs):
        """
        This backend doesn't perform authentication,
        only authorization (permission checking)
        """
        return None
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if user has a specific permission through their roles
        
        Args:
            user_obj: User instance
            perm: Permission string (format: "app.permission_name" or "resource.action")
            obj: Optional object to check permission against
            
        Returns:
            Boolean indicating if user has permission
            
        Future: Will integrate with OIDC token scopes
        Format: "urn:tabitabe:permission:restaurant.view"
        """
        if not user_obj.is_active:
            return False
        
        # Superusers have all permissions
        if user_obj.is_superuser:
            return True
        
        # Parse permission string
        # Supports both Django format (app.codename) and RBAC format (resource.action)
        if '.' in perm:
            parts = perm.split('.')
            if len(parts) == 2:
                resource_or_app, action_or_codename = parts
                
                # Try RBAC format first (resource.action)
                if user_obj.has_permission(resource_or_app, action_or_codename):
                    return True
        
        # Fallback to default Django permission check
        return False
    
    def has_module_perms(self, user_obj, app_label):
        """
        Check if user has any permissions in the given app
        
        Future: Will check OIDC scopes like "urn:tabitabe:app:restaurants"
        """
        if not user_obj.is_active:
            return False
        
        if user_obj.is_superuser:
            return True
        
        # Check if user has any permissions for resources in this app
        # This is a simplified check - can be extended based on needs
        return user_obj.get_active_roles().exists()
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# Future OIDC Backend (commented out for now)
# Uncomment and configure when migrating to OIDC
"""
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

class TabitabeOIDCBackend(OIDCAuthenticationBackend):
    '''
    OIDC Authentication Backend for Tabitabe
    
    Providers to support:
    - Keycloak (primary)
    - Google (for customers)
    - Line (for Japan market)
    - Azure AD (for government/enterprise)
    '''
    
    def filter_users_by_claims(self, claims):
        '''Filter users by OIDC claims'''
        email = claims.get('email')
        if not email:
            return User.objects.none()
        
        return User.objects.filter(email__iexact=email)
    
    def create_user(self, claims):
        '''Create user from OIDC claims'''
        email = claims.get('email')
        
        # Map OIDC claims to user fields
        user = User.objects.create_user(
            email=email,
            first_name=claims.get('given_name', ''),
            last_name=claims.get('family_name', ''),
            # Set other fields from claims
        )
        
        # Map OIDC groups/roles to RBAC roles
        self._sync_roles_from_claims(user, claims)
        
        return user
    
    def update_user(self, user, claims):
        '''Update user from OIDC claims'''
        user.first_name = claims.get('given_name', user.first_name)
        user.last_name = claims.get('family_name', user.last_name)
        user.save()
        
        # Sync roles on each login
        self._sync_roles_from_claims(user, claims)
        
        return user
    
    def _sync_roles_from_claims(self, user, claims):
        '''
        Sync RBAC roles from OIDC claims
        
        Expected claim format:
        {
            "roles": ["super_admin", "region_admin"],
            "region": "JP",
            "scope": "global"
        }
        '''
        from apps.accounts.rbac_models import Role, UserRole, Region
        
        oidc_roles = claims.get('roles', [])
        region_code = claims.get('region')
        
        # Clear existing role assignments
        UserRole.objects.filter(user=user).delete()
        
        # Assign new roles from OIDC
        for role_name in oidc_roles:
            try:
                role = Role.objects.get(name=role_name)
                region = None
                
                # If role requires region, get it from claims
                if role.scope_level == 'region' and region_code:
                    region = Region.objects.get(code=region_code)
                
                UserRole.objects.create(
                    user=user,
                    role=role,
                    region=region,
                    is_active=True
                )
            except (Role.DoesNotExist, Region.DoesNotExist):
                logger.warning(f"Cannot assign role {role_name} to user {user.email}")
                continue
"""
