"""
CRUD operations for the Authentication Management Component

This package provides CRUD (Create, Read, Update, Delete) operations
for database models used in the Authentication Management Component.
"""

from app.crud.base import CRUDBase
from app.crud.crud_user import CRUDUser, user

# Export classes and instances for easy importing
__all__ = ["CRUDBase", "CRUDUser", "user"]