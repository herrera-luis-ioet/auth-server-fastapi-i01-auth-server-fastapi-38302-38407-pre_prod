"""
Token schemas for the Authentication Management Component

This module defines Pydantic schemas for JWT token handling.
"""

from typing import Optional

from pydantic import BaseModel


# PUBLIC_INTERFACE
class Token(BaseModel):
    """
    Schema for JWT token response.
    
    Attributes:
        access_token: JWT access token
        refresh_token: JWT refresh token for obtaining new access tokens
        token_type: Type of token (always "bearer")
    """
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# PUBLIC_INTERFACE
class TokenPayload(BaseModel):
    """
    Schema for JWT token payload.
    
    Attributes:
        sub: Subject of the token (user ID)
        exp: Expiration timestamp
        type: Token type ("access" or "refresh")
    """
    
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None


# PUBLIC_INTERFACE
class TokenRefresh(BaseModel):
    """
    Schema for refresh token request.
    
    Attributes:
        refresh_token: JWT refresh token
    """
    
    refresh_token: str


# PUBLIC_INTERFACE
class PasswordResetRequest(BaseModel):
    """
    Schema for password reset request.
    
    Attributes:
        email: User's email address
    """
    
    email: str


# PUBLIC_INTERFACE
class PasswordReset(BaseModel):
    """
    Schema for password reset.
    
    Attributes:
        token: Password reset token
        new_password: New password
    """
    
    token: str
    new_password: str


# PUBLIC_INTERFACE
class EmailVerification(BaseModel):
    """
    Schema for email verification.
    
    Attributes:
        token: Email verification token
    """
    
    token: str