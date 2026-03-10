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

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_google_token(token: str) -> Optional[dict]:
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=31536000
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return None
        
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
    
    if user_id:
        user = crud.get_user_by_id(db, user_id)
    else:
        user = crud.get_user_by_email(db, email)
    
    if user is None:
        raise credentials_exception
    
    return user


def authenticate_google_user(db: Session, google_token: str) -> tuple:
    google_info = verify_google_token(google_token)
    
    if not google_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    
    user = crud.get_or_create_user(
        db,
        email=google_info['email'],
        name=google_info['name'],
        oauth_provider='google'
    )
    
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    return user, access_token


def create_dev_token(email: str = "dev@example.com", name: str = "Developer") -> tuple:
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
