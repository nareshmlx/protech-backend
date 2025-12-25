"""Authentication and authorization specific exceptions."""

from app.exceptions.base_exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ConflictError
)


class InvalidCredentialsError(AuthenticationError):
    """Invalid login credentials."""

    def __init__(self):
        super().__init__(message="Invalid credentials")


class EmailAlreadyExistsError(ConflictError):
    """Email already registered."""

    def __init__(self, email: str):
        super().__init__(
            message="Email already exists",
            details={"email": email}
        )


class UserNotFoundError(AuthenticationError):
    """User not found."""

    def __init__(self):
        super().__init__(message="Invalid credentials")


class WeakPasswordError(ValidationError):
    """Password does not meet security requirements."""

    def __init__(self, min_length: int):
        super().__init__(
            message=f"Password must be at least {min_length} characters",
            details={"min_length": min_length}
        )


class AdminAccessRequiredError(AuthorizationError):
    """Admin access required for this operation."""

    def __init__(self):
        super().__init__(message="Admin access required")
