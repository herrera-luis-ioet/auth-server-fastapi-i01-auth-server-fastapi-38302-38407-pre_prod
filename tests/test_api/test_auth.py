"""
Tests for authentication endpoints

This module contains tests for the authentication endpoints of the Authentication Management Component.
"""

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db: AsyncSession) -> None:
    """Test successful login with valid credentials."""
    # Create a test user
    test_user = User(
        email="login_test@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Login Test User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
    )
    
    db.add(test_user)
    await db.commit()
    
    # Login with the test user
    login_data = {
        "username": "login_test@example.com",
        "password": "TestPassword123",
    }
    
    response = await client.post(
        "/api/v1/auth/login",
        data=login_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, db: AsyncSession) -> None:
    """Test login with invalid credentials."""
    # Create a test user
    test_user = User(
        email="invalid_login@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Invalid Login Test User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
    )
    
    db.add(test_user)
    await db.commit()
    
    # Login with incorrect password
    login_data = {
        "username": "invalid_login@example.com",
        "password": "WrongPassword123",
    }
    
    response = await client.post(
        "/api/v1/auth/login",
        data=login_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db: AsyncSession) -> None:
    """Test login with an inactive user account."""
    # Create an inactive test user
    test_user = User(
        email="inactive_user@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Inactive Test User",
        is_active=False,
        is_superuser=False,
        email_verified=True,
    )
    
    db.add(test_user)
    await db.commit()
    
    # Login with inactive user
    login_data = {
        "username": "inactive_user@example.com",
        "password": "TestPassword123",
    }
    
    response = await client.post(
        "/api/v1/auth/login",
        data=login_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Inactive user"


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user_token: dict) -> None:
    """Test refreshing access token with a valid refresh token."""
    # Refresh token
    refresh_data = {
        "refresh_token": test_user_token["refresh_token"],
    }
    
    response = await client.post(
        "/api/v1/auth/refresh",
        json=refresh_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient) -> None:
    """Test refreshing access token with an invalid refresh token."""
    # Refresh with invalid token
    refresh_data = {
        "refresh_token": "invalid_token",
    }
    
    response = await client.post(
        "/api/v1/auth/refresh",
        json=refresh_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, db: AsyncSession) -> None:
    """Test registering a new user."""
    # Register a new user
    user_data = {
        "email": "new_user@example.com",
        "password": "NewPassword123",
        "full_name": "New Test User",
    }
    
    response = await client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    
    # Check that user was created in the database
    result = await db.execute(select(User).where(User.email == user_data["email"]))
    user = result.scalars().first()
    assert user is not None
    assert user.email == user_data["email"]
    assert user.full_name == user_data["full_name"]
    assert verify_password(user_data["password"], user.hashed_password)
    assert user.is_active
    assert not user.is_superuser
    assert not user.email_verified
    assert user.verification_token is not None


@pytest.mark.asyncio
async def test_register_existing_user(client: AsyncClient, db: AsyncSession) -> None:
    """Test registering a user with an email that already exists."""
    # Create a test user
    test_user = User(
        email="existing_user@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Existing Test User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
    )
    
    db.add(test_user)
    await db.commit()
    
    # Try to register with the same email
    user_data = {
        "email": "existing_user@example.com",
        "password": "NewPassword123",
        "full_name": "New Test User",
    }
    
    response = await client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "A user with this email already exists"


@pytest.mark.asyncio
async def test_password_reset_request(client: AsyncClient, db: AsyncSession) -> None:
    """Test requesting a password reset."""
    # Create a test user
    test_user = User(
        email="reset_test@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Reset Test User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
    )
    
    db.add(test_user)
    await db.commit()
    
    # Request password reset
    reset_data = {
        "email": "reset_test@example.com",
    }
    
    response = await client.post(
        "/api/v1/auth/password-reset-request",
        json=reset_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert "message" in data
    
    # Check that reset token was created
    result = await db.execute(select(User).where(User.email == reset_data["email"]))
    user = result.scalars().first()
    assert user.password_reset_token is not None
    assert user.password_reset_token_expires is not None


@pytest.mark.asyncio
async def test_password_reset(client: AsyncClient, db: AsyncSession) -> None:
    """Test resetting a password with a valid token."""
    # Create a test user with a reset token
    from datetime import datetime, timedelta
    import secrets
    
    reset_token = secrets.token_urlsafe(32)
    reset_token_expires = datetime.utcnow() + timedelta(hours=24)
    
    test_user = User(
        email="reset_password@example.com",
        hashed_password=get_password_hash("OldPassword123"),
        full_name="Reset Password Test User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
        password_reset_token=reset_token,
        password_reset_token_expires=reset_token_expires,
    )
    
    db.add(test_user)
    await db.commit()
    
    # Reset password
    reset_data = {
        "token": reset_token,
        "new_password": "NewPassword123",
    }
    
    response = await client.post(
        "/api/v1/auth/password-reset",
        json=reset_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    
    # Check that password was updated
    result = await db.execute(select(User).where(User.email == test_user.email))
    user = result.scalars().first()
    assert user.password_reset_token is None
    assert user.password_reset_token_expires is None
    assert verify_password("NewPassword123", user.hashed_password)


@pytest.mark.asyncio
async def test_verify_email(client: AsyncClient, db: AsyncSession) -> None:
    """Test verifying email with a valid token."""
    # Create a test user with a verification token
    from datetime import datetime, timedelta
    import secrets
    
    verification_token = secrets.token_urlsafe(32)
    verification_token_expires = datetime.utcnow() + timedelta(days=3)
    
    test_user = User(
        email="verify_email@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Verify Email Test User",
        is_active=True,
        is_superuser=False,
        email_verified=False,
        verification_token=verification_token,
        verification_token_expires=verification_token_expires,
    )
    
    db.add(test_user)
    await db.commit()
    
    # Verify email
    verification_data = {
        "token": verification_token,
    }
    
    response = await client.post(
        "/api/v1/auth/verify-email",
        json=verification_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    
    # Check that email was verified
    result = await db.execute(select(User).where(User.email == test_user.email))
    user = result.scalars().first()
    assert user.email_verified
    assert user.verification_token is None
    assert user.verification_token_expires is None


@pytest.mark.asyncio
async def test_logout(authenticated_client: AsyncClient) -> None:
    """Test logging out a user."""
    # Logout
    response = await authenticated_client.post("/api/v1/auth/logout")
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert data["message"] == "Successfully logged out"