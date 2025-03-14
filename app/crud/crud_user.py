"""
User CRUD operations for the Authentication Management Component

This module provides user-specific CRUD operations for user creation,
authentication, password management, and user management.
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


# PUBLIC_INTERFACE
class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    CRUD operations for User model.
    
    Extends the base CRUD class with user-specific operations for authentication,
    password management, and user verification.
    """
    
    # PUBLIC_INTERFACE
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: Email address to search for
            
        Returns:
            User if found, None otherwise
        """
        return await self.get_by_attribute(db, "email", email)
    
    # PUBLIC_INTERFACE
    async def create_with_password(
        self, db: AsyncSession, *, obj_in: UserCreate
    ) -> User:
        """
        Create a new user with password hashing.
        
        Args:
            db: Database session
            obj_in: User creation data with plain password
            
        Returns:
            Created user
        """
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
            email_verified=obj_in.email_verified,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    # PUBLIC_INTERFACE
    async def update_user(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update a user, handling password hashing if password is provided.
        
        Args:
            db: Database session
            db_obj: User object to update
            obj_in: User update data
            
        Returns:
            Updated user
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
            
        return await super().update(db, db_obj=db_obj, obj_in=update_data)
    
    # PUBLIC_INTERFACE
    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Args:
            db: Database session
            email: User's email
            password: User's plain password
            
        Returns:
            Authenticated user if credentials are valid, None otherwise
        """
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    # PUBLIC_INTERFACE
    async def is_active(self, user: User) -> bool:
        """
        Check if a user is active.
        
        Args:
            user: User to check
            
        Returns:
            True if user is active, False otherwise
        """
        return user.is_active
    
    # PUBLIC_INTERFACE
    async def is_superuser(self, user: User) -> bool:
        """
        Check if a user is a superuser.
        
        Args:
            user: User to check
            
        Returns:
            True if user is a superuser, False otherwise
        """
        return user.is_superuser
    
    # PUBLIC_INTERFACE
    async def update_last_login(
        self, db: AsyncSession, *, user: User
    ) -> User:
        """
        Update a user's last login timestamp.
        
        Args:
            db: Database session
            user: User to update
            
        Returns:
            Updated user
        """
        user.last_login = datetime.utcnow()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    # PUBLIC_INTERFACE
    async def create_verification_token(
        self, db: AsyncSession, *, user: User, expires_days: int = 3
    ) -> str:
        """
        Create and store an email verification token for a user.
        
        Args:
            db: Database session
            user: User to create token for
            expires_days: Number of days until token expires
            
        Returns:
            Generated verification token
        """
        token = secrets.token_urlsafe(32)
        user.verification_token = token
        user.verification_token_expires = datetime.utcnow() + timedelta(days=expires_days)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return token
    
    # PUBLIC_INTERFACE
    async def verify_email(
        self, db: AsyncSession, *, token: str
    ) -> Optional[User]:
        """
        Verify a user's email using a verification token.
        
        Args:
            db: Database session
            token: Verification token
            
        Returns:
            User if verification successful, None otherwise
        """
        result = await db.execute(
            select(User).where(User.verification_token == token)
        )
        user = result.scalars().first()
        
        if not user or not user.is_active:
            return None
            
        # Check if token is expired
        if (
            not user.verification_token_expires
            or user.verification_token_expires < datetime.utcnow()
        ):
            return None
            
        # Mark email as verified and clear verification token
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    # PUBLIC_INTERFACE
    async def create_password_reset_token(
        self, db: AsyncSession, *, user: User, expires_hours: int = 24
    ) -> str:
        """
        Create and store a password reset token for a user.
        
        Args:
            db: Database session
            user: User to create token for
            expires_hours: Number of hours until token expires
            
        Returns:
            Generated password reset token
        """
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_token_expires = datetime.utcnow() + timedelta(hours=expires_hours)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return token
    
    # PUBLIC_INTERFACE
    async def reset_password(
        self, db: AsyncSession, *, token: str, new_password: str
    ) -> Optional[User]:
        """
        Reset a user's password using a reset token.
        
        Args:
            db: Database session
            token: Password reset token
            new_password: New password to set
            
        Returns:
            User if password reset successful, None otherwise
        """
        result = await db.execute(
            select(User).where(User.password_reset_token == token)
        )
        user = result.scalars().first()
        
        if not user or not user.is_active:
            return None
            
        # Check if token is expired
        if (
            not user.password_reset_token_expires
            or user.password_reset_token_expires < datetime.utcnow()
        ):
            return None
            
        # Update password and clear reset token
        user.hashed_password = get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_token_expires = None
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    # PUBLIC_INTERFACE
    async def change_password(
        self, db: AsyncSession, *, user: User, current_password: str, new_password: str
    ) -> bool:
        """
        Change a user's password, verifying the current password.
        
        Args:
            db: Database session
            user: User to update
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password change successful, False otherwise
        """
        if not verify_password(current_password, user.hashed_password):
            return False
            
        user.hashed_password = get_password_hash(new_password)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return True
    
    # PUBLIC_INTERFACE
    async def deactivate_user(
        self, db: AsyncSession, *, user_id: UUID
    ) -> Optional[User]:
        """
        Deactivate a user by ID.
        
        Args:
            db: Database session
            user_id: ID of user to deactivate
            
        Returns:
            Deactivated user if found, None otherwise
        """
        user = await self.get(db=db, id=user_id)
        if not user:
            return None
            
        user.is_active = False
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    # PUBLIC_INTERFACE
    async def reactivate_user(
        self, db: AsyncSession, *, user_id: UUID
    ) -> Optional[User]:
        """
        Reactivate a deactivated user by ID.
        
        Args:
            db: Database session
            user_id: ID of user to reactivate
            
        Returns:
            Reactivated user if found, None otherwise
        """
        user = await self.get(db=db, id=user_id)
        if not user:
            return None
            
        user.is_active = True
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user


# Create a singleton instance for global use
user = CRUDUser(User)