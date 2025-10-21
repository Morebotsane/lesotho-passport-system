# app/core/security.py
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import secrets
import string

from app.core.config import settings
from app.models.user import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    Create a JWT access token
    
    Args:
        subject: Usually the user ID or email
        expires_delta: Token expiration time (optional)
    
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # JWT payload
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow(),
        "type": "access_token"
    }
    
    # Create the JWT token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        User identifier from token payload, or None if invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract subject (user identifier)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        # Verify token type
        token_type: str = payload.get("type")
        if token_type != "access_token":
            return None
            
        return user_id
        
    except JWTError:
        return None

def get_password_hash(password: str) -> str:
    """
    Hash the user's password safely.

    Bcrypt supports a maximum of 72 bytes; truncate longer passwords
    to avoid internal Passlib errors.
    """
    if isinstance(password, str):
        password_bytes = password.encode("utf-8")
    else:
        password_bytes = password

    # Truncate safely to 72 bytes before hashing
    password_bytes = password_bytes[:72]
    safe_password = password_bytes.decode("utf-8", errors="ignore")

    return pwd_context.hash(safe_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def generate_password_reset_token(email: str) -> str:
    """
    Generate a password reset token
    
    Args:
        email: User's email address
        
    Returns:
        Password reset token
    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    
    to_encode = {
        "exp": expires,
        "sub": email,
        "iat": now,
        "type": "password_reset"
    }
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token
    
    Args:
        token: Password reset token
        
    Returns:
        Email from token if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if not email or token_type != "password_reset":
            return None
            
        return email
        
    except JWTError:
        return None

def generate_application_number() -> str:
    """
    Generate a unique passport application number
    Format: PP-YYYY-XXXXXXXX (PP-2024-A1B2C3D4)
    
    Returns:
        Unique application number string
    """
    current_year = datetime.now().year
    
    # Generate random 8-character alphanumeric string
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(8))
    
    return f"PP-{current_year}-{random_part}"

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password
    
    Args:
        db: Database session
        email: User's email
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
        
    if not verify_password(password, user.hashed_password):
        return None
        
    if not user.is_active:
        return None
        
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user