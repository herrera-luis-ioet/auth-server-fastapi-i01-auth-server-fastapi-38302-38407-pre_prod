"""
FastAPI application entry point for the Authentication Management Component

This module initializes and configures the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings

# Create FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Authentication and Authorization Service API",
    version="0.1.0",
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint that returns basic API information.
    """
    return {
        "message": "Authentication Management Component API",
        "docs": "/docs",
        "version": "0.1.0",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {"status": "healthy"}


# Include API routers
# This will be implemented in future tasks
# from app.api.api_v1.api import api_router
# app.include_router(api_router, prefix=settings.API_V1_STR)


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Actions to run on application startup.
    """
    # Database initialization will be implemented in future tasks
    # await init_db()
    pass


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to run on application shutdown.
    """
    # Close connections and perform cleanup
    pass