"""
Authentication module for ERP Purchase Order System.
Handles JWT token creation/validation and Google OAuth.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import User
from backend import crud

# HTTP Bearer token security scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_google_token(token: str) -> Optional[dict]:
    """
    Verify a Google OAuth ID token.
    
    Args:
        token: Google ID token
        
    Returns:
        User info dict if valid, None otherwise
    """
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        # Verify issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return None
        
        # Get name with fallback to email prefix
        name = idinfo.get('name', '') or idinfo.get('given_name', '')
        if not name:
            name = idinfo['email'].split('@')[0].replace('.', ' ').title()
        
        return {
            'email': idinfo['email'],
            'name': name,
            'picture': idinfo.get('picture', '')
        }
    except ValueError as e:
        print(f"Google token verification error: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise credentials_exception
    
    email = payload.get("sub")
    user_id = payload.get("user_id")
    
    if email is None:
        raise credentials_exception
    
    # Get user from database
    if user_id:
        user = crud.get_user_by_id(db, user_id)
    else:
        user = crud.get_user_by_email(db, email)
    
    if user is None:
        raise credentials_exception
    
    return user


def authenticate_google_user(db: Session, google_token: str) -> tuple:
    """
    Authenticate a user via Google OAuth.
    Creates user if first login.
    
    Args:
        db: Database session
        google_token: Google ID token
        
    Returns:
        Tuple of (user, access_token)
        
    Raises:
        HTTPException: If Google token is invalid
    """
    # Verify Google token
    google_info = verify_google_token(google_token)
    
    if not google_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    
    # Get or create user
    user = crud.get_or_create_user(
        db,
        email=google_info['email'],
        name=google_info['name'],
        oauth_provider='google'
    )
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    return user, access_token


# For development/testing: Create a mock user authentication
def create_dev_token(email: str = "dev@example.com", name: str = "Developer") -> tuple:
    """
    Create a development token for testing without Google OAuth.
    Only use in development mode.
    
    Args:
        email: User email
        name: User name
        
    Returns:
        Tuple of (mock_user_data, access_token)
    """
    access_token = create_access_token(
        data={"sub": email, "user_id": 1}
    )
    
    user_data = {
        "id": 1,
        "email": email,
        "name": name,
        "oauth_provider": "development"
    }
    
    return user_data, access_token
