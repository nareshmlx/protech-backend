"""Security utilities for password hashing and JWT token management."""

import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from app.config.settings import settings


class PasswordService:
    """Service for password hashing and verification using bcrypt."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plain text password to hash

        Returns:
            Hashed password as string
        """
        salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash using constant-time comparison.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False


class TokenService:
    """Service for JWT token creation and validation."""

    @staticmethod
    def create_access_token(user_id: str, role: str) -> str:
        """Create an access token that never expires.

        Args:
            user_id: UUID of the user
            role: Role of the user (user or admin)

        Returns:
            Encoded JWT access token
        """
        payload: Dict[str, Any] = {
            "sub": str(user_id),
            "role": role,
            "type": "access",
            "iat": datetime.now(timezone.utc)
        }
        # NO "exp" field - token never expires
        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a refresh token that expires after configured days.

        Args:
            user_id: UUID of the user

        Returns:
            Encoded JWT refresh token
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.refresh_token_expire_days)

        payload: Dict[str, Any] = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expires_at
        }
        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and verify a JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Decoded token payload

        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
        """
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )

    @staticmethod
    def validate_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
        """Validate that the token has the expected type.

        Args:
            payload: Decoded token payload
            expected_type: Expected token type ("access" or "refresh")

        Returns:
            True if token type matches, False otherwise
        """
        return payload.get("type") == expected_type


# Global service instances
password_service = PasswordService()
token_service = TokenService()
