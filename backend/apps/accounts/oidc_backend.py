"""
OIDC Authentication Backend for Tabitabe
Implements Keycloak integration with RBAC role synchronization
"""
from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
import logging

try:
    from mozilla_django_oidc.auth import OIDCAuthenticationBackend as BaseOIDCBackend
    OIDC_AVAILABLE = True
except ImportError:
    OIDC_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("mozilla-django-oidc not installed. Install with: pip install mozilla-django-oidc")

logger = logging.getLogger(__name__)
User = get_user_model()


if OIDC_AVAILABLE:
    class TabitabeOIDCBackend(BaseOIDCBackend):
        """
        Custom OIDC backend for Tabitabe with Keycloak
        
        Features:
        - User creation from OIDC claims
        - Role synchronization from Keycloak to RBAC
        - Region assignment from claims
        - Automatic user updates on login
        
        Keycloak Configuration Required:
        - Realm: tabitabe
        - Client: tabitabe-web
        - Protocol Mappers: email, roles, region, scope_level
        
        Expected Claims Structure:
        {
            'email': 'user@example.com',
            'given_name': 'John',
            'family_name': 'Doe',
            'roles': ['restaurant_owner', 'customer_premium'],
            'region': 'JP',
            'scope_level': 'entity'
        }
        """
        
        def filter_users_by_claims(self, claims: Dict[str, Any]):
            """
            Find existing user by email from OIDC claims
            
            Args:
                claims: OIDC claims dict containing user info
                
            Returns:
                QuerySet of matching users
            """
            email = claims.get('email')
            if not email:
                logger.warning("No email in OIDC claims")
                return self.UserModel.objects.none()
            
            logger.info(f"Looking for user with email: {email}")
            return self.UserModel.objects.filter(email__iexact=email)
        
        @transaction.atomic
        def create_user(self, claims: Dict[str, Any]):
            """
            Create new user from OIDC claims
            
            Args:
                claims: OIDC claims dict
                
            Returns:
                Created user instance
            """
            email = claims.get('email')
            if not email:
                raise ValueError("Email is required to create user")
            
            logger.info(f"Creating new user from OIDC: {email}")
            
            user = self.UserModel.objects.create_user(
                email=email,
                first_name=claims.get('given_name', ''),
                last_name=claims.get('family_name', ''),
                is_active=True
            )
            
            # Sync roles from claims
            self._sync_roles_from_claims(user, claims)
            
            logger.info(f"Successfully created user: {email}")
            return user
        
        @transaction.atomic
        def update_user(self, user, claims: Dict[str, Any]):
            """
            Update existing user from OIDC claims
            
            This is called on every login to keep user info in sync with Keycloak
            
            Args:
                user: User instance to update
                claims: OIDC claims dict
                
            Returns:
                Updated user instance
            """
            logger.info(f"Updating user from OIDC: {user.email}")
            
            # Update basic info
            user.first_name = claims.get('given_name', user.first_name)
            user.last_name = claims.get('family_name', user.last_name)
            
            # Ensure user is active
            if not user.is_active:
                user.is_active = True
            
            user.save()
            
            # Sync roles from OIDC claims to RBAC (full sync)
            self._sync_roles_from_claims(user, claims)
            
            logger.info(f"Successfully updated user: {user.email}")
            return user
        
        def _sync_roles_from_claims(self, user, claims: Dict[str, Any]) -> None:
            """
            Synchronize user roles from OIDC claims to RBAC system
            
            This performs a FULL SYNC - removes all existing roles and assigns
            new ones from Keycloak. Keycloak is the source of truth.
            
            Args:
                user: User instance to sync roles for
                claims: OIDC claims dict containing role information
            """
            from apps.accounts.rbac_models import Role, UserRole, Region
            
            # DEBUG: Print all claims
            print(f"\n🔍 DEBUG - All OIDC claims for {user.email}:")
            print(f"   Claims keys: {list(claims.keys())}")
            print(f"   Full claims: {claims}\n")
            
            roles_from_claims = claims.get('roles', [])
            region_code = claims.get('region', 'JP')
            
            print(f"🎭 Roles from claims: {roles_from_claims}")
            print(f"🌏 Region from claims: {region_code}\n")
            
            logger.info(f"Syncing roles for {user.email}: {roles_from_claims}")
            
            # Get region instance
            try:
                region = Region.objects.get(code=region_code)
            except Region.DoesNotExist:
                logger.error(f"Region not found: {region_code}, using default JP")
                region, _ = Region.objects.get_or_create(
                    code='JP',
                    defaults={
                        'name': 'Japan',
                        'language': 'ja',
                        'timezone': 'Asia/Tokyo',
                        'currency': 'JPY'
                    }
                )
            
            # Remove existing roles (full sync from Keycloak)
            deleted_count = UserRole.objects.filter(user=user).delete()[0]
            if deleted_count > 0:
                logger.info(f"Removed {deleted_count} existing roles")
            
            # Assign new roles from Keycloak claims
            assigned_roles = []
            failed_roles = []
            
            for role_name in roles_from_claims:
                try:
                    role = Role.objects.get(name=role_name)
                    
                    # Determine if role needs region
                    user_role_kwargs = {
                        'user': user,
                        'role': role,
                        'is_active': True
                    }
                    
                    # Region/market scoped roles need region assignment
                    if role.scope_level in ['region', 'market']:
                        user_role_kwargs['region'] = region
                    
                    user_role = UserRole.objects.create(**user_role_kwargs)
                    assigned_roles.append(role_name)
                    logger.debug(f"Assigned role {role_name} to {user.email}")
                    
                except Role.DoesNotExist:
                    logger.warning(f"Role not found in database: {role_name}")
                    failed_roles.append(role_name)
                except Exception as e:
                    logger.error(f"Error assigning role {role_name}: {str(e)}")
                    failed_roles.append(role_name)
            
            logger.info(
                f"Role sync completed for {user.email}: "
                f"{len(assigned_roles)} assigned, {len(failed_roles)} failed"
            )
            
            if failed_roles:
                logger.warning(f"Failed to assign roles: {failed_roles}")
        
        def verify_claims(self, claims: Dict[str, Any]) -> bool:
            """
            Verify that required claims are present
            
            Args:
                claims: OIDC claims dict
                
            Returns:
                True if claims are valid
            """
            required_claims = ['email']
            
            for claim in required_claims:
                if claim not in claims:
                    logger.error(f"Missing required claim: {claim}")
                    return False
            
            # Validate email format
            email = claims.get('email')
            if email and '@' not in email:
                logger.error(f"Invalid email format in claims: {email}")
                return False
            
            return True

else:
    # Placeholder when mozilla-django-oidc not installed
    class TabitabeOIDCBackend:
        """Placeholder - mozilla-django-oidc not installed"""
        
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "mozilla-django-oidc is required for OIDC authentication. "
                "Install with: pip install mozilla-django-oidc"
            )
