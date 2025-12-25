"""User repository for user-specific database operations."""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User model with specific query methods."""

    def __init__(self, session: AsyncSession):
        """Initialize user repository.

        Args:
            session: Async database session
        """
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address.

        Args:
            email: User's email address

        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered.

        Args:
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        return await self.exists(email=email)

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get all active users.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active users
        """
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_admins(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get all admin users.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of admin users
        """
        result = await self.session.execute(
            select(User)
            .where(User.role == UserRole.ADMIN)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_last_login(self, user_id: str) -> Optional[User]:
        """Update the last login timestamp for a user.

        Args:
            user_id: User's UUID

        Returns:
            Updated user or None if not found
        """
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(user)
            logger.info(f"Updated last login for user: {user.email}")
        return user

    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate a user account.

        Args:
            user_id: User's UUID

        Returns:
            Updated user or None if not found
        """
        return await self.update(user_id, is_active=False)

    async def activate_user(self, user_id: str) -> Optional[User]:
        """Activate a user account.

        Args:
            user_id: User's UUID

        Returns:
            Updated user or None if not found
        """
        return await self.update(user_id, is_active=True)

    async def change_role(self, user_id: str, role: UserRole) -> Optional[User]:
        """Change a user's role.

        Args:
            user_id: User's UUID
            role: New role to assign

        Returns:
            Updated user or None if not found
        """
        return await self.update(user_id, role=role)

    async def count_active_users(self) -> int:
        """Count active users.

        Returns:
            Number of active users
        """
        return await self.count(is_active=True)

    async def count_admins(self) -> int:
        """Count admin users.

        Returns:
            Number of admin users
        """
        return await self.count(role=UserRole.ADMIN)
