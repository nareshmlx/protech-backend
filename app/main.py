"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config.settings import settings
from app.exceptions.base_exceptions import AppException
from app.api.v1.endpoints import auth
from infrastructure.db.session import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info("Starting ProTech Surveillance System Backend")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize database
    db_manager.init_engine()
    logger.info("Database engine initialized")

    yield

    # Shutdown
    logger.info("Shutting down ProTech Surveillance System Backend")
    await db_manager.close()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Backend API for ProTech Surveillance System with authentication and authorization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Global exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions.

    Args:
        request: The request that caused the exception
        exc: The application exception

    Returns:
        JSON response with error details
    """
    logger.warning(
        f"AppException: {exc.message} - Path: {request.url.path} - "
        f"Status: {exc.status_code}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: The request that caused the exception
        exc: The validation exception

    Returns:
        JSON response with validation error details
    """
    logger.warning(f"Validation error: {exc.errors()} - Path: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Validation error",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: The request that caused the exception
        exc: The exception

    Returns:
        JSON response with generic error message
    """
    logger.error(
        f"Unexpected error: {str(exc)} - Path: {request.url.path}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "An unexpected error occurred",
            "details": {} if settings.is_production else {"error": str(exc)}
        }
    )


# Health check endpoint
@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running"
)
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }


# Include routers
app.include_router(auth.router, prefix=settings.api_v1_prefix)


# Root endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="Root Endpoint",
    description="Get API information"
)
async def root() -> dict:
    """Root endpoint.

    Returns:
        API information
    """
    return {
        "message": "Welcome to ProTech Surveillance System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
