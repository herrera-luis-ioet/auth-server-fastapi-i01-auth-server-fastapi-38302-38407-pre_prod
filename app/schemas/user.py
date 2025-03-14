"""
User schemas for the Authentication Management Component

This module defines Pydantic schemas for user data validation and serialization.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# PUBLIC_INTERFACE
class UserBase(BaseModel):
    """
    Base schema for User data.
    
    Attributes:
        email: User's email address
        full_name: User's full name (optional)
        is_active: Whether the user account is active
        is_superuser: Whether the user has superuser privileges
        email_verified: Whether the user's email has been verified
    """
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    email_verified: Optional[bool] = False


# PUBLIC_INTERFACE
class UserCreate(UserBase):
    """
    Schema for creating a new user.
    
    Attributes:
        email: User's email address (required)
        password: User's password (required)
    """
    
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v


# PUBLIC_INTERFACE
class UserUpdate(UserBase):
    """
    Schema for updating an existing user.
    
    All fields are optional to allow partial updates.
    """
    
    password: Optional[str] = Field(None, min_length=8)
    
    @field_validator("password")
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password complexity if provided."""
        if v is None:
            return v
            
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v


# PUBLIC_INTERFACE
class UserInDB(UserBase):
    """
    Schema for user data stored in the database.
    
    Includes hashed_password and system fields.
    """
    
    id: uuid.UUID
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        
        from_attributes = True


# PUBLIC_INTERFACE
class User(UserBase):
    """
    Schema for user data returned to clients.
    
    Excludes sensitive information like password.
    """
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        
        from_attributes = True