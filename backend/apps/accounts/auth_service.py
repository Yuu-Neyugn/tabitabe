"""
Authentication Service Layer - Abstraction for multiple auth methods
Provides unified interface for Email/Password and future OIDC authentication
"""
from typing import Optional, Dict, Tuple, List
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.rbac_models import Role, UserRole, Region
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthenticationService:
    """
    Authentication service providing unified interface
    
    Current: Email/Password authentication
    Future: Will handle OIDC/OAuth2 flows
    """
    
    @staticmethod
    def authenticate_user(
        email: str,
        password: str,
        auth_method: str = 'email'
    ) -> Optional[User]:
        """
        Authenticate user with given credentials
        
        Args:
            email: User email
            password: User password
            auth_method: Authentication method ('email', 'oidc', etc.)
            
        Returns:
            User object if successful, None otherwise
        """
        if auth_method == 'email':
            return authenticate(username=email, password=password)
        
        # Future: Handle OIDC authentication
        # elif auth_method == 'oidc':
        #     return OIDCAuthenticationService.authenticate(email, token)
        
        logger.warning(f"Unknown auth method: {auth_method}")
        return None
    
    @staticmethod
    def generate_tokens(user: User) -> Dict[str, str]:
        """
        Generate JWT tokens for user
        
        Returns:
            Dict with 'access' and 'refresh' tokens
            
        Future: Tokens will include OIDC claims
        """
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims (compatible with future OIDC structure)
        refresh['email'] = user.email
        refresh['user_type'] = user.user_type if hasattr(user, 'user_type') else None
        
        # Add RBAC roles to token
        active_roles = user.get_active_roles()
        refresh['roles'] = [role.name for role in active_roles]
        
        # Add regions if user has region-scoped roles
        regions = user.get_regions()
        if regions:
            refresh['regions'] = [region.code for region in regions]
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
    
    @staticmethod
    @transaction.atomic
    def register_user(
        email: str,
        password: str,
        user_type: str = 'customer',
        **extra_fields
    ) -> Tuple[User, Dict[str, str]]:
        """
        Register new user
        
        Args:
            email: User email
            password: User password
            user_type: User type (customer, restaurant, etc.)
            **extra_fields: Additional user fields
            
        Returns:
            Tuple of (User, tokens_dict)
        """
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            **extra_fields
        )
        
        # Assign default role based on user type
        AuthenticationService._assign_default_role(user, user_type)
        
        # Generate tokens
        tokens = AuthenticationService.generate_tokens(user)
        
        logger.info(f"New user registered: {email} (type: {user_type})")
        return user, tokens
    
    @staticmethod
    def _assign_default_role(user: User, user_type: str) -> None:
        """
        Assign default role to new user
        
        Future: This will be handled by OIDC claims
        """
        role_mapping = {
            'customer': 'customer_free',
            'restaurant': 'restaurant_owner',
            'admin': 'super_admin',
        }
        
        role_name = role_mapping.get(user_type.lower(), 'customer_free')
        
        try:
            role = Role.objects.get(name=role_name)
            UserRole.objects.create(
                user=user,
                role=role,
                is_active=True
            )
        except Role.DoesNotExist:
            logger.error(f"Default role not found: {role_name}")
    
    @staticmethod
    def refresh_user_permissions(user: User) -> None:
        """
        Refresh user permissions from external source
        
        Current: No-op for email auth
        Future: Will sync roles from OIDC provider
        """
        # For email auth, permissions are managed internally
        # For OIDC, this will fetch latest claims and sync roles
        pass


class OIDCAuthenticationService:
    """
    OIDC-specific authentication service (for future use)
    
    This class will handle:
    - OIDC authorization code flow
    - Token validation
    - Claims parsing
    - Role synchronization
    """
    
    @staticmethod
    def initiate_authorization_flow(
        provider: str,
        redirect_uri: str,
        state: str
    ) -> str:
        """
        Initiate OIDC authorization flow
        
        Args:
            provider: OIDC provider (keycloak, google, line, azure)
            redirect_uri: Callback URL
            state: State parameter for CSRF protection
            
        Returns:
            Authorization URL to redirect user
        """
        # To be implemented when migrating to OIDC
        raise NotImplementedError("OIDC not yet implemented")
    
    @staticmethod
    def handle_callback(
        code: str,
        state: str,
        provider: str
    ) -> Tuple[User, Dict[str, str]]:
        """
        Handle OIDC callback
        
        Args:
            code: Authorization code
            state: State parameter
            provider: OIDC provider
            
        Returns:
            Tuple of (User, tokens_dict)
        """
        # To be implemented when migrating to OIDC
        raise NotImplementedError("OIDC not yet implemented")
    
    @staticmethod
    def validate_token(token: str, provider: str) -> Optional[Dict]:
        """
        Validate OIDC token and extract claims
        
        Args:
            token: ID token or access token
            provider: OIDC provider
            
        Returns:
            Claims dict if valid, None otherwise
        """
        # To be implemented when migrating to OIDC
        raise NotImplementedError("OIDC not yet implemented")
    
    @staticmethod
    def sync_roles_from_claims(user: User, claims: Dict) -> None:
        """
        Synchronize user roles from OIDC claims
        
        Args:
            user: User instance
            claims: OIDC claims dictionary
        """
        # To be implemented when migrating to OIDC
        raise NotImplementedError("OIDC not yet implemented")


class AuthProviderRegistry:
    """
    Registry for authentication providers
    
    Allows easy addition of new auth providers without modifying core code
    """
    
    _providers: Dict[str, 'AuthProvider'] = {}
    
    @classmethod
    def register(cls, name: str, provider: 'AuthProvider'):
        """Register authentication provider"""
        cls._providers[name] = provider
        logger.info(f"Registered auth provider: {name}")
    
    @classmethod
    def get_provider(cls, name: str) -> Optional['AuthProvider']:
        """Get authentication provider by name"""
        return cls._providers.get(name)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered providers"""
        return list(cls._providers.keys())


class AuthProvider:
    """
    Base class for authentication providers
    
    Subclass this to add new authentication methods
    """
    
    def authenticate(self, credentials: Dict) -> Optional[User]:
        """Authenticate user with given credentials"""
        raise NotImplementedError
    
    def get_user_info(self, token: str) -> Optional[Dict]:
        """Get user info from token"""
        raise NotImplementedError
    
    def sync_user(self, user: User, external_data: Dict) -> User:
        """Sync user data from external source"""
        raise NotImplementedError


# Register default email provider
class EmailAuthProvider(AuthProvider):
    """Email/password authentication provider"""
    
    def authenticate(self, credentials: Dict) -> Optional[User]:
        return AuthenticationService.authenticate_user(
            email=credentials.get('email'),
            password=credentials.get('password'),
            auth_method='email'
        )
    
    def get_user_info(self, token: str) -> Optional[Dict]:
        # Email auth doesn't use external tokens
        return None
    
    def sync_user(self, user: User, external_data: Dict) -> User:
        # No external sync for email auth
        return user


# Register email provider
AuthProviderRegistry.register('email', EmailAuthProvider())
