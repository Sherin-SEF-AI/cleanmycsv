import jwt as PyJWT
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models import User, UserSession
from app.config import settings
from app.database import get_db
import uuid

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = PyJWT.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = PyJWT.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except PyJWT.ExpiredSignatureError:
        return None
    except PyJWT.JWTError:
        return None

def create_session_token(user_id: str, db: Session) -> str:
    """Create a session token for the user"""
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=30)
    
    session = UserSession(
        user_id=user_id,
        session_token=session_token,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    
    return session_token

def verify_session_token(session_token: str, db: Session) -> Optional[User]:
    """Verify a session token and return the user"""
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        return None
    
    # Update last used
    session.last_used = datetime.utcnow()
    db.commit()
    
    return db.query(User).filter(User.id == session.user_id).first()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    
    # Try JWT token first
    payload = verify_token(token)
    if payload and "sub" in payload:
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if user and user.is_active:
            return user
    
    # Try session token
    user = verify_session_token(token, db)
    if user and user.is_active:
        return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    try:
        # Extract token from Authorization header
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None
        
        # Verify token and get user
        payload = verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None

def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    """Authenticate a user with email and password"""
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        return None
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is locked until {user.locked_until.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    if not verify_password(password, user.hashed_password):
        # Increment login attempts
        user.login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account locked due to too many failed login attempts. Try again in 30 minutes."
            )
        
        db.commit()
        return None
    
    # Reset login attempts on successful login
    user.login_attempts = 0
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

def create_user(email: str, password: str, first_name: str = None, last_name: str = None, db: Session = None) -> User:
    """Create a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create verification token
    verification_token = secrets.token_urlsafe(32)
    
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        email_verification_token=verification_token
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send verification email
    send_verification_email(user.email, verification_token)
    
    return user

def send_verification_email(email: str, token: str):
    """Send email verification email"""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return  # Skip if email not configured
    
    try:
        verification_url = f"https://cleancsv.online/verify-email?token={token}"
        
        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = "Verify your CleanMyCSV.online account"
        
        body = f"""
        Welcome to CleanMyCSV.online!
        
        Please click the link below to verify your email address:
        {verification_url}
        
        If you didn't create an account, you can safely ignore this email.
        
        Best regards,
        The CleanMyCSV.online Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send verification email: {e}")

def send_password_reset_email(email: str, token: str):
    """Send password reset email"""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return  # Skip if email not configured
    
    try:
        reset_url = f"https://cleancsv.online/reset-password?token={token}"
        
        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = "Reset your CleanMyCSV.online password"
        
        body = f"""
        You requested a password reset for your CleanMyCSV.online account.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this reset, you can safely ignore this email.
        
        Best regards,
        The CleanMyCSV.online Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send password reset email: {e}")

def verify_email_token(token: str, db: Session) -> bool:
    """Verify email verification token"""
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        return False
    
    user.is_email_verified = True
    user.email_verification_token = None
    db.commit()
    return True

def create_password_reset_token(email: str, db: Session) -> bool:
    """Create password reset token"""
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        return False
    
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)
    
    user.password_reset_token = token
    user.password_reset_expires = expires
    db.commit()
    
    send_password_reset_email(email, token)
    return True

def reset_password_with_token(token: str, new_password: str, db: Session) -> bool:
    """Reset password using token"""
    user = db.query(User).filter(
        User.password_reset_token == token,
        User.password_reset_expires > datetime.utcnow()
    ).first()
    
    if not user:
        return False
    
    user.hashed_password = get_password_hash(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.login_attempts = 0  # Reset login attempts
    db.commit()
    
    return True

def invalidate_user_sessions(user_id: str, db: Session):
    """Invalidate all sessions for a user"""
    db.query(UserSession).filter(UserSession.user_id == user_id).update({"is_active": False}) 