import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.core.domain_exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabaseUnavailableError,
    DomainException,
    RepositoryError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    status_code: int


from backend.core.request_context import get_request_id


def make_error_response(error_code: str, message: str, status_code: int) -> JSONResponse:
    payload = ErrorResponse(
        error_code=error_code,
        message=message,
        status_code=status_code,
    ).model_dump()
    request_id = get_request_id()
    if request_id is not None:
        payload["request_id"] = request_id
    return JSONResponse(status_code=status_code, content=payload)


def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    if isinstance(exc, DatabaseUnavailableError):
        return make_error_response(
            error_code="database_unavailable",
            message="Database unavailable",
            status_code=503,
        )
    if isinstance(exc, ResourceNotFoundError):
        return make_error_response(
            error_code="resource_not_found",
            message="Resource not found",
            status_code=404,
        )
    if isinstance(exc, AuthenticationError):
        return make_error_response(
            error_code="authentication_error",
            message=str(exc) or "Authentication required",
            status_code=401,
        )
    if isinstance(exc, AuthorizationError):
        return make_error_response(
            error_code="authorization_error",
            message=str(exc) or "Forbidden",
            status_code=403,
        )
    if isinstance(exc, RepositoryError):
        return make_error_response(
            error_code="repository_error",
            message="Internal server error",
            status_code=500,
        )

    return make_error_response(
        error_code="domain_error",
        message=str(exc) or "Domain error",
        status_code=400,
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return make_error_response(
        error_code="validation_error",
        message="Request validation failed",
        status_code=422,
    )


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return make_error_response(
        error_code="http_exception",
        message=str(exc.detail) if exc.detail else "HTTP error",
        status_code=exc.status_code,
    )


def server_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error: %s", exc)
    return make_error_response(
        error_code="internal_server_error",
        message="Internal server error",
        status_code=500,
    )
