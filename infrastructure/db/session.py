from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    def init_engine(self) -> None:
        if self._engine is not None:
            logger.warning("Database engine already initialized")
            return

        self._engine = create_async_engine(
            settings.database_url,
            echo=settings.db_echo,
            future=True,
        )

        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("Async database engine initialized")

    async def close(self) -> None:
        if self._engine is None:
            return

        await self._engine.dispose()
        self._engine = None
        self._session_maker = None
        logger.info("Database engine closed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if self._session_maker is None:
            raise RuntimeError("DB engine not initialized")

        async with self._session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


db_manager = DatabaseSessionManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session
