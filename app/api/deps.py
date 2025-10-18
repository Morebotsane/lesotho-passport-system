# app/api/deps.py
"""
Authentication and authorization dependencies for FastAPI endpoints
These functions handle JWT token validation and user authorization
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.core.security import verify_token
from app.models.user import User, UserRole

# HTTP Bearer token security scheme
security = HTTPBearer()

def get_current_user(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get the current authenticated user from JWT token
    
    Args:
        db: Database session
        token: HTTP Bearer token from Authorization header
        
    Returns:
        User object of the authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Create credentials exception
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        jwt_token = token.credentials
        
        # Verify and decode the token
        user_id = verify_token(jwt_token)
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (convenience function)
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="User account is inactive"
        )
    return current_user

def get_current_officer(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user if they are a passport officer or admin
    
    Args:
        current_user: Current active user
        
    Returns:
        User object if they have officer/admin role
        
    Raises:
        HTTPException: If user is not an officer or admin
    """
    if current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires officer or admin privileges"
        )
    return current_user

def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user if they are an admin
    
    Args:
        current_user: Current active user
        
    Returns:
        User object if they have admin role
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires admin privileges"
        )
    return current_user

def get_current_applicant_or_officer(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user if they are an applicant, officer, or admin
    (Used for endpoints that both applicants and officers can access)
    
    Args:
        current_user: Current active user
        
    Returns:
        User object
        
    Raises:
        HTTPException: If somehow user has no valid role (shouldn't happen)
    """
    # This should always pass since we validate roles at user creation
    # But keeping it for completeness
    if current_user.role not in [UserRole.APPLICANT, UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role"
        )
    return current_user

def check_user_permission(
    current_user: User,
    target_user_id: str = None,
    allow_officer_access: bool = True
) -> bool:
    """
    Check if current user can access resource owned by target_user_id
    
    Args:
        current_user: Current authenticated user
        target_user_id: ID of the user who owns the resource
        allow_officer_access: Whether officers can access any user's data
        
    Returns:
        True if access allowed, False otherwise
    """
    # Admins can access everything
    if current_user.role == UserRole.ADMIN:
        return True
        
    # Officers can access everything if allowed
    if current_user.role == UserRole.OFFICER and allow_officer_access:
        return True
        
    # Users can access their own data
    if target_user_id and str(current_user.id) == str(target_user_id):
        return True
        
    return False

def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user