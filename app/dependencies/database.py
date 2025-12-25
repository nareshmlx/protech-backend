"""Database dependencies for FastAPI."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.db.session import get_db


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session.

    Yields:
        AsyncSession instance for database operations
    """
    async for session in get_db():
        yield session
