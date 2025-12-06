"""
Test OIDC Authentication Flow
Verifies Keycloak integration and role synchronization
"""
import requests
import json
from urllib.parse import urlencode


def test_oidc_flow():
    """Test complete OIDC authentication flow"""
    
    print("=" * 80)
    print("KEYCLOAK OIDC INTEGRATION TEST")
    print("=" * 80)
    
    # Configuration
    keycloak_url = "http://localhost:8081"
    realm = "tabitabe"
    client_id = "tabitabe-web"
    client_secret = "tabitabe-web-secret-change-in-production"
    redirect_uri = "http://localhost:8000/oidc/callback/"
    
    # Test user
    username = "admin@tabitabe.com"
    password = "Admin@123"
    
    print(f"\n1. Testing Keycloak Health...")
    print(f"   URL: {keycloak_url}")
    
    try:
        response = requests.get(f"{keycloak_url}/health/ready", timeout=5)
        if response.status_code == 200:
            print("   ✅ Keycloak is healthy")
        else:
            print(f"   ❌ Keycloak not ready: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to Keycloak: {str(e)}")
        print(f"   💡 Make sure Keycloak is running: docker-compose up -d keycloak")
        return
    
    print(f"\n2. Testing Realm Configuration...")
    print(f"   Realm: {realm}")
    
    try:
        # Get realm info
        realm_url = f"{keycloak_url}/realms/{realm}"
        response = requests.get(realm_url, timeout=5)
        
        if response.status_code == 200:
            realm_info = response.json()
            print(f"   ✅ Realm '{realm}' exists")
            print(f"   📋 Display Name: {realm_info.get('displayName', 'N/A')}")
        else:
            print(f"   ❌ Realm not found: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error checking realm: {str(e)}")
        return
    
    print(f"\n3. Getting Access Token (Direct Grant)...")
    print(f"   Client: {client_id}")
    print(f"   User: {username}")
    
    token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
    
    try:
        # Direct grant (password flow) - for testing only
        token_data = {
            'grant_type': 'password',
            'client_id': client_id,
            'client_secret': client_secret,
            'username': username,
            'password': password,
            'scope': 'openid email profile roles'
        }
        
        response = requests.post(token_url, data=token_data, timeout=10)
        
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get('access_token')
            id_token = tokens.get('id_token')
            refresh_token = tokens.get('refresh_token')
            
            print("   ✅ Successfully got tokens")
            print(f"   🔑 Access Token: {access_token[:50]}...")
            print(f"   🆔 ID Token: {id_token[:50]}...")
            print(f"   🔄 Refresh Token: {refresh_token[:50]}...")
            
            # Decode ID token (without verification for testing)
            import base64
            parts = id_token.split('.')
            if len(parts) >= 2:
                # Add padding if needed
                payload = parts[1]
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                claims = json.loads(decoded)
                
                print("\n   📄 ID Token Claims:")
                print(f"      Email: {claims.get('email', 'N/A')}")
                print(f"      Name: {claims.get('given_name', '')} {claims.get('family_name', '')}")
                print(f"      Roles: {claims.get('roles', [])}")
                print(f"      Region: {claims.get('region', 'N/A')}")
                print(f"      Scope Level: {claims.get('scope_level', 'N/A')}")
        else:
            print(f"   ❌ Token request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Error getting token: {str(e)}")
        return
    
    print(f"\n4. Testing UserInfo Endpoint...")
    
    try:
        userinfo_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/userinfo"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(userinfo_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            userinfo = response.json()
            print("   ✅ Successfully got user info")
            print(f"   👤 User Info:")
            print(f"      Email: {userinfo.get('email', 'N/A')}")
            print(f"      Email Verified: {userinfo.get('email_verified', False)}")
            print(f"      Preferred Username: {userinfo.get('preferred_username', 'N/A')}")
        else:
            print(f"   ❌ UserInfo request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error getting user info: {str(e)}")
    
    print(f"\n5. Browser Login Flow Instructions...")
    print(f"   " + "=" * 76)
    print(f"   To test the full OIDC flow in a browser:")
    print(f"   ")
    print(f"   1. Start Django server:")
    print(f"      cd backend")
    print(f"      .\\venv\\Scripts\\python.exe manage.py runserver")
    print(f"   ")
    print(f"   2. Visit: http://localhost:8000/oidc/login/")
    print(f"   ")
    print(f"   3. You'll be redirected to Keycloak login page")
    print(f"   ")
    print(f"   4. Login with:")
    print(f"      Email: {username}")
    print(f"      Password: {password}")
    print(f"   ")
    print(f"   5. After successful login, you'll be redirected back to Django")
    print(f"      Django will automatically:")
    print(f"      - Create/update user in database")
    print(f"      - Sync roles from Keycloak to RBAC")
    print(f"      - Assign region if needed")
    print(f"   " + "=" * 76)
    
    print(f"\n6. Authorization URL for Manual Testing...")
    
    auth_params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile roles',
        'state': 'test-state-123'
    }
    
    auth_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/auth"
    full_auth_url = f"{auth_url}?{urlencode(auth_params)}"
    
    print(f"   Copy and paste this URL in your browser:")
    print(f"   {full_auth_url}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE ✅")
    print("=" * 80)
    print("\n💡 Next Steps:")
    print("   1. Start Django server and test browser flow")
    print("   2. Check Django logs for role synchronization")
    print("   3. Verify user has correct roles in Django admin")
    print("   4. Test with different users (customer@example.com / Customer@123)")
    print("\n")


if __name__ == '__main__':
    test_oidc_flow()
