import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.rbac_models import Role, Region

print(f"✅ Roles in database: {Role.objects.count()}")
print(f"✅ Regions in database: {Region.objects.count()}")

if Role.objects.count() > 0:
    print("\n📋 Available roles:")
    for role in Role.objects.all().order_by('scope_level', 'name'):
        print(f"   - {role.name} (scope: {role.scope_level})")

if Region.objects.count() > 0:
    print("\n🌍 Available regions:")
    for region in Region.objects.all():
        print(f"   - {region.code}: {region.name}")
