"""
OAuth2 Authentication Configuration for CMF Server
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# Google OAuth2 Settings (REQUIRED)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/api/auth/google/callback")

# JWT Settings for Session Management (REQUIRED)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))  # 30 days

# Session Cookie Settings
COOKIE_NAME = "cmf_session"
COOKIE_MAX_AGE = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"  # True for HTTPS only
COOKIE_HTTPONLY = True  # Prevents JavaScript access
COOKIE_SAMESITE = "lax"  # CSRF protection

# Frontend URL (REQUIRED)
FRONTEND_URL = os.getenv("REACT_APP_CMF_API_URL", "http://localhost:3000")

# Optional: Enable/Disable Authentication
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

# Optional: Whitelist of allowed email domains (e.g., only allow company emails)
ALLOWED_EMAIL_DOMAINS = os.getenv("ALLOWED_EMAIL_DOMAINS", "").split(",") if os.getenv("ALLOWED_EMAIL_DOMAINS") else []

# OAuth2 Configuration
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_ACCESS_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# Scopes
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]
