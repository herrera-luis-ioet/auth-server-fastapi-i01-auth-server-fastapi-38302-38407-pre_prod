"""
API dependencies for the Authentication Management Component

This module provides dependency functions for FastAPI to inject database sessions
and authenticate users based on JWT tokens.
"""

from datetime import datetime
from typing import Annotated, AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Type aliases for commonly used dependencies
DBSession = Annotated[AsyncSession, Depends(get_db)]


# PUBLIC_INTERFACE
async def get_current_user(
    db: DBSession,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """
    Dependency to get the current authenticated user from a JWT token.
    
    Args:
        db: Database session dependency
        token: JWT token from the Authorization header
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = decode_token(token)
        user_id: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        
        if user_id is None:
            raise credentials_exception
        
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError:
        raise credentials_exception
    
    # Get the user from the database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.add(user)
    await db.commit()
    
    return user


# PUBLIC_INTERFACE
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to get the current authenticated user and verify they are active.
    
    Args:
        current_user: The authenticated user from get_current_user
        
    Returns:
        User: The authenticated active user
        
    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


# PUBLIC_INTERFACE
async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Dependency to get the current authenticated user and verify they are a superuser.
    
    Args:
        current_user: The authenticated active user from get_current_active_user
        
    Returns:
        User: The authenticated active superuser
        
    Raises:
        HTTPException: If the user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


# Type aliases for commonly used user dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentSuperUser = Annotated[User, Depends(get_current_active_superuser)]