# Tabitabe Backend

Django backend for Tabitabe Restaurant Discovery Platform.

## Quick Start

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements/dev.txt
```

### 3. Setup Environment Variables

```bash
# Copy .env.example from root
cp ../.env.example ../.env.development
# Edit .env.development with your settings
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit http://localhost:8000/admin/

## Project Structure

```
backend/
├── config/              # Django settings
│   ├── settings/
│   │   ├── base.py     # Base settings
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/               # Django applications
│   ├── accounts/      # User authentication
│   ├── restaurants/   # Restaurant management
│   ├── customers/     # Customer features
│   ├── reviews/       # Review system
│   ├── campaigns/     # Gift cards & stamp rallies
│   ├── media_manager/ # Media handling
│   ├── notifications/ # Email/Push notifications
│   └── core/          # Shared utilities
├── api/               # REST API
│   └── v1/
│       ├── auth/
│       ├── customers/
│       ├── restaurants/
│       └── admin/
├── tests/             # Test suites
├── requirements/      # Python dependencies
└── docker/            # Docker configurations
```

## Commands

### Run Celery Worker

```bash
celery -A config worker -l info
```

### Run Celery Beat

```bash
celery -A config beat -l info
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black .
ruff check .
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Schema: http://localhost:8000/api/schema/

## Features Implemented

### ✅ RBAC (Role-Based Access Control) - 2025/12/07

完全なRBACシステムを実装:

**Models:**
- `Role` - 15種類のロール (super_admin, customer_free, customer_premium, restaurant_owner, restaurant_staff, など)
- `Permission` - 32種類のパーミッション (細かいアクセス制御)
- `UserRole` - ユーザーとロールの多対多関係
- `RolePermission` - ロールとパーミッションのマッピング
- `Region` - マルチリージョン対応 (JP, US, VN, など)

**Scope Levels:**
- Global: システム全体
- Region: 地域レベル
- Market: 市場レベル  
- Entity: エンティティレベル

**テスト:** 16/20 passing (80%)

### ✅ OIDC Authentication with Keycloak - 2025/12/07

Keycloakを使用したOpenID Connect認証を完全実装:

**Infrastructure:**
- Keycloak v23.0 (Docker Compose)
- Realm: `tabitabe`
- Client: `django-backend`
- PostgreSQL backend for Keycloak

**Features:**
- ✅ OIDC認証フロー完全動作
- ✅ Keycloakからの自動ロール同期
- ✅ リージョン自動割り当て
- ✅ Force sync endpoint (手動同期)
- ✅ Session management (logout/clear)
- ✅ Test page with full controls

**Backend:**
- Custom `TabitabeOIDCBackend` with role synchronization
- Protocol mapper: `realm-roles-to-id-token` 
- Automatic user provisioning from OIDC claims
- Full transaction-based role sync

**Configuration:**
```python
# settings.py
AUTHENTICATION_BACKENDS = [
    'apps.accounts.oidc_backend.TabitabeOIDCBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

**Test Users:**
- `admin@tabitabe.com` / `Admin@123` - super_admin role
- `admin3@tabitabe.com` / `Admin@123` - super_admin role

**Test Page:** http://localhost:8000/accounts/test/oidc/

**Scripts:**
- `scripts/import_keycloak_roles.py` - Import Django roles to Keycloak
- `scripts/configure_keycloak_mapper.py` - Setup protocol mapper for roles

**Status:** Production ready ✅

### 🚧 Pending Features

- [ ] Google OAuth2 integration
- [ ] Line Login integration  
- [ ] DRF API endpoints for OIDC
- [ ] Integration tests for OIDC flow
- [ ] Social login UI components

## OIDC Setup Guide

### 1. Start Keycloak

```bash
cd backend
docker-compose up -d keycloak
```

Keycloak UI: http://localhost:8081 (admin/admin)

### 2. Import Roles to Keycloak

```bash
python scripts/import_keycloak_roles.py
```

### 3. Configure Protocol Mapper

```bash
python scripts/configure_keycloak_mapper.py
```

### 4. Test OIDC Login

Visit: http://localhost:8000/accounts/test/oidc/

**Test Actions:**
- Login with OIDC → Redirect to Keycloak
- Force Sync Roles → Manual role synchronization  
- Clear Session → Remove session data
- Check Current Session → View user info and roles

### 5. Verify Role Sync

After login, check JSON response:

```json
{
  "rbac": {
    "roles": [{
      "name": "super_admin",
      "scope_level": "global"
    }],
    "regions": [{
      "code": "JP",
      "name": "Japan"
    }]
  },
  "debug": {
    "user_roles_in_db": 1,
    "oidc_backend_used": true
  }
}
```
