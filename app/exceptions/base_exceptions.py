"""Custom exception classes for the application."""

from typing import Any, Optional, Dict


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize application exception.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppException):
    """Validation error exception (400 Bad Request)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=400, details=details)


class AuthenticationError(AppException):
    """Authentication error exception (401 Unauthorized)."""

    def __init__(self, message: str = "Invalid credentials", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=401, details=details)


class AuthorizationError(AppException):
    """Authorization error exception (403 Forbidden)."""

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=403, details=details)


class NotFoundError(AppException):
    """Resource not found exception (404 Not Found)."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=404, details=details)


class ConflictError(AppException):
    """Resource conflict exception (409 Conflict)."""

    def __init__(self, message: str = "Resource already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=409, details=details)


class TokenExpiredError(AuthenticationError):
    """Token expired exception (401 Unauthorized)."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message=message)


class InvalidTokenError(AuthenticationError):
    """Invalid token exception (401 Unauthorized)."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message=message)


class InactiveUserError(AuthenticationError):
    """Inactive user exception (401 Unauthorized)."""

    def __init__(self, message: str = "User account is inactive"):
        super().__init__(message=message)
