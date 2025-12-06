# Keycloak OIDC Integration Guide

## 📋 Tổng quan

Tabitabe đã tích hợp **Keycloak** làm Identity Provider (IdP) với đầy đủ RBAC roles.

### Chi phí triển khai

#### Local Development (MIỄN PHÍ) ✅
- ✅ Keycloak chạy trong Docker container
- ✅ Không tốn phí
- ✅ Cấu hình sẵn trong `docker-compose.yml`

#### Production Deployment
**Option 1: Self-hosted (Rẻ nhất)**
- VM/VPS: $10-50/tháng (AWS EC2 t3.medium, DigitalOcean, etc.)
- Keycloak chạy trong Docker
- PostgreSQL share với Django
- Total: ~$15-60/tháng

**Option 2: Managed Keycloak**
- Red Hat SSO: ~$200/tháng
- Keycloak-as-a-Service: $50-150/tháng
- Total: $50-200/tháng

**Option 3: Hybrid (Khuyến nghị)**
- Social login providers (Google/Line) MIỄN PHÍ
- Keycloak self-hosted: $10-50/tháng
- Total: ~$15-60/tháng

### Kiến trúc Authentication

```
User → Frontend → Keycloak (OIDC) → Django Backend
                      ↓
                Social Providers
                (Google, Line)
```

## 🚀 Bắt đầu

### 1. Start Keycloak

```powershell
cd c:\Users\nguyen.nguyencao\Desktop\Personal\tabitabe
docker-compose up -d keycloak
```

### 2. Truy cập Keycloak Admin Console

- URL: http://localhost:8081
- Username: `admin`
- Password: `admin`

### 3. Kiểm tra Realm Import

Keycloak sẽ tự động import realm `tabitabe` với:
- ✅ 15 RBAC roles (super_admin, restaurant_owner, customer_free, etc.)
- ✅ 3 clients (tabitabe-web, tabitabe-mobile, tabitabe-admin)
- ✅ 2 test users:
  - `admin@tabitabe.com` / `Admin@123` → super_admin role
  - `customer@example.com` / `Customer@123` → customer_free role
- ✅ Protocol mappers (email, roles, region, scope_level)

## 🔧 Cấu hình Django

### Environment Variables

Thêm vào file `.env.development`:

```env
# Keycloak OIDC
OIDC_RP_CLIENT_ID=tabitabe-web
OIDC_RP_CLIENT_SECRET=tabitabe-web-secret-change-in-production
OIDC_OP_AUTHORIZATION_ENDPOINT=http://localhost:8081/realms/tabitabe/protocol/openid-connect/auth
OIDC_OP_TOKEN_ENDPOINT=http://localhost:8081/realms/tabitabe/protocol/openid-connect/token
OIDC_OP_USER_ENDPOINT=http://localhost:8081/realms/tabitabe/protocol/openid-connect/userinfo
OIDC_OP_JWKS_ENDPOINT=http://localhost:8081/realms/tabitabe/protocol/openid-connect/certs
```

### Authentication Backends

`config/settings/base.py` đã được cấu hình:

```python
AUTHENTICATION_BACKENDS = [
    'apps.accounts.oidc_backend.TabitabeOIDCBackend',  # Keycloak OIDC
    'apps.accounts.auth_backends.EmailBackend',        # Email/Password fallback
    'apps.accounts.auth_backends.RBACPermissionBackend', # RBAC permissions
    'guardian.backends.ObjectPermissionBackend',       # Object permissions
]
```

## 🧪 Testing OIDC Login

### Method 1: Django Admin

1. Start Django server:
```powershell
cd backend
.\venv\Scripts\python.exe manage.py runserver
```

2. Truy cập: http://localhost:8000/oidc/login/
3. Sẽ redirect đến Keycloak login
4. Login bằng:
   - `admin@tabitabe.com` / `Admin@123`
   - hoặc `customer@example.com` / `Customer@123`
5. Sau khi login thành công, redirect về Django

### Method 2: API Testing

```python
# Test OIDC authentication flow
import requests

# 1. Get authorization code
auth_url = "http://localhost:8081/realms/tabitabe/protocol/openid-connect/auth"
params = {
    'client_id': 'tabitabe-web',
    'response_type': 'code',
    'redirect_uri': 'http://localhost:8000/oidc/callback/',
    'scope': 'openid email profile roles'
}

# User visits this URL in browser
print(f"{auth_url}?{'&'.join([f'{k}={v}' for k,v in params.items()])}")

# 2. After login, Keycloak redirects to callback with code
# Django handles token exchange automatically via TabitabeOIDCBackend
```

## 📊 Role Synchronization

### OIDC Claims → RBAC Roles

Khi user login qua Keycloak, `TabitabeOIDCBackend` tự động:

1. **Extract claims** từ ID token:
```json
{
  "email": "user@example.com",
  "given_name": "John",
  "family_name": "Doe",
  "roles": ["restaurant_owner", "customer_premium"],
  "region": "JP",
  "scope_level": "entity"
}
```

2. **Sync to RBAC**:
   - Xóa tất cả roles cũ của user
   - Assign roles mới từ Keycloak
   - Assign region nếu role scope là `region` hoặc `market`

3. **Update user info**:
   - First name, last name
   - Activate user nếu inactive

### Code Flow

```python
# apps/accounts/oidc_backend.py

class TabitabeOIDCBackend(BaseOIDCBackend):
    def update_user(self, user, claims):
        # Update basic info
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save()
        
        # Sync roles from Keycloak to RBAC
        self._sync_roles_from_claims(user, claims)
        return user
```

## 🔐 Managing Users in Keycloak

### Add New User

1. Keycloak Admin → Users → Add user
2. Set email, first name, last name
3. Credentials tab → Set password
4. Role Mappings tab → Assign realm roles
5. Attributes tab → Set custom attributes:
   - `region`: JP, US, etc.
   - `scope_level`: global, region, entity

### Modify User Roles

1. Users → Find user → Role Mappings
2. Available Roles → Select roles → Add selected
3. Next login, Django sẽ tự động sync

### Disable User

1. Users → Find user → Details
2. Enabled: OFF
3. User không thể login

## 🌐 Social Login Integration

### Google Login

1. Keycloak Admin → Identity Providers → Add provider → Google
2. Nhập Google Client ID & Secret (https://console.cloud.google.com)
3. Mapper: Map Google email → Keycloak email
4. Default role: `customer_free`

**Chi phí**: MIỄN PHÍ (Google OAuth2 không tính phí)

### Line Login

1. Keycloak Admin → Identity Providers → Add provider → OpenID Connect
2. Config:
   - Alias: `line`
   - Display Name: `LINE`
   - Authorization URL: `https://access.line.me/oauth2/v2.1/authorize`
   - Token URL: `https://api.line.me/oauth2/v2.1/token`
   - Client ID: LINE Channel ID
   - Client Secret: LINE Channel Secret
3. Mapper: Map Line email → Keycloak email

**Chi phí**: MIỄN PHÍ (Line Login không tính phí)

### Facebook Login

Tương tự Google Login.

**Chi phí**: MIỄN PHÍ

## 📈 Scaling Considerations

### Database

Keycloak dùng chung PostgreSQL với Django:
- Development: OK
- Production: Nên tách riêng database cho Keycloak

### High Availability

Production nên setup:
- 2+ Keycloak instances (load balanced)
- Shared database
- Redis cache cho sessions

**Chi phí**: +$20-50/tháng cho thêm 1 instance

### Monitoring

- Keycloak metrics: Built-in
- Log aggregation: ELK stack hoặc CloudWatch
- Uptime monitoring: UptimeRobot (free)

## 🔧 Troubleshooting

### Keycloak không start

```powershell
# Check logs
docker-compose logs keycloak

# Common issue: PostgreSQL chưa ready
docker-compose up -d postgres
# Wait 10 seconds
docker-compose up -d keycloak
```

### OIDC login redirect loop

Check:
1. `OIDC_RP_CLIENT_ID` đúng với client ID trong Keycloak
2. `OIDC_RP_CLIENT_SECRET` khớp
3. Redirect URI trong Keycloak client settings: `http://localhost:8000/oidc/callback/`

### Role không sync

Check logs:
```powershell
# Django logs
cd backend
.\venv\Scripts\python.exe manage.py runserver

# Look for:
# "Syncing roles for user@example.com: ['role1', 'role2']"
# "Assigned role X to user@example.com"
```

### Token expired

Token lifetime: 1 hour (configurable)

Keycloak Admin → Realm Settings → Tokens:
- Access Token Lifespan: 1 hour
- Refresh Token Lifespan: 7 days

## 📚 Next Steps

1. **Test OIDC Login Flow** ✅
   ```powershell
   docker-compose up -d keycloak
   cd backend
   .\venv\Scripts\python.exe manage.py runserver
   # Visit: http://localhost:8000/oidc/login/
   ```

2. **Create API Endpoints** 🔧
   - `/api/v1/auth/oidc/login/` - Initiate OIDC flow
   - `/api/v1/auth/oidc/callback/` - Handle callback
   - `/api/v1/auth/me/` - Get current user + roles

3. **Setup Social Login** 🌐
   - Google OAuth2 credentials
   - Line Login channel
   - Configure in Keycloak

4. **Production Deployment** 🚀
   - Setup production Keycloak instance
   - Configure HTTPS
   - Update redirect URIs
   - Change default passwords

## 💰 Cost Summary

| Component | Development | Production |
|-----------|-------------|------------|
| Keycloak | FREE | $10-50/month |
| Social Login (Google, Line) | FREE | FREE |
| Database | FREE (shared) | $10-20/month (dedicated) |
| **Total** | **FREE** | **$20-70/month** |

### Cost Optimization Tips

1. **Self-host Keycloak** thay vì dùng managed service → Save $150/month
2. **Share PostgreSQL** với Django trong development
3. **Use social login** cho majority users → Reduce user management overhead
4. **Single Keycloak instance** in production initially → Upgrade khi scale

## 🎯 Benefits

✅ **Security**: Industry-standard OIDC/OAuth2
✅ **Flexibility**: Easy to add social providers
✅ **Scalability**: Keycloak handles millions of users
✅ **Separation of Concerns**: Auth logic độc lập khỏi Django
✅ **Enterprise Ready**: Government SSO support
✅ **Cost Effective**: Chỉ $20-70/month in production

---

**Ready to go!** 🚀

Start với:
```powershell
docker-compose up -d keycloak
```
