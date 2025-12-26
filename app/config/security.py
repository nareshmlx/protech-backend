"""
Security utilities for password hashing and JWT token management.

Production notes:
- Access tokens MAY include exp based on settings.ACCESS_TOKEN_EXPIRE_HOURS
- Refresh tokens ALWAYS include exp based on settings.REFRESH_TOKEN_EXPIRE_DAYS
- Token type is enforced (access vs refresh)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt

from app.config.settings import settings

logger = logging.getLogger(__name__)


class PasswordService:
    """Service for password hashing and verification using bcrypt."""

    def __init__(self, rounds: int = 12):
        self.rounds = rounds

    def hash_password(self, password: str) -> str:
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception as exc:
            logger.error("Password verification error: %s", exc)
            return False


class TokenService:
    """Service for JWT token creation and verification."""

    def __init__(self):
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_hours = settings.access_token_expire_hours
        self.refresh_token_expire_days = settings.refresh_token_expire_days

    def create_access_token(
        self,
        user_id: str,
        role: str,
        expires_in_hours: Optional[int] = None,
    ) -> str:
        now = datetime.now(timezone.utc)

        payload: dict[str, Any] = {
            "sub": user_id,
            "role": role,
            "type": "access",
            "iat": int(now.timestamp()),
        }

        exp_hours = (
            expires_in_hours
            if expires_in_hours is not None
            else self.access_token_expire_hours
        )
        if exp_hours:  # allow "no exp" in dev if configured as empty/0/None
            payload["exp"] = int((now + timedelta(hours=exp_hours)).timestamp())

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        expires_in_days: Optional[int] = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        days = (
            expires_in_days
            if expires_in_days is not None
            else self.refresh_token_expire_days
        )

        payload: dict[str, Any] = {
            "sub": user_id,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=days)).timestamp()),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, expected_type: str = "access") -> dict:
        """
        Decode + validate token signature and claims, and enforce token type.
        Raises PyJWT exceptions on invalid/expired tokens.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            token_type = payload.get("type")
            if token_type != expected_type:
                raise ValueError(
                    f"Invalid token type. Expected {expected_type}, got {token_type}"
                )

            logger.debug("Token verified successfully: type=%s", token_type)
            return payload
        except Exception as exc:
            logger.error("Token verification error: %s", exc)
            raise

    def decode_token(self, token: str, expected_type: str = "access") -> dict:
        """
        Compatibility method used by dependencies/services.
        """
        return self.verify_token(token, expected_type=expected_type)

    def validate_token_type(self, payload: dict, expected_type: str) -> bool:
        """
        Compatibility method used by services.
        Returns True/False (does not raise) to match existing call-sites.
        """
        try:
            return payload.get("type") == expected_type
        except Exception:
            return False

    def get_user_id_from_token(self, token: str, expected_type: str = "access") -> str:
        payload = self.verify_token(token, expected_type=expected_type)
        return str(payload.get("sub"))


password_service = PasswordService()
token_service = TokenService()