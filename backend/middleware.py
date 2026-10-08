"""
CHIXUS Centralized Middleware for Global Exception Handling & Request Logging
Provides standardized error responses and comprehensive request/response logging
Environment: Termux on ARM64 Android
Master Passkey: CHIXUS-ADMIN-@)@^
"""

import logging
import time
import json
import sqlite3
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from enum import Enum

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standardized error codes"""
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONFLICT = "CONFLICT"
    DATABASE_ERROR = "DATABASE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


class ErrorResponse:
    """Standardized error response builder"""

    @staticmethod
    def build(
        error: bool = True,
        code: str = ErrorCode.UNKNOWN.value,
        message: str = "An unknown error occurred",
        timestamp: Optional[str] = None,
        status_code: int = 500
    ) -> tuple[Dict[str, Any], int]:
        """
        Build a standardized error response
        
        Args:
            error: Whether this is an error response
            code: Error code enum
            message: Human-readable error message
            timestamp: ISO timestamp (auto-generated if not provided)
            status_code: HTTP status code
            
        Returns:
            Tuple of (response_dict, http_status_code)
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        response = {
            "error": error,
            "code": code,
            "message": message,
            "timestamp": timestamp
        }

        return response, status_code

    @staticmethod
    def validation_error(details: Any, timestamp: Optional[str] = None) -> tuple[Dict[str, Any], int]:
        """Build validation error response"""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        return {
            "error": True,
            "code": ErrorCode.VALIDATION_ERROR.value,
            "message": "Request validation failed",
            "details": details if isinstance(details, list) else [str(details)],
            "timestamp": timestamp
        }, 422

    @staticmethod
    def from_exception(exc: Exception, timestamp: Optional[str] = None) -> tuple[Dict[str, Any], int]:
        """
        Map exception to standardized error response
        
        Args:
            exc: Exception instance
            timestamp: ISO timestamp
            
        Returns:
            Tuple of (response_dict, http_status_code)
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        # Map exception types to error codes and status codes
        if isinstance(exc, ValueError):
            return ErrorResponse.build(
                code=ErrorCode.INVALID_REQUEST.value,
                message=str(exc) or "Invalid value provided",
                timestamp=timestamp,
                status_code=400
            )
        elif isinstance(exc, KeyError):
            return ErrorResponse.build(
                code=ErrorCode.RESOURCE_NOT_FOUND.value,
                message=f"Resource not found: {str(exc)}",
                timestamp=timestamp,
                status_code=404
            )
        elif isinstance(exc, PermissionError):
            return ErrorResponse.build(
                code=ErrorCode.AUTHORIZATION_FAILED.value,
                message="Permission denied",
                timestamp=timestamp,
                status_code=403
            )
        elif isinstance(exc, sqlite3.DatabaseError):
            # Handle SQLite errors
            error_str = str(exc).lower()
            if "locked" in error_str or "timeout" in error_str:
                return ErrorResponse.build(
                    code=ErrorCode.TIMEOUT.value,
                    message="Database temporarily locked. Please retry.",
                    timestamp=timestamp,
                    status_code=503
                )
            else:
                return ErrorResponse.build(
                    code=ErrorCode.DATABASE_ERROR.value,
                    message="Database error occurred",
                    timestamp=timestamp,
                    status_code=500
                )
        elif isinstance(exc, TimeoutError):
            return ErrorResponse.build(
                code=ErrorCode.TIMEOUT.value,
                message="Request timeout",
                timestamp=timestamp,
                status_code=504
            )
        else:
            # Default to internal error
            return ErrorResponse.build(
                code=ErrorCode.INTERNAL_ERROR.value,
                message="An internal server error occurred",
                timestamp=timestamp,
                status_code=500
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request and response logging
    Logs HTTP method, endpoint, status code, processing time, and metadata
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """
        Intercept request/response cycle and log details
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response
        """
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params) if request.query_params else {}
        
        # Try to extract client IP
        client_host = request.client.host if request.client else "unknown"
        
        # Record start time
        start_time = time.time()

        try:
            # Call next middleware/handler
            response = await call_next(request)
            
            # Record end time and calculate duration
            duration_ms = (time.time() - start_time) * 1000
            status_code = response.status_code

            # Log request/response details
            log_level = "INFO"
            if status_code >= 500:
                log_level = "ERROR"
            elif status_code >= 400:
                log_level = "WARNING"

            self.logger.log(
                getattr(logging, log_level),
                f"HTTP {method} {path} | Status {status_code} | "
                f"Client {client_host} | Duration {duration_ms:.2f}ms | "
                f"Query: {query_params if query_params else 'none'}"
            )

            # Add processing time header
            response.headers["X-Process-Time"] = str(duration_ms)

            return response

        except Exception as exc:
            # Handle exceptions in middleware
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.error(
                f"HTTP {method} {path} | Exception | "
                f"Client {client_host} | Duration {duration_ms:.2f}ms | "
                f"Error: {type(exc).__name__}: {str(exc)}"
            )

            # Re-raise to be handled by global exception handler
            raise


class SQLiteErrorHandler:
    """Handles SQLite-specific errors with context-aware responses"""

    @staticmethod
    def handle_database_lock(exc: sqlite3.OperationalError, request_path: str) -> tuple[Dict[str, Any], int]:
        """Handle database lock/timeout errors"""
        logger.warning(f"Database lock detected on {request_path}: {str(exc)}")
        
        return ErrorResponse.build(
            code=ErrorCode.TIMEOUT.value,
            message="Database is temporarily locked. Please retry your request.",
            status_code=503
        )

    @staticmethod
    def handle_database_error(exc: sqlite3.DatabaseError, request_path: str) -> tuple[Dict[str, Any], int]:
        """Handle general database errors"""
        logger.error(f"Database error on {request_path}: {str(exc)}")
        
        return ErrorResponse.build(
            code=ErrorCode.DATABASE_ERROR.value,
            message="A database error occurred. Please contact support if the issue persists.",
            status_code=500
        )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all custom exception handlers with FastAPI application
    
    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors from Pydantic"""
        logger.warning(f"Validation error on {request.url.path}: {exc}")
        
        response_body, status_code = ErrorResponse.validation_error(exc.errors())
        return JSONResponse(status_code=status_code, content=response_body)

    @app.exception_handler(sqlite3.OperationalError)
    async def sqlite_operational_error_handler(request: Request, exc: sqlite3.OperationalError):
        """Handle SQLite operational errors (lock, timeout, etc.)"""
        error_str = str(exc).lower()
        
        if "locked" in error_str or "timeout" in error_str:
            response_body, status_code = SQLiteErrorHandler.handle_database_lock(exc, request.url.path)
        else:
            response_body, status_code = SQLiteErrorHandler.handle_database_error(exc, request.url.path)
        
        return JSONResponse(status_code=status_code, content=response_body)

    @app.exception_handler(sqlite3.DatabaseError)
    async def sqlite_database_error_handler(request: Request, exc: sqlite3.DatabaseError):
        """Handle SQLite database errors"""
        logger.error(f"SQLite database error on {request.url.path}: {exc}")
        
        response_body, status_code = SQLiteErrorHandler.handle_database_error(exc, request.url.path)
        return JSONResponse(status_code=status_code, content=response_body)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle value errors"""
        logger.warning(f"Value error on {request.url.path}: {exc}")
        
        response_body, status_code = ErrorResponse.from_exception(exc)
        return JSONResponse(status_code=status_code, content=response_body)

    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError):
        """Handle key errors (missing resource)"""
        logger.warning(f"Key error on {request.url.path}: {exc}")
        
        response_body, status_code = ErrorResponse.from_exception(exc)
        return JSONResponse(status_code=status_code, content=response_body)

    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError):
        """Handle permission errors"""
        logger.warning(f"Permission error on {request.url.path}: {exc}")
        
        response_body, status_code = ErrorResponse.from_exception(exc)
        return JSONResponse(status_code=status_code, content=response_body)

    @app.exception_handler(TimeoutError)
    async def timeout_error_handler(request: Request, exc: TimeoutError):
        """Handle timeout errors"""
        logger.warning(f"Timeout on {request.url.path}: {exc}")
        
        response_body, status_code = ErrorResponse.from_exception(exc)
        return JSONResponse(status_code=status_code, content=response_body)

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other unhandled exceptions"""
        logger.error(
            f"Unhandled exception on {request.url.path}: {type(exc).__name__}: {exc}",
            exc_info=True
        )
        
        response_body, status_code = ErrorResponse.from_exception(exc)
        return JSONResponse(status_code=status_code, content=response_body)


def setup_middleware(app: FastAPI) -> None:
    """
    Setup all middleware for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    # Add request logging middleware
    # Note: Middleware is applied in reverse order (last added is executed first)
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("Middleware setup completed")


# Export for registration
__all__ = [
    "RequestLoggingMiddleware",
    "ErrorResponse",
    "ErrorCode",
    "SQLiteErrorHandler",
    "register_exception_handlers",
    "setup_middleware"
]
