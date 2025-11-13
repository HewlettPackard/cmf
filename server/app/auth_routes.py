"""
OAuth2 Authentication Routes for Google Login
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from server.app.auth_config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
    FRONTEND_URL,
    AUTH_ENABLED
)
from server.app.auth_utils import (
    create_access_token,
    set_auth_cookie,
    clear_auth_cookie,
    get_current_user_from_cookie,
    validate_email_domain,
    create_user_session_data
)
from typing import Dict, Any

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Configure OAuth
config = Config(environ={
    "GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": GOOGLE_CLIENT_SECRET
})

oauth = OAuth(config)

# Register Google OAuth provider
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': ' '.join(GOOGLE_SCOPES)
    }
)


@router.get("/login/google")
async def login_google(request: Request):
    """
    Initiate Google OAuth login flow
    
    Returns:
        Redirect to Google's authorization page
    """
    if not AUTH_ENABLED:
        raise HTTPException(status_code=403, detail="Authentication is disabled")
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured properly"
        )
    
    redirect_uri = GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request):
    """
    Handle Google OAuth callback
    
    Returns:
        Redirect to frontend with authentication cookie set
    """
    try:
        # Get access token from Google
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            # If userinfo not in token, fetch it
            resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
            user_info = resp.json()
        
        # Validate email domain if configured
        email = user_info.get('email')
        if not validate_email_domain(email):
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?error=unauthorized_domain",
                status_code=302
            )
        
        # Create user session data
        session_data = create_user_session_data(user_info)
        
        # Create JWT token
        access_token = create_access_token(data=session_data)
        
        # Redirect to frontend with cookie
        response = RedirectResponse(url=f"{FRONTEND_URL}/?auth=success", status_code=302)
        set_auth_cookie(response, access_token)
        
        return response
        
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/?error=auth_failed",
            status_code=302
        )


@router.post("/logout")
async def logout(request: Request):
    """
    Logout user and clear session cookie
    
    Returns:
        Success response with cleared cookie
    """
    response = JSONResponse(content={"message": "Logged out successfully"})
    clear_auth_cookie(response)
    return response


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user information
    
    Returns:
        User information from session
        
    Raises:
        HTTPException: If user is not authenticated
    """
    try:
        user = get_current_user_from_cookie(request)
        return {
            "authenticated": True,
            "user": {
                "email": user.get("email"),
                "name": user.get("name"),
                "picture": user.get("picture"),
                "email_verified": user.get("email_verified", False)
            }
        }
    except HTTPException:
        return {
            "authenticated": False,
            "user": None
        }


@router.get("/status")
async def auth_status():
    """
    Check if authentication is enabled
    
    Returns:
        Authentication configuration status
    """
    return {
        "auth_enabled": AUTH_ENABLED,
        "google_oauth_configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
    }
