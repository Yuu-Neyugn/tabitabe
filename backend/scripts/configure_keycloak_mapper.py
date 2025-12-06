"""
Script to configure Keycloak Client Scope Mapper for Roles
This adds realm roles to ID token so Django can sync them
"""
import requests
import json
from typing import Dict, Any

# Keycloak configuration
KEYCLOAK_URL = "http://localhost:8081"
REALM = "tabitabe"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"  # Change if different
CLIENT_ID = "django-backend"

def get_admin_token() -> str:
    """Get admin access token"""
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        'client_id': 'admin-cli',
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD,
        'grant_type': 'password'
    }
    
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()['access_token']

def get_client_uuid(token: str) -> str:
    """Get client UUID by client ID"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients"
    headers = {'Authorization': f'Bearer {token}'}
    params = {'clientId': CLIENT_ID}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    clients = response.json()
    if not clients:
        raise ValueError(f"Client '{CLIENT_ID}' not found")
    
    return clients[0]['id']

def create_roles_mapper(token: str, client_uuid: str) -> Dict[str, Any]:
    """
    Create protocol mapper to add realm roles to ID token
    
    This mapper will:
    1. Get all realm roles assigned to the user
    2. Add them to ID token as 'roles' claim
    3. Make them available in userinfo endpoint
    """
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_uuid}/protocol-mappers/models"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Check if mapper already exists
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    existing_mappers = response.json()
    
    for mapper in existing_mappers:
        if mapper['name'] == 'realm-roles-to-id-token':
            print(f"✅ Mapper 'realm-roles-to-id-token' already exists (ID: {mapper['id']})")
            return mapper
    
    # Create new mapper
    mapper_config = {
        "name": "realm-roles-to-id-token",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-usermodel-realm-role-mapper",
        "consentRequired": False,
        "config": {
            "claim.name": "roles",
            "jsonType.label": "String",
            "multivalued": "true",
            "userinfo.token.claim": "true",
            "id.token.claim": "true",
            "access.token.claim": "true"
        }
    }
    
    response = requests.post(url, headers=headers, json=mapper_config)
    response.raise_for_status()
    
    print(f"✅ Created mapper 'realm-roles-to-id-token'")
    return mapper_config

def verify_user_roles(token: str, email: str) -> None:
    """Verify user has roles assigned"""
    # Get user ID
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users"
    headers = {'Authorization': f'Bearer {token}'}
    params = {'email': email, 'exact': 'true'}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    users = response.json()
    
    if not users:
        print(f"❌ User {email} not found")
        return
    
    user_id = users[0]['id']
    print(f"\n👤 User: {email} (ID: {user_id})")
    
    # Get user's realm roles
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/role-mappings/realm"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    roles = response.json()
    print(f"📋 Assigned Realm Roles: {len(roles)}")
    for role in roles:
        print(f"   - {role['name']}")
    
    if not roles:
        print("⚠️  WARNING: User has no realm roles assigned!")
        print("   Go to Keycloak UI → Users → Role mapping → Assign role")

def main():
    """Main execution"""
    print("🔧 Configuring Keycloak Client Scope Mapper for Roles")
    print("=" * 60)
    
    try:
        # Step 1: Get admin token
        print("\n1️⃣ Authenticating as admin...")
        token = get_admin_token()
        print("   ✅ Admin token obtained")
        
        # Step 2: Get client UUID
        print(f"\n2️⃣ Finding client '{CLIENT_ID}'...")
        client_uuid = get_client_uuid(token)
        print(f"   ✅ Client UUID: {client_uuid}")
        
        # Step 3: Create roles mapper
        print("\n3️⃣ Creating protocol mapper for realm roles...")
        mapper = create_roles_mapper(token, client_uuid)
        print(f"   ✅ Mapper configured")
        print(f"   📝 Mapper will add 'roles' claim to ID token")
        
        # Step 4: Verify test users
        print("\n4️⃣ Verifying test users...")
        verify_user_roles(token, "admin3@tabitabe.com")
        verify_user_roles(token, "admin@tabitabe.com")
        
        print("\n" + "=" * 60)
        print("✅ Configuration complete!")
        print("\n📋 Next steps:")
        print("1. Clear Django session: http://localhost:8000/accounts/test/oidc/clear-session/")
        print("2. Login again with OIDC")
        print("3. Click 'Force Sync Roles' to verify roles appear in claims")
        print("\n💡 Expected claims after login:")
        print('   { "email": "admin3@tabitabe.com", "roles": ["super_admin"], "region": "JP" }')
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
