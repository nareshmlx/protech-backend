"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import logging

from app.schemas.v1.auth_schemas import (
    SignupRequest,
    LoginRequest,
    RefreshTokenRequest,
    AuthResponse,
    TokenResponse,
    UserResponse,
    MessageResponse,
    ErrorResponse
)
from app.models.user import User
from app.services.auth_service import AuthService
from app.dependencies.auth import (
    get_auth_service,
    get_current_active_user,
    get_current_admin,
    AuthServiceDep,
    CurrentActiveUser,
    CurrentAdmin
)
from app.exceptions.base_exceptions import AppException
from app.exceptions.auth_exceptions import (
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    WeakPasswordError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Email already exists"}
    },
    summary="User Signup",
    description="Register a new user account with email and password"
)
async def signup(
    request: SignupRequest,
    auth_service: AuthServiceDep
) -> Dict[str, Any]:
    """Register a new user.

    Args:
        request: Signup request with email, password, and optional names
        auth_service: Authentication service instance

    Returns:
        User information and authentication tokens

    Raises:
        HTTPException: 409 if email exists, 400 if validation fails
    """
    try:
        # Create user
        user = await auth_service.signup(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name
        )

        # Login user to get tokens
        auth_data = await auth_service.login(request.email, request.password)

        return {
            "user": UserResponse.model_validate(user),
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"],
            "token_type": auth_data["token_type"]
        }

    except EmailAlreadyExistsError as e:
        logger.warning(f"Signup failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except WeakPasswordError as e:
        logger.warning(f"Signup failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except AppException as e:
        logger.error(f"Signup failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"}
    },
    summary="User Login",
    description="Authenticate user and receive access and refresh tokens"
)
async def login(
    request: LoginRequest,
    auth_service: AuthServiceDep
) -> Dict[str, Any]:
    """Authenticate user and return tokens.

    Args:
        request: Login request with email and password
        auth_service: Authentication service instance

    Returns:
        User information and authentication tokens

    Raises:
        HTTPException: 401 if authentication fails
    """
    try:
        # Authenticate user
        auth_data = await auth_service.login(request.email, request.password)

        return {
            "user": UserResponse.model_validate(auth_data["user"]),
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"],
            "token_type": auth_data["token_type"]
        }

    except InvalidCredentialsError as e:
        logger.warning(f"Login failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except AppException as e:
        logger.error(f"Login failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"model": ErrorResponse, "description": "Invalid or expired token"}
    },
    summary="Refresh Access Token",
    description="Exchange refresh token for a new access token"
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthServiceDep
) -> Dict[str, str]:
    """Refresh access token using refresh token.

    Args:
        request: Refresh token request
        auth_service: Authentication service instance

    Returns:
        New access token

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    try:
        # Refresh access token
        token_data = await auth_service.refresh_access_token(request.refresh_token)

        return token_data

    except AppException as e:
        logger.warning(f"Token refresh failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "User details retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    },
    summary="Get Current User",
    description="Retrieve authenticated user details"
)
async def get_me(current_user: CurrentActiveUser) -> UserResponse:
    """Get current authenticated user details.

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        User information
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Logout successful"},
        401: {"model": ErrorResponse, "description": "Authentication required"}
    },
    summary="User Logout",
    description="Logout user (client should discard tokens)"
)
async def logout(
    current_user: CurrentActiveUser,
    auth_service: AuthServiceDep
) -> Dict[str, str]:
    """Logout current user.

    Note: This is a stateless JWT implementation. The client should
    discard the tokens. This endpoint logs the event for audit purposes.

    Args:
        current_user: Current authenticated user from dependency
        auth_service: Authentication service instance

    Returns:
        Success message
    """
    try:
        await auth_service.logout(current_user)
        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Unexpected error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


# Admin-only endpoints (examples)
@router.get(
    "/admin/users",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Users retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Admin access required"}
    },
    summary="Get All Users (Admin Only)",
    description="Retrieve all users - requires admin role"
)
async def get_all_users(current_admin: CurrentAdmin) -> Dict[str, Any]:
    """Get all users (admin only endpoint example).

    Args:
        current_admin: Current authenticated admin user

    Returns:
        Message confirming admin access
    """
    return {
        "message": "Admin access granted",
        "admin_email": current_admin.email,
        "note": "This is a placeholder for user list functionality"
    }
