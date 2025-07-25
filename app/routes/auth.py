from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.auth import (
    authenticate_user, create_user, create_access_token, create_session_token,
    verify_email_token, create_password_reset_token, reset_password_with_token,
    invalidate_user_sessions, get_current_user, get_current_user_optional
)
from app.models import User
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    plan: str
    is_email_verified: bool
    files_processed_this_month: int
    total_files_processed: int
    subscription_status: str
    created_at: datetime

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        user = create_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            db=db
        )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        return Token(
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "plan": user.plan,
                "is_email_verified": user.is_email_verified,
                "files_processed_this_month": user.files_processed_this_month,
                "total_files_processed": user.total_files_processed,
                "subscription_status": user.subscription_status,
                "created_at": user.created_at
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = authenticate_user(user_data.email, user_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "plan": user.plan,
            "is_email_verified": user.is_email_verified,
            "files_processed_this_month": user.files_processed_this_month,
            "total_files_processed": user.total_files_processed,
            "subscription_status": user.subscription_status,
            "created_at": user.created_at
        }
    )

@router.post("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email address"""
    if verify_email_token(token, db):
        return {"message": "Email verified successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset"""
    if create_password_reset_token(request.email, db):
        return {"message": "Password reset email sent"}
    else:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(request: PasswordReset, db: Session = Depends(get_db)):
    """Reset password with token"""
    if reset_password_with_token(request.token, request.new_password, db):
        return {"message": "Password reset successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        plan=current_user.plan,
        is_email_verified=current_user.is_email_verified,
        files_processed_this_month=current_user.files_processed_this_month,
        total_files_processed=current_user.total_files_processed,
        subscription_status=current_user.subscription_status,
        created_at=current_user.created_at
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout user and invalidate sessions"""
    invalidate_user_sessions(current_user.id, db)
    return {"message": "Logged out successfully"}

@router.post("/resend-verification")
async def resend_verification_email(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Resend email verification"""
    if current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Create new verification token
    from app.auth import send_verification_email
    import secrets
    
    verification_token = secrets.token_urlsafe(32)
    current_user.email_verification_token = verification_token
    db.commit()
    
    send_verification_email(current_user.email, verification_token)
    
    return {"message": "Verification email sent"}

@router.put("/profile")
async def update_profile(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if first_name is not None:
        current_user.first_name = first_name
    if last_name is not None:
        current_user.last_name = last_name
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Profile updated successfully"}

@router.delete("/account")
async def delete_account(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account"""
    from app.auth import verify_password
    
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Invalidate sessions
    invalidate_user_sessions(current_user.id, db)
    
    # Delete user
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account deleted successfully"} 