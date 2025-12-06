"""
OIDC Logout view
Clears Django session and OIDC tokens
"""
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def oidc_logout_view(request):
    """
    Clear Django session and OIDC tokens, then redirect to test page
    """
    user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
    logger.info(f"User {user_email} logging out")
    
    # Clear Django session (this also clears OIDC tokens)
    logout(request)
    
    logger.info(f"Session cleared for {user_email}")
    
    return redirect('/accounts/test/oidc/')


@require_http_methods(["GET"])
def clear_session_view(request):
    """
    Debug endpoint to forcefully clear session
    """
    if request.user.is_authenticated:
        user_email = request.user.email
        logout(request)
        message = f"✅ Session cleared for {user_email}"
    else:
        message = "ℹ️ No active session"
    
    return HttpResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Session Cleared</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 100px auto;
                padding: 20px;
                text-align: center;
            }}
            .message {{
                background: #e8f5e9;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                font-size: 18px;
            }}
            a {{
                display: inline-block;
                margin: 10px;
                padding: 12px 24px;
                background: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <h1>🔓 Session Management</h1>
        <div class="message">{message}</div>
        <a href="/accounts/test/oidc/">Back to Login Test</a>
    </body>
    </html>
    """)
