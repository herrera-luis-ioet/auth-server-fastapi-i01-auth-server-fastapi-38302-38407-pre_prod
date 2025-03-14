"""
API router for the Authentication Management Component

This module sets up the main API router and includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users

# Create main API router
api_router = APIRouter()

# Include endpoint routers with appropriate prefixes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])