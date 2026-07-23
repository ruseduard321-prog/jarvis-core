from __future__ import annotations

import httpx
import openai

from backend.core.openai_error_classification import classify_openai_error, sanitize_error_message
from backend.core.provider_exceptions import PermanentProviderError, TransientProviderError


def _make_response(status_code: int) -> httpx.Response:
    request = httpx.Request("POST", "https://api.openai.com/v1/x")
    return httpx.Response(status_code, request=request)


def test_sanitize_error_message_redacts_api_key():
    message = "Request failed with key sk-abcdefgh12345678"
    assert "sk-abcdefgh12345678" not in sanitize_error_message(message)
    assert "[REDACTED]" in sanitize_error_message(message)


def test_sanitize_error_message_redacts_bearer_token():
    message = "Authorization: Bearer abc123.def456-ghi"
    sanitized = sanitize_error_message(message)
    assert "Bearer abc123.def456-ghi" not in sanitized
    assert "[REDACTED]" in sanitized


def test_sanitize_error_message_leaves_normal_text_untouched():
    message = "The model did not return any data"
    assert sanitize_error_message(message) == message


def test_classify_rate_limit_error_as_transient():
    exc = openai.RateLimitError("rate limited", response=_make_response(429), body=None)
    assert isinstance(classify_openai_error(exc), TransientProviderError)


def test_classify_bad_request_error_as_permanent():
    exc = openai.BadRequestError("bad request", response=_make_response(400), body=None)
    assert isinstance(classify_openai_error(exc), PermanentProviderError)


def test_classify_internal_server_error_as_transient():
    exc = openai.InternalServerError("server error", response=_make_response(500), body=None)
    assert isinstance(classify_openai_error(exc), TransientProviderError)


def test_classify_unknown_exception_as_permanent():
    exc = ValueError("unexpected")
    assert isinstance(classify_openai_error(exc), PermanentProviderError)


def test_classify_error_message_is_sanitized():
    exc = openai.BadRequestError("failed using sk-abcdefgh12345678", response=_make_response(400), body=None)
    classified = classify_openai_error(exc)
    assert "sk-abcdefgh12345678" not in str(classified)
