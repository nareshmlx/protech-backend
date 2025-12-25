"""Authentication and authorization dependencies for FastAPI."""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.exceptions.base_exceptions import (
    AuthenticationError,
    AuthorizationError,
    InactiveUserError,
    InvalidTokenError
)
from infrastructure.db.session import get_db
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
http_bearer = HTTPBearer(auto_error=True)


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency to get user repository.

    Args:
        db: Database session

    Returns:
        UserRepository instance
    """
    return UserRepository(db)


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """Dependency to get authentication service.

    Args:
        user_repo: User repository instance

    Returns:
        AuthService instance
    """
    return AuthService(user_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Dependency to get current authenticated user.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        auth_service: Authentication service instance

    Returns:
        Current authenticated user

    Raises:
        HTTPException: 401 if authentication fails
    """
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        return user
    except (AuthenticationError, InvalidTokenError, InactiveUserError) as e:
        logger.warning(f"Authentication failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        HTTPException: 401 if user is inactive
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to get current admin user.

    Args:
        current_user: Current authenticated active user

    Returns:
        Current admin user

    Raises:
        HTTPException: 403 if user is not an admin
    """
    if not current_user.is_admin:
        logger.warning(
            f"Non-admin user attempted admin access: {current_user.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Type aliases for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
