"""
Script to import all RBAC roles into Keycloak via Admin API
Reads role definitions from Django and creates them in Keycloak
"""
import requests
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from apps.accounts.rbac_models import Role

# Keycloak configuration
KEYCLOAK_URL = "http://localhost:8081"
REALM = "tabitabe"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"  # Default Keycloak admin password


def get_admin_token():
    """Get admin access token from Keycloak"""
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "client_id": "admin-cli",
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
        "grant_type": "password"
    }
    
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def get_existing_roles(token):
    """Get list of existing roles in Keycloak"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/roles"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return {role["name"]: role for role in response.json()}


def create_role(token, role_data):
    """Create a role in Keycloak"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/roles"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=role_data, headers=headers)
    if response.status_code == 409:
        print(f"  ⚠️  Role '{role_data['name']}' already exists")
        return False
    response.raise_for_status()
    return True


def update_role_attributes(token, role_name, attributes):
    """Update role attributes in Keycloak"""
    # Get role details
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/roles/{role_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    role_data = response.json()
    
    # Update attributes
    role_data["attributes"] = attributes
    
    # Update role
    response = requests.put(url, json=role_data, headers=headers)
    response.raise_for_status()
    return True


def main():
    print("🚀 Importing RBAC roles to Keycloak...")
    print(f"   Keycloak: {KEYCLOAK_URL}")
    print(f"   Realm: {REALM}\n")
    
    try:
        # Get admin token
        print("1️⃣  Getting admin token...")
        token = get_admin_token()
        print("   ✅ Token obtained\n")
        
        # Get existing roles
        print("2️⃣  Checking existing roles in Keycloak...")
        existing_roles = get_existing_roles(token)
        print(f"   Found {len(existing_roles)} existing roles\n")
        
        # Get Django roles
        print("3️⃣  Loading roles from Django database...")
        django_roles = Role.objects.all()
        print(f"   Found {django_roles.count()} roles in Django\n")
        
        # Create/update roles
        print("4️⃣  Creating/updating roles in Keycloak...\n")
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for role in django_roles:
            role_data = {
                "name": role.name,
                "description": role.description,
                "composite": False,
                "clientRole": False,
                "attributes": {
                    "scope_level": [role.scope_level]
                }
            }
            
            if role.name in existing_roles:
                # Update attributes
                print(f"  🔄 Updating role: {role.name}")
                try:
                    update_role_attributes(token, role.name, role_data["attributes"])
                    updated_count += 1
                    print(f"     ✅ Updated")
                except Exception as e:
                    print(f"     ❌ Failed to update: {e}")
                    skipped_count += 1
            else:
                # Create new role
                print(f"  ➕ Creating role: {role.name}")
                try:
                    if create_role(token, role_data):
                        created_count += 1
                        print(f"     ✅ Created")
                    else:
                        skipped_count += 1
                except Exception as e:
                    print(f"     ❌ Failed to create: {e}")
                    skipped_count += 1
        
        # Summary
        print("\n" + "="*60)
        print("📊 SUMMARY:")
        print(f"   ✅ Created: {created_count} roles")
        print(f"   🔄 Updated: {updated_count} roles")
        print(f"   ⚠️  Skipped: {skipped_count} roles")
        print(f"   📋 Total processed: {django_roles.count()} roles")
        print("="*60)
        
        if created_count + updated_count > 0:
            print("\n🎉 Import completed successfully!")
            print("\n📝 Next steps:")
            print("   1. Go to Keycloak admin console")
            print("   2. Assign 'super_admin' role to user admin@tabitabe.com")
            print("   3. Test OIDC login again")
            print(f"\n   Keycloak Users: {KEYCLOAK_URL}/admin/master/console/#/{REALM}/users")
        else:
            print("\n⚠️  No roles were created or updated")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
