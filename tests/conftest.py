"""
Pytest configuration and fixtures for the Authentication Management Component

This module provides fixtures for testing the Authentication Management Component,
including database and application testing fixtures.
"""

import asyncio
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.api.deps import get_current_active_user, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.main import app
from app.models.user import User


# Use an in-memory SQLite database for testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for testing
test_engine = create_async_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)

# Create async session factory for testing
TestingSessionLocal = sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Override the get_db dependency for testing
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Override the get_db dependency for testing.
    
    Yields:
        AsyncSession: SQLAlchemy async session for testing
    """
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Test user data
test_user_id = uuid.uuid4()
test_user_email = "test@example.com"
test_user_password = "TestPassword123"
test_user_hashed_password = get_password_hash(test_user_password)


# Override the get_current_user dependency for testing
async def override_get_current_user() -> User:
    """
    Override the get_current_user dependency for testing.
    
    Returns:
        User: Test user for authentication
    """
    return User(
        id=test_user_id,
        email=test_user_email,
        hashed_password=test_user_hashed_password,
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# Override the get_current_active_superuser dependency for testing
async def override_get_current_superuser() -> User:
    """
    Override the get_current_active_superuser dependency for testing.
    
    Returns:
        User: Test superuser for authentication
    """
    return User(
        id=test_user_id,
        email=test_user_email,
        hashed_password=test_user_hashed_password,
        full_name="Test Superuser",
        is_active=True,
        is_superuser=True,
        email_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an instance of the default event loop for each test case.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture that creates a fresh database for each test.
    
    Yields:
        AsyncSession: SQLAlchemy async session for testing
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Use the session
    async with TestingSessionLocal() as session:
        yield session
    
    # Drop all tables after the test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that creates a test client with the FastAPI application.
    
    Args:
        db: Database session fixture
        
    Yields:
        AsyncClient: Test client for making HTTP requests
    """
    # Override dependencies
    app.dependency_overrides = {
        get_db: lambda: override_get_db(),
    }
    
    # Use the client
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clear dependency overrides
    app.dependency_overrides = {}


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that creates an authenticated test client with a valid JWT token.
    
    Args:
        db: Database session fixture
        
    Yields:
        AsyncClient: Authenticated test client for making HTTP requests
    """
    # Create a test user
    test_user = User(
        id=test_user_id,
        email=test_user_email,
        hashed_password=test_user_hashed_password,
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(test_user)
    await db.commit()
    
    # Create access token
    access_token = create_access_token(test_user.id)
    
    # Override dependencies
    app.dependency_overrides = {
        get_db: lambda: override_get_db(),
        get_current_user: lambda: override_get_current_user(),
    }
    
    # Use the client with authentication
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"Authorization": f"Bearer {access_token}"}
    ) as client:
        yield client
    
    # Clear dependency overrides
    app.dependency_overrides = {}


@pytest_asyncio.fixture(scope="function")
async def superuser_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that creates an authenticated test client with superuser privileges.
    
    Args:
        db: Database session fixture
        
    Yields:
        AsyncClient: Authenticated superuser test client for making HTTP requests
    """
    # Create a test superuser
    test_superuser = User(
        id=test_user_id,
        email=test_user_email,
        hashed_password=test_user_hashed_password,
        full_name="Test Superuser",
        is_active=True,
        is_superuser=True,
        email_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(test_superuser)
    await db.commit()
    
    # Create access token
    access_token = create_access_token(test_superuser.id)
    
    # Override dependencies
    app.dependency_overrides = {
        get_db: lambda: override_get_db(),
        get_current_user: lambda: override_get_current_superuser(),
    }
    
    # Use the client with authentication
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"Authorization": f"Bearer {access_token}"}
    ) as client:
        yield client
    
    # Clear dependency overrides
    app.dependency_overrides = {}


@pytest_asyncio.fixture(scope="function")
async def test_user_token(db: AsyncSession) -> Dict[str, str]:
    """
    Fixture that creates a test user and returns access and refresh tokens.
    
    Args:
        db: Database session fixture
        
    Returns:
        Dict[str, str]: Dictionary with access_token and refresh_token
    """
    # Create a test user
    test_user = User(
        id=test_user_id,
        email=test_user_email,
        hashed_password=test_user_hashed_password,
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        email_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(test_user)
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(test_user.id)
    refresh_token = create_access_token(
        test_user.id,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }