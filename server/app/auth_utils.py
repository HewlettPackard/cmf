"""
Authentication utilities for JWT token management and user sessions
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status, Request, Response
from server.app.auth_config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_NAME,
    COOKIE_MAX_AGE,
    COOKIE_SECURE,
    COOKIE_HTTPONLY,
    COOKIE_SAMESITE,
    ALLOWED_EMAIL_DOMAINS
)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token with user information
    
    Args:
        data: Dictionary containing user information (email, name, picture, etc.)
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


def get_current_user_from_cookie(request: Request) -> Dict[str, Any]:
    """
    Extract and verify user from session cookie
    
    Args:
        request: FastAPI Request object
        
    Returns:
        User information dictionary
        
    Raises:
        HTTPException: If no valid session found
    """
    token = request.cookies.get(COOKIE_NAME)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return verify_token(token)


def set_auth_cookie(response: Response, token: str) -> None:
    """
    Set authentication cookie in response
    
    Args:
        response: FastAPI Response object
        token: JWT token to store in cookie
    """
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )


def clear_auth_cookie(response: Response) -> None:
    """
    Clear authentication cookie (for logout)
    
    Args:
        response: FastAPI Response object
    """
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )


def validate_email_domain(email: str) -> bool:
    """
    Validate if email domain is in allowed list (if configured)
    
    Args:
        email: User email address
        
    Returns:
        True if email is allowed, False otherwise
    """
    if not ALLOWED_EMAIL_DOMAINS or not ALLOWED_EMAIL_DOMAINS[0]:
        # If no domain restrictions, allow all
        return True
    
    domain = email.split("@")[-1]
    return domain in ALLOWED_EMAIL_DOMAINS


def create_user_session_data(google_user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format user session data from Google user info
    
    Args:
        google_user_info: User information from Google OAuth
        
    Returns:
        Formatted user session dictionary
    """
    return {
        "email": google_user_info.get("email"),
        "name": google_user_info.get("name"),
        "picture": google_user_info.get("picture"),
        "email_verified": google_user_info.get("email_verified", False),
        "sub": google_user_info.get("sub")  # Google user ID
    }
