"""Authentication request and response schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from app.config.settings import settings


# Request Schemas
class SignupRequest(BaseModel):
    """User signup request schema."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=settings.min_password_length, description="User's password")
    first_name: Optional[str] = Field(None, max_length=100, description="User's first name")
    last_name: Optional[str] = Field(None, max_length=100, description="User's last name")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets minimum requirements.

        Args:
            v: Password string

        Returns:
            Validated password

        Raises:
            ValueError: If password is too short
        """
        if len(v) < settings.min_password_length:
            raise ValueError(f"Password must be at least {settings.min_password_length} characters")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "SecurePassword123",
                    "first_name": "John",
                    "last_name": "Doe"
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "SecurePassword123"
                }
            ]
        }
    }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="Refresh token to exchange for new access token")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            ]
        }
    }


# Response Schemas
class UserResponse(BaseModel):
    """User information response schema."""

    id: UUID = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    role: str = Field(..., description="User's role (user or admin)")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "user",
                    "is_active": True,
                    "created_at": "2023-01-01T00:00:00Z",
                    "last_login_at": "2023-01-15T10:30:00Z"
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """Authentication token response schema."""

    access_token: str = Field(..., description="JWT access token (never expires)")
    refresh_token: str = Field(..., description="JWT refresh token (expires in 30 days)")
    token_type: str = Field(default="bearer", description="Token type")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer"
                }
            ]
        }
    }


class AuthResponse(BaseModel):
    """Complete authentication response schema."""

    user: UserResponse = Field(..., description="User information")
    access_token: str = Field(..., description="JWT access token (never expires)")
    refresh_token: str = Field(..., description="JWT refresh token (expires in 30 days)")
    token_type: str = Field(default="bearer", description="Token type")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "user@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "role": "user",
                        "is_active": True,
                        "created_at": "2023-01-01T00:00:00Z",
                        "last_login_at": "2023-01-15T10:30:00Z"
                    },
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer"
                }
            ]
        }
    }


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str = Field(..., description="Response message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Operation completed successfully"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Error response schema."""

    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Invalid credentials",
                    "details": {}
                }
            ]
        }
    }
