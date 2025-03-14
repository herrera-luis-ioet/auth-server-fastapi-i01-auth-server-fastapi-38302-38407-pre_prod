"""
Tests for user management endpoints

This module contains tests for the user management endpoints of the Authentication Management Component.
"""

import uuid

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User


@pytest.mark.asyncio
async def test_read_users(superuser_client: AsyncClient, db: AsyncSession) -> None:
    """Test retrieving all users as a superuser."""
    # Create some test users
    test_users = [
        User(
            email=f"list_user{i}@example.com",
            hashed_password=get_password_hash("TestPassword123"),
            full_name=f"List Test User {i}",
            is_active=True,
            is_superuser=False,
            email_verified=True,
        )
        for i in range(3)
    ]
    
    for user in test_users:
        db.add(user)
    
    await db.commit()
    
    # Get users list
    response = await superuser_client.get("/api/v1/users/")
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3  # At least the 3 users we created


@pytest.mark.asyncio
async def test_read_users_normal_user(authenticated_client: AsyncClient) -> None:
    """Test that a normal user cannot retrieve all users."""
    # Try to get users list as normal user
    response = await authenticated_client.get("/api/v1/users/")
    
    # Check response
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "The user doesn't have enough privileges"


@pytest.mark.asyncio
async def test_create_user(superuser_client: AsyncClient, db: AsyncSession) -> None:
    """Test creating a new user as a superuser."""
    # Create a new user
    user_data = {
        "email": "new_admin_user@example.com",
        "password": "AdminPassword123",
        "full_name": "New Admin User",
        "is_active": True,
        "is_superuser": True,
        "email_verified": True,
    }
    
    response = await superuser_client.post(
        "/api/v1/users/",
        json=user_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert data["is_active"] == user_data["is_active"]
    assert data["is_superuser"] == user_data["is_superuser"]
    assert data["email_verified"] == user_data["email_verified"]
    assert "id" in data
    
    # Check that user was created in the database
    result = await db.execute(select(User).where(User.email == user_data["email"]))
    user = result.scalars().first()
    assert user is not None
    assert user.email == user_data["email"]
    assert user.full_name == user_data["full_name"]
    assert verify_password(user_data["password"], user.hashed_password)
    assert user.is_active == user_data["is_active"]
    assert user.is_superuser == user_data["is_superuser"]
    assert user.email_verified == user_data["email_verified"]


@pytest.mark.asyncio
async def test_create_user_existing_email(superuser_client: AsyncClient, db: AsyncSession) -> None:
    """Test creating a user with an email that already exists."""
    # Create a test user
    test_user = User(
        email="existing_admin_user@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Existing Admin User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
    )
    
    db.add(test_user)
    await db.commit()
    
    # Try to create a user with the same email
    user_data = {
        "email": "existing_admin_user@example.com",
        "password": "AdminPassword123",
        "full_name": "New Admin User",
        "is_active": True,
        "is_superuser": True,
        "email_verified": True,
    }
    
    response = await superuser_client.post(
        "/api/v1/users/",
        json=user_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "A user with this email already exists"


@pytest.mark.asyncio
async def test_read_user_me(authenticated_client: AsyncClient) -> None:
    """Test retrieving the current user's information."""
    # Get current user info
    response = await authenticated_client.get("/api/v1/users/me")
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "full_name" in data
    assert "is_active" in data
    assert "is_superuser" in data
    assert "email_verified" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_update_user_me(authenticated_client: AsyncClient, db: AsyncSession) -> None:
    """Test updating the current user's information."""
    # Update current user
    user_data = {
        "full_name": "Updated Test User",
        "password": "NewPassword123",
    }
    
    response = await authenticated_client.put(
        "/api/v1/users/me",
        json=user_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == user_data["full_name"]
    
    # Check that user was updated in the database
    result = await db.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalars().first()
    assert user is not None
    assert user.full_name == user_data["full_name"]
    assert verify_password(user_data["password"], user.hashed_password)


@pytest.mark.asyncio
async def test_read_user_by_id(superuser_client: AsyncClient, db: AsyncSession) -> None:
    """Test retrieving a user by ID as a superuser."""
    # Create a test user
    test_user = User(
        email="get_by_id@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Get By ID User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
    )
    
    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)
    
    # Get user by ID
    response = await superuser_client.get(f"/api/v1/users/{test_user.id}")
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_read_user_by_id_not_found(superuser_client: AsyncClient) -> None:
    """Test retrieving a non-existent user by ID."""
    # Generate a random UUID
    random_id = uuid.uuid4()
    
    # Try to get non-existent user
    response = await superuser_client.get(f"/api/v1/users/{random_id}")
    
    # Check response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "User not found"


@pytest.mark.asyncio
async def test_update_user(superuser_client: AsyncClient, db: AsyncSession) -> None:
    """Test updating a user as a superuser."""
    # Create a test user
    test_user = User(
        email="update_user@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Update User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
    )
    
    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)
    
    # Update user
    user_data = {
        "full_name": "Updated User Name",
        "is_active": False,
        "is_superuser": True,
    }
    
    response = await superuser_client.put(
        f"/api/v1/users/{test_user.id}",
        json=user_data,
    )
    
    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == user_data["full_name"]
    assert data["is_active"] == user_data["is_active"]
    assert data["is_superuser"] == user_data["is_superuser"]
    
    # Check that user was updated in the database
    result = await db.execute(select(User).where(User.id == test_user.id))
    user = result.scalars().first()
    assert user is not None
    assert user.full_name == user_data["full_name"]
    assert user.is_active == user_data["is_active"]
    assert user.is_superuser == user_data["is_superuser"]


@pytest.mark.asyncio
async def test_delete_user(superuser_client: AsyncClient, db: AsyncSession) -> None:
    """Test deleting a user as a superuser."""
    # Create a test user
    test_user = User(
        email="delete_user@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Delete User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
    )
    
    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)
    
    # Delete user
    response = await superuser_client.delete(f"/api/v1/users/{test_user.id}")
    
    # Check response
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Check that user was deleted from the database
    result = await db.execute(select(User).where(User.id == test_user.id))
    user = result.scalars().first()
    assert user is None


@pytest.mark.asyncio
async def test_delete_self(superuser_client: AsyncClient, db: AsyncSession) -> None:
    """Test that a user cannot delete themselves."""
    # Get current user ID
    response = await superuser_client.get("/api/v1/users/me")
    data = response.json()
    user_id = data["id"]
    
    # Try to delete self
    response = await superuser_client.delete(f"/api/v1/users/{user_id}")
    
    # Check response
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Users cannot delete themselves"