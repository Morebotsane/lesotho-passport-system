# app/api/auth.py
"""
Authentication API endpoints
Handles user registration, login, and profile management
"""
from datetime import timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password
)
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate,
    UserResponse,
    LoginResponse,
    UserLogin,
    UserUpdate,
    PasswordChange
)

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register a new user
    
    Creates a new user account with the provided information.
    Default role is APPLICANT unless specified otherwise.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Check if phone number already exists
    existing_phone = db.query(User).filter(User.phone == user_in.phone).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this phone number already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_in.password)
    
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone=user_in.phone,
        role=user_in.role,
        is_active=True,
        is_verified=False  # Email verification can be added later
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=LoginResponse)
def login(
    *,
    db: Session = Depends(get_db),
    user_credentials: UserLogin
) -> Any:
    """
    User login endpoint
    
    Authenticates user with email and password
    Returns JWT access token and user information
    """
    email = user_credentials.email
    password = user_credentials.password
    
    # Authenticate user
    user = authenticate_user(db, email=email, password=password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        user=UserResponse.from_orm(user)
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user's profile information
    
    Requires valid JWT token in Authorization header
    """
    return current_user

@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_update: UserUpdate
) -> Any:
    """
    Update current user's profile information
    
    Users can update their own profile information
    """
    # Check if email is being updated and if it already exists
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
        
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
        
    if user_update.phone is not None:
        # Check if phone number already exists for another user
        existing_phone = db.query(User).filter(
            User.phone == user_update.phone,
            User.id != current_user.id
        ).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists"
            )
        current_user.phone = user_update.phone
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.post("/change-password")
def change_password(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    password_data: PasswordChange
) -> Any:
    """
    Change user's password
    
    Requires current password for verification
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Check if new password is different from current
    if verify_password(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Logout endpoint
    
    Note: JWT tokens are stateless, so logout is mainly for client-side token cleanup
    In production, you might want to maintain a token blacklist
    """
    return {"message": "Successfully logged out"}

# Development/Testing endpoints (remove in production)
@router.get("/test-protected")
def test_protected_route(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Test endpoint to verify authentication is working
    Remove this in production
    """
    return {
        "message": "Authentication is working!",
        "user_id": str(current_user.id),
        "user_role": current_user.role.value,
        "user_name": current_user.full_name
    }