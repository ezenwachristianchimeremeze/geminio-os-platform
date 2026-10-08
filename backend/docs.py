"""
CHIXUS OpenAPI Schema & API Documentation Customization
Provides standardized API documentation, security scheme definitions, and route organization
Environment: Termux on ARM64 Android
Master Passkey: CHIXUS-ADMIN-@)@^
"""

import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIMetadata:
    """API metadata and configuration"""
    
    TITLE = "CHIXUS Edge & Team Verification Platform API"
    VERSION = "1.0.0"
    DESCRIPTION = """
Production-grade edge synchronization, cryptographic verification ledger, and role-based access control backend.

## Features

- **Edge Synchronization**: Offline queuing and batch synchronization with central backend
- **Cryptographic Verification**: SHA-256 ledger for immutable transaction verification
- **Role-Based Access Control**: Token-based authentication with granular permissions
- **Rate Limiting**: Anti-abuse protection with sliding window limiters per endpoint
- **Request Logging**: Comprehensive request/response logging with processing metrics
- **Standardized Errors**: Unified JSON error responses across all endpoints

## Authentication

All authenticated endpoints require one of the following headers:

- `x-access-token`: Standard access token for general operations
- `x-admin-passkey`: Master admin passkey for privileged operations (use with caution)

## Rate Limits

- **Standard Endpoints**: 60 requests/minute per IP or token
- **Authentication Endpoints**: 10 requests/minute per IP or token
- **Admin Endpoints**: 1000 requests/minute per IP or token
- **Anonymous Endpoints**: 20 requests/minute per IP

## Response Format

All responses follow a standardized format:

### Success Response
```json
{
  "data": {},
  "message": "Operation successful",
  "timestamp": "2026-10-08T23:30:00.000Z"
}
```

### Error Response
```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human-readable error description",
  "timestamp": "2026-10-08T23:30:00.000Z"
}
```

## Environment

- **Framework**: FastAPI with async/await support
- **Database**: SQLite with offline sync queue
- **Deployment**: Termux on ARM64 Android
- **Security**: SHA-256 hashing, token-based auth, rate limiting
"""
    
    TAGS_METADATA = [
        {
            "name": "Authentication & Tokens",
            "description": "Token management, verification, and authentication endpoints",
            "externalDocs": {
                "description": "Learn more about authentication",
                "url": "https://github.com/ezenwachristianchimeremeze/geminio-os-platform#authentication",
            },
        },
        {
            "name": "Edge Synchronization",
            "description": "Local edge sync engine for offline queuing and batch synchronization",
            "externalDocs": {
                "description": "Learn more about edge sync",
                "url": "https://github.com/ezenwachristianchimeremeze/geminio-os-platform#edge-synchronization",
            },
        },
        {
            "name": "Node Health & Telemetry",
            "description": "Node health checks, metrics collection, and cluster telemetry",
            "externalDocs": {
                "description": "Learn more about monitoring",
                "url": "https://github.com/ezenwachristianchimeremeze/geminio-os-platform#monitoring",
            },
        },
        {
            "name": "Verification Ledger",
            "description": "Cryptographic verification ledger for immutable transaction history",
            "externalDocs": {
                "description": "Learn more about the ledger",
                "url": "https://github.com/ezenwachristianchimeremeze/geminio-os-platform#verification-ledger",
            },
        },
    ]


class SecuritySchemes:
    """OpenAPI security scheme definitions"""
    
    SCHEMES: Dict[str, Any] = {
        "AccessToken": {
            "type": "apiKey",
            "in": "header",
            "name": "x-access-token",
            "description": "Standard access token for general API operations. Grants permissions based on token scope.",
        },
        "AdminPasskey": {
            "type": "apiKey",
            "in": "header",
            "name": "x-admin-passkey",
            "description": "Master admin passkey for privileged operations. Use with extreme caution in production.",
        },
        "BearerToken": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Optional JWT bearer token for advanced authentication scenarios.",
        },
    }
    
    # Security requirements for different endpoint categories
    SECURITY_REQUIREMENTS = {
        "public": [],  # No security required
        "standard": [{"AccessToken": []}],  # Requires access token
        "admin": [{"AdminPasskey": []}],  # Requires admin passkey
        "either": [{"AccessToken": []}, {"AdminPasskey": []}],  # Either token works
    }


def customize_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate customized OpenAPI schema for the FastAPI application
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Custom OpenAPI schema dictionary
    """
    
    if app.openapi_schema:
        return app.openapi_schema
    
    # Generate base OpenAPI schema
    openapi_schema = get_openapi(
        title=APIMetadata.TITLE,
        version=APIMetadata.VERSION,
        description=APIMetadata.DESCRIPTION,
        routes=app.routes,
        tags=APIMetadata.TAGS_METADATA,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = SecuritySchemes.SCHEMES
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Local development server (Termux on Android)",
            "variables": {
                "protocol": {
                    "enum": ["http", "https"],
                    "default": "http",
                },
            },
        },
        {
            "url": "http://0.0.0.0:8000",
            "description": "All interfaces (Termux deployment)",
        },
    ]
    
    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "CHIXUS Platform Documentation",
        "url": "https://github.com/ezenwachristianchimeremeze/geminio-os-platform",
    }
    
    # Add info contact
    openapi_schema["info"]["contact"] = {
        "name": "CHIXUS Platform Support",
        "url": "https://github.com/ezenwachristianchimeremeze/geminio-os-platform/issues",
        "email": "support@chixus.local",
    }
    
    # Add license information
    openapi_schema["info"]["license"] = {
        "name": "Proprietary",
        "url": "https://github.com/ezenwachristianchimeremeze/geminio-os-platform",
    }
    
    # Add response status codes documentation
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
    
    # Add error response schema
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "title": "Error Response",
        "description": "Standard error response format for all API errors",
        "properties": {
            "error": {
                "type": "boolean",
                "description": "Always true for error responses",
                "example": True,
            },
            "code": {
                "type": "string",
                "description": "Machine-readable error code",
                "enum": [
                    "INVALID_REQUEST",
                    "AUTHENTICATION_FAILED",
                    "AUTHORIZATION_FAILED",
                    "RESOURCE_NOT_FOUND",
                    "CONFLICT",
                    "DATABASE_ERROR",
                    "INTERNAL_ERROR",
                    "SERVICE_UNAVAILABLE",
                    "VALIDATION_ERROR",
                    "TIMEOUT",
                    "RATE_LIMIT_EXCEEDED",
                ],
                "example": "VALIDATION_ERROR",
            },
            "message": {
                "type": "string",
                "description": "Human-readable error message",
                "example": "Request validation failed",
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 timestamp when error occurred",
                "example": "2026-10-08T23:30:00.000Z",
            },
        },
        "required": ["error", "code", "message", "timestamp"],
    }
    
    # Add success response schema
    openapi_schema["components"]["schemas"]["SuccessResponse"] = {
        "type": "object",
        "title": "Success Response",
        "description": "Standard success response format for all API operations",
        "properties": {
            "data": {
                "description": "Response payload (structure depends on endpoint)",
            },
            "message": {
                "type": "string",
                "description": "Human-readable success message",
                "example": "Operation successful",
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 timestamp when operation completed",
                "example": "2026-10-08T23:30:00.000Z",
            },
        },
        "required": ["message", "timestamp"],
    }
    
    # Add rate limit response schema
    openapi_schema["components"]["schemas"]["RateLimitExceeded"] = {
        "type": "object",
        "title": "Rate Limit Exceeded",
        "description": "Response when rate limit is exceeded",
        "properties": {
            "error": {
                "type": "boolean",
                "example": True,
            },
            "code": {
                "type": "string",
                "example": "RATE_LIMIT_EXCEEDED",
            },
            "message": {
                "type": "string",
                "example": "Too many requests. Please try again later.",
            },
            "retry_after_seconds": {
                "type": "integer",
                "description": "Number of seconds to wait before retrying",
                "example": 45,
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "example": "2026-10-08T23:30:00.000Z",
            },
        },
        "required": ["error", "code", "message", "retry_after_seconds", "timestamp"],
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_api_documentation(app: FastAPI) -> None:
    """
    Setup comprehensive API documentation for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    
    # Customize OpenAPI schema
    app.openapi = lambda: customize_openapi_schema(app)
    
    # Configure Swagger UI with custom settings
    app.swagger_ui_init_oauth = {
        "clientId": "chixus-api-client",
        "appName": "CHIXUS Platform",
        "scopes": {
            "read:all": "Read all resources",
            "write:all": "Write all resources",
            "admin:all": "Full admin access",
        },
    }
    
    logger.info("API documentation setup completed")
    logger.info(f"OpenAPI schema available at /openapi.json")
    logger.info(f"Swagger UI available at /docs")
    logger.info(f"ReDoc available at /redoc")


def get_route_tags() -> Dict[str, str]:
    """
    Get a mapping of route paths to OpenAPI tags
    Useful for programmatic route organization
    
    Returns:
        Dictionary mapping route patterns to tag names
    """
    return {
        "auth": "Authentication & Tokens",
        "verify": "Authentication & Tokens",
        "token": "Authentication & Tokens",
        "sync": "Edge Synchronization",
        "queue": "Edge Synchronization",
        "batch": "Edge Synchronization",
        "health": "Node Health & Telemetry",
        "metrics": "Node Health & Telemetry",
        "telemetry": "Node Health & Telemetry",
        "heartbeat": "Node Health & Telemetry",
        "ledger": "Verification Ledger",
        "transaction": "Verification Ledger",
        "verify": "Verification Ledger",
    }


def create_endpoint_documentation(
    summary: str,
    description: str,
    tag: str,
    responses: Optional[Dict[int, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Helper to create standardized endpoint documentation
    
    Args:
        summary: Short endpoint summary
        description: Detailed endpoint description
        tag: OpenAPI tag name
        responses: Custom response documentation
        
    Returns:
        Dictionary suitable for FastAPI route decorators
    """
    
    default_responses = {
        400: {
            "model": "ErrorResponse",
            "description": "Bad request - validation error",
        },
        401: {
            "model": "ErrorResponse",
            "description": "Unauthorized - authentication failed",
        },
        403: {
            "model": "ErrorResponse",
            "description": "Forbidden - insufficient permissions",
        },
        404: {
            "model": "ErrorResponse",
            "description": "Not found - resource doesn't exist",
        },
        429: {
            "model": "RateLimitExceeded",
            "description": "Rate limit exceeded - too many requests",
        },
        500: {
            "model": "ErrorResponse",
            "description": "Internal server error",
        },
        503: {
            "model": "ErrorResponse",
            "description": "Service unavailable - database locked",
        },
    }
    
    if responses:
        default_responses.update(responses)
    
    return {
        "summary": summary,
        "description": description,
        "tags": [tag],
        "responses": default_responses,
    }


__all__ = [
    "APIMetadata",
    "SecuritySchemes",
    "customize_openapi_schema",
    "setup_api_documentation",
    "get_route_tags",
    "create_endpoint_documentation",
]
