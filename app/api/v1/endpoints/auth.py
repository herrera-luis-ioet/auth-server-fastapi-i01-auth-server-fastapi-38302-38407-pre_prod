"""
Authentication endpoints for the Authentication Management Component

This module provides endpoints for user authentication, registration,
token refresh, password reset, and email verification.
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBSession, CurrentActiveUser
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.token import (
    EmailVerification,
    PasswordReset,
    PasswordResetRequest,
    Token,
    TokenRefresh,
)
from app.schemas.user import UserCreate, User as UserSchema

# Create router for authentication endpoints
router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    db: DBSession,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Args:
        db: Database session
        form_data: OAuth2 form with username (email) and password
        
    Returns:
        Token: Access and refresh tokens
    """
    # Find the user by email
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    
    # Validate user and password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.add(user)
    await db.commit()
    
    # Generate tokens
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    db: DBSession,
    token_data: TokenRefresh = Body(...),
) -> Any:
    """
    Refresh access token using a valid refresh token.
    
    Args:
        db: Database session
        token_data: Refresh token data
        
    Returns:
        Token: New access and refresh tokens
    """
    try:
        # Decode and validate the refresh token
        payload = decode_token(token_data.refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if not user_id or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get the user from the database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user or inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate new tokens
        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user(
    db: DBSession,
    user_in: UserCreate = Body(...),
) -> Any:
    """
    Register a new user.
    
    Args:
        db: Database session
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
    
    # Create verification token
    verification_token = secrets.token_urlsafe(32)
    verification_token_expires = datetime.utcnow() + timedelta(days=3)
    
    # Create new user
    user = User(
        id=uuid.uuid4(),
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False,
        email_verified=False,
        verification_token=verification_token,
        verification_token_expires=verification_token_expires,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # TODO: Send verification email
    
    return user


@router.post("/password-reset-request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    db: DBSession,
    reset_request: PasswordResetRequest = Body(...),
) -> Any:
    """
    Request a password reset token.
    
    Args:
        db: Database session
        reset_request: Password reset request with email
        
    Returns:
        dict: Success message
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == reset_request.email))
    user = result.scalars().first()
    
    # Always return success to prevent email enumeration
    if not user or not user.is_active:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate password reset token
    reset_token = secrets.token_urlsafe(32)
    reset_token_expires = datetime.utcnow() + timedelta(hours=24)
    
    # Update user with reset token
    user.password_reset_token = reset_token
    user.password_reset_token_expires = reset_token_expires
    
    db.add(user)
    await db.commit()
    
    # TODO: Send password reset email
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset", status_code=status.HTTP_200_OK)
async def reset_password(
    db: DBSession,
    reset_data: PasswordReset = Body(...),
) -> Any:
    """
    Reset password using a valid reset token.
    
    Args:
        db: Database session
        reset_data: Password reset data with token and new password
        
    Returns:
        dict: Success message
    """
    # Find user by reset token
    result = await db.execute(
        select(User).where(User.password_reset_token == reset_data.token)
    )
    user = result.scalars().first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )
    
    # Check if token is expired
    if (
        not user.password_reset_token_expires
        or user.password_reset_token_expires < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired",
        )
    
    # Update password and clear reset token
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_token_expires = None
    
    db.add(user)
    await db.commit()
    
    return {"message": "Password has been reset successfully"}


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    db: DBSession,
    verification_data: EmailVerification = Body(...),
) -> Any:
    """
    Verify email using a verification token.
    
    Args:
        db: Database session
        verification_data: Email verification data with token
        
    Returns:
        dict: Success message
    """
    # Find user by verification token
    result = await db.execute(
        select(User).where(User.verification_token == verification_data.token)
    )
    user = result.scalars().first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )
    
    # Check if token is expired
    if (
        not user.verification_token_expires
        or user.verification_token_expires < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired",
        )
    
    # Mark email as verified and clear verification token
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    
    db.add(user)
    await db.commit()
    
    return {"message": "Email has been verified successfully"}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: CurrentActiveUser,
) -> Any:
    """
    Logout the current user.
    
    Note: This is a client-side operation as JWT tokens are stateless.
    The client should discard the tokens.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Success message
    """
    # JWT is stateless, so we just return success
    # In a real-world scenario, you might want to implement a token blacklist
    return {"message": "Successfully logged out"}