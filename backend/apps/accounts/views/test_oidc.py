"""
Test views for OIDC authentication flow
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
@login_required
def oidc_success(request):
    """
    View to test OIDC login success.
    Shows user information and roles after successful authentication.
    """
    user = request.user
    
    # Get user roles and permissions
    roles = []
    if hasattr(user, 'get_active_roles'):
        roles = [{'id': str(role.id), 'name': role.name, 'scope_level': role.scope_level} 
                 for role in user.get_active_roles()]
    
    # Get user regions
    regions = []
    if hasattr(user, 'get_regions'):
        regions = [{'code': region.code, 'name': region.name} 
                   for region in user.get_regions()]
    
    # Debug info
    from apps.accounts.rbac_models import UserRole
    user_roles_count = UserRole.objects.filter(user=user).count()
    
    return JsonResponse({
        'success': True,
        'message': 'OIDC authentication successful!',
        'user': {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'is_active': user.is_active,
        },
        'authentication': {
            'backend': request.session.get('_auth_user_backend', 'Unknown'),
            'has_oidc_access_token': 'oidc_access_token' in request.session,
            'has_oidc_id_token': 'oidc_id_token' in request.session,
        },
        'rbac': {
            'roles': roles,
            'regions': regions,
        },
        'debug': {
            'user_roles_in_db': user_roles_count,
            'roles_method_available': hasattr(user, 'get_active_roles'),
            'oidc_backend_used': 'TabitabeOIDCBackend' in request.session.get('_auth_user_backend', ''),
            'session_keys': list(request.session.keys()),
        },
    }, json_dumps_params={'ensure_ascii': False, 'indent': 2})


@require_http_methods(["GET"])
def oidc_test_page(request):
    """
    Simple HTML page to initiate OIDC login
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OIDC Login Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                margin-top: 0;
            }
            .info {
                background-color: #e3f2fd;
                padding: 15px;
                border-left: 4px solid #2196F3;
                margin: 20px 0;
            }
            .button {
                display: inline-block;
                padding: 12px 24px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin: 10px 5px;
                font-size: 16px;
            }
            .button:hover {
                background-color: #45a049;
            }
            .button.secondary {
                background-color: #2196F3;
            }
            .button.secondary:hover {
                background-color: #0b7dda;
            }
            ul {
                line-height: 1.8;
            }
            code {
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 OIDC Authentication Test</h1>
            
            <div class="info">
                <h3>📋 Test Information</h3>
                <ul>
                    <li><strong>Keycloak URL:</strong> http://localhost:8081</li>
                    <li><strong>Realm:</strong> tabitabe</li>
                    <li><strong>Client ID:</strong> tabitabe-web</li>
                </ul>
            </div>

            <h3>🧪 Test Accounts</h3>
            <p><strong>Admin User:</strong></p>
            <ul>
                <li>Email: <code>admin@tabitabe.com</code></li>
                <li>Password: <code>Admin@123</code></li>
                <li>Role: super_admin</li>
            </ul>

            <p><strong>Customer User:</strong></p>
            <ul>
                <li>Email: <code>customer@example.com</code></li>
                <li>Password: <code>Customer@123</code></li>
                <li>Role: customer_free</li>
            </ul>

            <h3>🚀 Actions</h3>
            <a href="/oidc/authenticate/?next=/accounts/test/oidc/success/" class="button">
                Login with OIDC
            </a>
            <a href="/accounts/test/oidc/success/" class="button secondary">
                Check Current Session
            </a>
            <button onclick="forceSync()" class="button" style="background-color: #9c27b0;">
                🔄 Force Sync Roles
            </button>
            <a href="/accounts/test/oidc/clear-session/" class="button" style="background-color: #ff9800;">
                Clear Session
            </a>
            <a href="/oidc/logout/" class="button" style="background-color: #f44336;">
                Logout
            </a>
            
            <div id="sync-result" style="display: none; margin-top: 20px; padding: 15px; border-radius: 4px;"></div>
            
            <script>
            async function forceSync() {
                const resultDiv = document.getElementById('sync-result');
                resultDiv.style.display = 'block';
                resultDiv.style.backgroundColor = '#e3f2fd';
                resultDiv.style.borderLeft = '4px solid #2196F3';
                resultDiv.innerHTML = '⏳ Syncing roles from Keycloak...';
                
                try {
                    const response = await fetch('/accounts/test/oidc/force-sync/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        }
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        resultDiv.style.backgroundColor = '#e8f5e9';
                        resultDiv.style.borderColor = '#4CAF50';
                        resultDiv.innerHTML = `
                            <h4>✅ ${data.message}</h4>
                            <p><strong>User:</strong> ${data.user}</p>
                            <p><strong>Roles:</strong> ${JSON.stringify(data.roles, null, 2)}</p>
                            <p><strong>Claims:</strong> ${JSON.stringify(data.claims_preview, null, 2)}</p>
                            <br>
                            <a href="/accounts/test/oidc/success/" class="button secondary">View Full Details</a>
                        `;
                    } else {
                        resultDiv.style.backgroundColor = '#ffebee';
                        resultDiv.style.borderColor = '#f44336';
                        resultDiv.innerHTML = `
                            <h4>❌ Sync Failed</h4>
                            <p>${data.message}</p>
                            <p><strong>Error:</strong> ${data.error}</p>
                        `;
                    }
                } catch (error) {
                    resultDiv.style.backgroundColor = '#ffebee';
                    resultDiv.style.borderColor = '#f44336';
                    resultDiv.innerHTML = `<h4>❌ Error</h4><p>${error.message}</p>`;
                }
            }
            
            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            </script>

            <div class="info" style="margin-top: 30px; background-color: #fff3cd; border-color: #ffc107;">
                <h4>ℹ️ How it works:</h4>
                <ol>
                    <li>Click "Login with OIDC" to redirect to Keycloak</li>
                    <li>Login with one of the test accounts</li>
                    <li>You'll be redirected back to success page</li>
                    <li>View your user info, roles, and regions</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """
    from django.http import HttpResponse
    return HttpResponse(html)
