"""
Base CRUD class for the Authentication Management Component

This module provides a generic CRUD class with common database operations
for SQLAlchemy models.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

# Define generic type variables
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


# PUBLIC_INTERFACE
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations.
    
    Generic base class that provides standard create, read, update, delete operations
    for SQLAlchemy models.
    
    Attributes:
        model: The SQLAlchemy model class
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize the CRUD base class with a SQLAlchemy model.
        
        Args:
            model: The SQLAlchemy model class
        """
        self.model = model
    
    # PUBLIC_INTERFACE
    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            db: Database session
            id: UUID of the record to get
            
        Returns:
            The model instance if found, None otherwise
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()
    
    # PUBLIC_INTERFACE
    async def get_by_attribute(
        self, db: AsyncSession, attr_name: str, attr_value: Any
    ) -> Optional[ModelType]:
        """
        Get a single record by a specific attribute.
        
        Args:
            db: Database session
            attr_name: Name of the attribute to filter by
            attr_value: Value of the attribute to filter by
            
        Returns:
            The model instance if found, None otherwise
        """
        result = await db.execute(
            select(self.model).where(getattr(self.model, attr_name) == attr_value)
        )
        return result.scalars().first()
    
    # PUBLIC_INTERFACE
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()
    
    # PUBLIC_INTERFACE
    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Pydantic schema with the data to create
            
        Returns:
            The created model instance
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    # PUBLIC_INTERFACE
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db: Database session
            db_obj: The model instance to update
            obj_in: Pydantic schema or dict with the data to update
            
        Returns:
            The updated model instance
        """
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    # PUBLIC_INTERFACE
    async def remove(self, db: AsyncSession, *, id: UUID) -> Optional[ModelType]:
        """
        Remove a record by ID.
        
        Args:
            db: Database session
            id: UUID of the record to remove
            
        Returns:
            The removed model instance if found, None otherwise
        """
        obj = await self.get(db=db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
    
    # PUBLIC_INTERFACE
    async def exists(self, db: AsyncSession, id: UUID) -> bool:
        """
        Check if a record exists by ID.
        
        Args:
            db: Database session
            id: UUID of the record to check
            
        Returns:
            True if the record exists, False otherwise
        """
        result = await db.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar() is not None
    
    # PUBLIC_INTERFACE
    async def exists_by_attribute(
        self, db: AsyncSession, attr_name: str, attr_value: Any
    ) -> bool:
        """
        Check if a record exists by a specific attribute.
        
        Args:
            db: Database session
            attr_name: Name of the attribute to filter by
            attr_value: Value of the attribute to filter by
            
        Returns:
            True if the record exists, False otherwise
        """
        result = await db.execute(
            select(self.model.id).where(getattr(self.model, attr_name) == attr_value)
        )
        return result.scalar() is not None
    
    # PUBLIC_INTERFACE
    async def count(self, db: AsyncSession) -> int:
        """
        Count the total number of records.
        
        Args:
            db: Database session
            
        Returns:
            Total number of records
        """
        result = await db.execute(select(self.model.id))
        return len(result.scalars().all())