from backend.auth.auth_middleware import AuthenticationMiddleware
from backend.auth.supabase_auth import SupabaseAuthClient
from backend.core.config_validation import startup_validate_settings
from backend.core.dependencies import get_database
from backend.core.logging import configure_logging
from backend.core.middleware.metrics_middleware import MetricsMiddleware
from backend.core.middleware.rate_limit_middleware import RateLimitMiddleware
from backend.core.middleware.request_id_middleware import RequestIDMiddleware
from backend.core.middleware.security_headers_middleware import SecurityHeadersMiddleware
from backend.core.middleware.trusted_host_middleware import TrustedHostMiddleware
from backend.core.middleware.compression_middleware import CompressionMiddleware
from backend.core.domain_exceptions import DomainException
from backend.core.exceptions import (
    domain_exception_handler,
    http_exception_handler,
    server_exception_handler,
    validation_exception_handler,
)
from backend.core.lifespan import lifespan
from backend.core.rate_limit import InMemoryRateLimitStore
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1.router import router as api_router
from backend.core.config import settings

configure_logging()
startup_validate_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CompressionMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    store=InMemoryRateLimitStore(),
    default_limit=(100, 60),
    endpoint_limits={
        "/api/v1/auth/sign-in": (20, 60),
        "/api/v1/auth/me": (60, 60),
    },
)
app.add_middleware(AuthenticationMiddleware, auth_client=SupabaseAuthClient(get_database()))
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, server_exception_handler)
app.include_router(api_router, prefix="/api/v1")
