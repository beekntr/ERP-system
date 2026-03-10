from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user, authenticate_google_user, create_dev_token
from backend.models import User
from backend import crud
from backend.schemas import (
    GoogleAuthRequest, LoginResponse, UserResponse, Token,
    UserCreate
)
from backend.config import settings
from backend.security import limiter, sanitize

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/google", response_model=LoginResponse)
@limiter.limit("10/minute")
async def google_login(
    request: Request,
    auth_request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    try:
        user, access_token = authenticate_google_user(db, auth_request.token)
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/dev-login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def dev_login(
    request: Request,
    db: Session = Depends(get_db)
):
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login is only available in debug mode"
        )
    
    try:
        user = crud.get_or_create_user(
            db,
            email="developer@erp-demo.com",
            name="Developer",
            oauth_provider="development"
        )
        
        from backend.auth import create_access_token
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
@limiter.limit("100/minute")
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.post("/logout")
@limiter.limit("30/minute")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return {"message": "Logged out successfully. Please remove the token from client storage."}


@router.get("/config")
@limiter.limit("60/minute")
async def get_auth_config(request: Request):
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "app_name": settings.APP_NAME
    }
