"""
User management API endpoints (Admin only)
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User, UserRole
from app.schemas.user import UserResponse

from sqlalchemy.orm import joinedload

router = APIRouter()

def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.get("/officers", response_model=List[UserResponse])
def get_all_officers(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Any:
    """Get all officers (Admin only)"""
    officers = db.query(User).options(
        joinedload(User.assigned_location)  # Important!
    ).filter(User.role == UserRole.OFFICER).all()
    return officers

@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_id: str
) -> Any:
    """Get user by ID (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_id: str,
    user_update: dict
) -> Any:
    """Update user information (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update allowed fields
    if "first_name" in user_update:
        user.first_name = user_update["first_name"]
    
    if "last_name" in user_update:
        user.last_name = user_update["last_name"]
    
    if "phone" in user_update:
        # Check if phone already exists for another user
        if user_update["phone"]:
            existing_phone = db.query(User).filter(
                User.phone == user_update["phone"],
                User.id != user_id
            ).first()
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number already exists"
                )
        user.phone = user_update["phone"]
    
    # ADD THIS BLOCK - Update assigned location
    if "assigned_location_id" in user_update:
        location_id = user_update["assigned_location_id"]
        if location_id:
            # Verify location exists
            from app.models.appointment import PickupLocation
            location = db.query(PickupLocation).filter(
                PickupLocation.id == location_id
            ).first()
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Location not found"
                )
            user.assigned_location_id = location_id
        else:
            user.assigned_location_id = None
    
    db.commit()
    db.refresh(user)
    
    # Load the relationship before returning
    from sqlalchemy.orm import joinedload
    user = db.query(User).options(
        joinedload(User.assigned_location)
    ).filter(User.id == user_id).first()
    
    return user

@router.put("/{user_id}/activate")
def activate_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_id: str
) -> Any:
    """Activate user account (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    db.commit()
    
    return {"message": "User activated successfully", "user_id": user_id}

@router.put("/{user_id}/deactivate")
def deactivate_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_id: str
) -> Any:
    """Deactivate user account (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully", "user_id": user_id}

@router.put("/{user_id}/reset-password")
def reset_user_password(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_id: str,
    new_password: str
) -> Any:
    """Reset user password (Admin only)"""
    from app.core.security import get_password_hash
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password reset successfully", "user_id": user_id}