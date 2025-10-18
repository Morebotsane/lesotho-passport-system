"""
File upload and validation utilities
"""
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
import uuid
import os

from app.core.config import settings

async def save_upload_file(
    file: UploadFile,
    subdirectory: str = "documents"
) -> str:
    """
    Save uploaded file to disk and return relative path
    
    Args:
        file: FastAPI UploadFile object
        subdirectory: Subdirectory within uploads folder
        
    Returns:
        Relative file path (e.g., "documents/uuid_filename.jpg")
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    
    # Create subdirectory if it doesn't exist
    upload_dir = settings.get_upload_path() / subdirectory
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = upload_dir / unique_filename
    
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        await file.close()
    
    # Return relative path
    return f"{subdirectory}/{unique_filename}"


def delete_file(file_path: str) -> bool:
    """
    Delete file from disk
    
    Args:
        file_path: Relative path to file
        
    Returns:
        True if deleted, False if file didn't exist
    """
    full_path = settings.get_upload_path() / file_path
    if full_path.exists():
        full_path.unlink()
        return True
    return False


def get_file_url(file_path: Optional[str]) -> Optional[str]:
    """
    Convert file path to URL
    
    Args:
        file_path: Relative file path
        
    Returns:
        Full URL to access file
    """
    if not file_path:
        return None
    return f"{settings.API_V1_STR}/files/{file_path}"