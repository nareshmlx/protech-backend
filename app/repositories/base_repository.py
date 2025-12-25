"""Base repository with generic CRUD operations."""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    """Base repository providing generic CRUD operations.

    Args:
        model: SQLAlchemy model class
        session: Async database session
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """Initialize base repository.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record.

        Args:
            **kwargs: Field values for the new record

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        logger.debug(f"Created {self.model.__name__} with id: {instance.id}")
        return instance

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get a record by its ID.

        Args:
            id: Primary key value

        Returns:
            Model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get all records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field name to order by

        Returns:
            List of model instances
        """
        query = select(self.model)

        if order_by:
            query = query.order_by(getattr(self.model, order_by))

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """Get a record by a specific field value.

        Args:
            field_name: Name of the field to filter by
            value: Value to match

        Returns:
            Model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(getattr(self.model, field_name) == value)
        )
        return result.scalar_one_or_none()

    async def get_many_by_field(
        self,
        field_name: str,
        value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records by a specific field value.

        Args:
            field_name: Name of the field to filter by
            value: Value to match
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        result = await self.session.execute(
            select(self.model)
            .where(getattr(self.model, field_name) == value)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self,
        id: Any,
        **kwargs: Any
    ) -> Optional[ModelType]:
        """Update a record by ID.

        Args:
            id: Primary key value
            **kwargs: Field values to update

        Returns:
            Updated model instance or None if not found
        """
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        logger.debug(f"Updated {self.model.__name__} with id: {id}")
        return instance

    async def delete(self, id: Any) -> bool:
        """Delete a record by ID.

        Args:
            id: Primary key value

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(id)
        if not instance:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        logger.debug(f"Deleted {self.model.__name__} with id: {id}")
        return True

    async def exists(self, **kwargs: Any) -> bool:
        """Check if a record exists.

        Args:
            **kwargs: Field name and value pairs to filter by

        Returns:
            True if record exists, False otherwise
        """
        conditions = [getattr(self.model, key) == value for key, value in kwargs.items()]
        query = select(func.count()).select_from(self.model).where(*conditions)
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0

    async def count(self, **kwargs: Any) -> int:
        """Count records matching the given criteria.

        Args:
            **kwargs: Field name and value pairs to filter by

        Returns:
            Number of matching records
        """
        if kwargs:
            conditions = [getattr(self.model, key) == value for key, value in kwargs.items()]
            query = select(func.count()).select_from(self.model).where(*conditions)
        else:
            query = select(func.count()).select_from(self.model)

        result = await self.session.execute(query)
        return result.scalar() or 0
