"""
User management endpoints for the Authentication Management Component

This module provides endpoints for user CRUD operations.
"""

import uuid
from typing import Any, List

from fastapi import APIRouter, Body, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    DBSession,
    CurrentActiveUser,
    CurrentSuperUser,
)
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate, UserUpdate

# Create router for user endpoints
router = APIRouter()


@router.get("/", response_model=List[UserSchema])
async def read_users(
    db: DBSession,
    current_user: CurrentSuperUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> Any:
    """
    Retrieve users.
    
    Args:
        db: Database session
        current_user: Current authenticated superuser
        skip: Number of users to skip
        limit: Maximum number of users to return
        
    Returns:
        List[User]: List of users
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    db: DBSession,
    current_user: CurrentSuperUser,
    user_in: UserCreate = Body(...),
) -> Any:
    """
    Create new user (superuser only).
    
    Args:
        db: Database session
        current_user: Current authenticated superuser
        user_in: User creation data
        
    Returns:
        User: Created user data
    """
    # Check if user with this email already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    # Create new user
    user = User(
        id=uuid.uuid4(),
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        email_verified=user_in.email_verified,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: CurrentActiveUser,
) -> Any:
    """
    Get current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current user data
    """
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_user_me(
    db: DBSession,
    current_user: CurrentActiveUser,
    user_in: UserUpdate = Body(...),
) -> Any:
    """
    Update current user.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        user_in: User update data
        
    Returns:
        User: Updated user data
    """
    # Check if email is being changed and if it's already in use
    if user_in.email and user_in.email != current_user.email:
        result = await db.execute(select(User).where(User.email == user_in.email))
        existing_user = result.scalars().first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists",
            )
    
    # Update user fields
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Handle password update separately
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    
    # Update user attributes
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.get("/{user_id}", response_model=UserSchema)
async def read_user_by_id(
    user_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentSuperUser,
) -> Any:
    """
    Get a specific user by id (superuser only).
    
    Args:
        db: Database session
        current_user: Current authenticated superuser
        user_id: User ID
        
    Returns:
        User: User data
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentSuperUser,
    user_in: UserUpdate = Body(...),
) -> Any:
    """
    Update a user (superuser only).
    
    Args:
        db: Database session
        current_user: Current authenticated superuser
        user_id: User ID
        user_in: User update data
        
    Returns:
        User: Updated user data
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if email is being changed and if it's already in use
    if user_in.email and user_in.email != user.email:
        result = await db.execute(select(User).where(User.email == user_in.email))
        existing_user = result.scalars().first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists",
            )
    
    # Update user fields
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Handle password update separately
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    
    # Update user attributes
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentSuperUser,
) -> None:
    """
    Delete a user (superuser only).
    
    Args:
        db: Database session
        current_user: Current authenticated superuser
        user_id: User ID
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users cannot delete themselves",
        )
    
    await db.delete(user)
    await db.commit()
