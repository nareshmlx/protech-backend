"""Authentication service with business logic."""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging
import jwt

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.config.security import password_service, token_service
from app.exceptions.auth_exceptions import (
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    UserNotFoundError,
    WeakPasswordError
)
from app.exceptions.base_exceptions import (
    InactiveUserError,
    TokenExpiredError,
    InvalidTokenError
)
from app.config.settings import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, user_repository: UserRepository):
        """Initialize authentication service.

        Args:
            user_repository: User repository instance
        """
        self.user_repository = user_repository

    async def signup(
        self,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> User:
        """Register a new user.

        Args:
            email: User's email address
            password: User's plain text password
            first_name: User's first name
            last_name: User's last name
            role: User role (default: USER)

        Returns:
            Created user instance

        Raises:
            EmailAlreadyExistsError: Email already registered
            WeakPasswordError: Password doesn't meet requirements
        """
        # Validate password strength
        if len(password) < settings.min_password_length:
            logger.warning(f"Signup failed: password too short for {email}")
            raise WeakPasswordError(settings.min_password_length)

        # Check if email already exists
        if await self.user_repository.email_exists(email):
            logger.warning(f"Signup failed: email already exists - {email}")
            raise EmailAlreadyExistsError(email)

        # Hash password
        password_hash = password_service.hash_password(password)

        # Create user
        user = await self.user_repository.create(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role
        )

        logger.info(f"User signed up successfully: {user.email} (ID: {user.id})")
        return user

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and generate tokens.

        Args:
            email: User's email address
            password: User's plain text password

        Returns:
            Dictionary containing user and tokens

        Raises:
            InvalidCredentialsError: Invalid email or password
            InactiveUserError: User account is inactive
        """
        # Get user by email
        user = await self.user_repository.get_by_email(email)
        if not user:
            logger.warning(f"Login failed: user not found - {email}")
            raise InvalidCredentialsError()

        # Verify password
        if not password_service.verify_password(password, user.password_hash):
            logger.warning(f"Login failed: invalid password for {email}")
            raise InvalidCredentialsError()

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed: inactive user - {email}")
            raise InactiveUserError()

        # Update last login timestamp
        await self.user_repository.update_last_login(str(user.id))

        # Generate tokens
        access_token = token_service.create_access_token(
            str(user.id),
            user.role.value
        )
        refresh_token = token_service.create_refresh_token(str(user.id))

        logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token.

        Production-grade behavior:
        - Verify token is a refresh token
        - Issue a new access token
        - Rotate refresh token (issue a new refresh token)
        """
        try:
            # Decode refresh token (MUST be refresh type)
            payload = token_service.decode_token(refresh_token, expected_type="refresh")

            user_id = payload.get("sub")
            user = await self.user_repository.get_by_id(user_id)

            if not user:
                logger.warning(f"Token refresh failed: user not found - {user_id}")
                raise UserNotFoundError()

            if not user.is_active:
                logger.warning(f"Token refresh failed: inactive user - {user.email}")
                raise InactiveUserError()

            # Issue new tokens (rotate refresh token)
            new_access_token = token_service.create_access_token(
                str(user.id),
                user.role.value,
            )
            new_refresh_token = token_service.create_refresh_token(str(user.id))

            logger.info("Tokens refreshed for user: %s", user.email)

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
            }

        except jwt.ExpiredSignatureError:
            logger.warning("Token refresh failed: token expired")
            raise TokenExpiredError()
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token refresh failed: invalid token - {str(e)}")
            raise InvalidTokenError()

    async def get_current_user(self, token: str) -> User:
        """Get current authenticated user from token.

        Args:
            token: JWT access token

        Returns:
            User instance

        Raises:
            InvalidTokenError: Token is invalid or wrong type
            UserNotFoundError: User not found
            InactiveUserError: User account is inactive
        """
        try:
            # Decode token
            payload = token_service.decode_token(token)

            # Validate token type
            if not token_service.validate_token_type(payload, "access"):
                logger.warning("Get current user failed: invalid token type")
                raise InvalidTokenError("Invalid token type")

            # Get user
            user_id = payload.get("sub")
            user = await self.user_repository.get_by_id(user_id)

            if not user:
                logger.warning(f"Get current user failed: user not found - {user_id}")
                raise UserNotFoundError()

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Get current user failed: inactive user - {user.email}")
                raise InactiveUserError()

            return user

        except jwt.ExpiredSignatureError:
            # This shouldn't happen for access tokens (no expiration)
            # but we handle it anyway for safety
            logger.warning("Get current user failed: token expired")
            raise TokenExpiredError()
        except jwt.InvalidTokenError as e:
            logger.warning(f"Get current user failed: invalid token - {str(e)}")
            raise InvalidTokenError()

    async def validate_admin(self, user: User) -> bool:
        """Validate that user has admin role.

        Args:
            user: User instance to validate

        Returns:
            True if user is admin

        Raises:
            AuthorizationError: User is not an admin (raised by dependency)
        """
        return user.role == UserRole.ADMIN

    async def logout(self, user: User) -> None:
        """Logout user (client-side token removal).

        Note: This is a stateless JWT implementation, so logout
        is primarily handled client-side by discarding tokens.
        This method logs the event for audit purposes.

        Args:
            user: User instance to logout
        """
        logger.info(f"User logged out: {user.email} (ID: {user.id})")
        # In a future enhancement, we could add token blacklisting here
        # using Redis with token expiration
