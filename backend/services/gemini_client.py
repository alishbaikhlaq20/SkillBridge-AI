"""
Shared Gemini helper used by the job and resume AI services.

Responsibilities:
  * Create the Gemini client (API key comes from .env, never hardcoded).
  * Apply a request timeout so a slow model cannot hang the request.
  * Call the primary model, and fall back to a second model ONLY when the
    failure is temporary (server error, timeout, rate limit, bad JSON).
  * Fail immediately on permanent errors (bad request, bad key, unknown model),
    because retrying them can never succeed.
  * Log every attempt separately, including how long it took.
  * Convert every failure into a GeminiServiceError with a clear message and
    an HTTP status code that the API routes can return to the frontend.
"""

import logging
import os
import time
from typing import TypeVar

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration  (change models here - nowhere else)
# ---------------------------------------------------------------------------

PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-3.8-flash"

# Timeouts are in milliseconds. The fallback gets longer because it is the
# last chance, and it is a larger model.
PRIMARY_TIMEOUT_MS = 20_000
FALLBACK_TIMEOUT_MS = 30_000


SchemaT = TypeVar("SchemaT", bound=BaseModel)


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------

class GeminiServiceError(Exception):
    """
    A Gemini failure that has already been classified.

    message     - safe, readable text for the frontend
    status_code - HTTP status the API route should return
    retryable   - True if trying the fallback model could help
    """

    def __init__(
        self,
        message: str,
        status_code: int = 503,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.retryable = retryable


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def get_gemini_client(timeout_ms: int) -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise GeminiServiceError(
            "The AI service is not configured on the server.",
            status_code=500,
            retryable=False,
        )

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=timeout_ms),
    )


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

def classify_error(exc: Exception) -> GeminiServiceError:
    """Turn any exception from a Gemini call into a GeminiServiceError."""

    if isinstance(exc, GeminiServiceError):
        return exc

    # 5xx from Google. 504 means Google's deadline expired.
    if isinstance(exc, errors.ServerError):
        if exc.code == 504:
            return GeminiServiceError(
                "The AI service took too long to respond. Please try again.",
                status_code=504,
                retryable=True,
            )
        return GeminiServiceError(
            "The AI service is temporarily unavailable. Please try again.",
            status_code=503,
            retryable=True,
        )

    # 4xx from Google.
    if isinstance(exc, errors.ClientError):
        if exc.code == 429:
            return GeminiServiceError(
                "The AI service rate limit was reached. "
                "Please wait a minute and try again.",
                status_code=429,
                retryable=True,
            )
        # 400 / 401 / 403 / 404: our request, key or model name is wrong.
        # The user cannot fix this and a retry cannot succeed.
        return GeminiServiceError(
            f"The AI service rejected the request (error {exc.code}). "
            "This is a server configuration problem.",
            status_code=500,
            retryable=False,
        )

    # Our own client-side timeout (network too slow / no answer in time).
    if isinstance(exc, httpx.TimeoutException):
        return GeminiServiceError(
            "The AI service took too long to respond. Please try again.",
            status_code=504,
            retryable=True,
        )

    # Other network problems (DNS, connection refused, dropped connection).
    if isinstance(exc, httpx.TransportError):
        return GeminiServiceError(
            "Could not reach the AI service. Check the network and try again.",
            status_code=503,
            retryable=True,
        )

    # Empty or invalid JSON. pydantic's ValidationError is a ValueError.
    if isinstance(exc, ValueError):
        return GeminiServiceError(
            "The AI service returned a response that could not be read.",
            status_code=502,
            retryable=True,
        )

    return GeminiServiceError(
        "An unexpected error occurred while calling the AI service.",
        status_code=500,
        retryable=False,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def _call_model(
    model: str,
    timeout_ms: int,
    prompt: str,
    schema: type[SchemaT],
) -> SchemaT:
    client = get_gemini_client(timeout_ms)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response")

    return schema.model_validate_json(response.text)


def generate_structured(
    prompt: str,
    schema: type[SchemaT],
    task_name: str,
    primary_timeout_ms: int | None = None,
    fallback_timeout_ms: int | None = None,
) -> SchemaT:
    """
    Ask Gemini for structured output that matches `schema`.

    Tries the primary model first. Falls back to the second model only if the
    first failure was temporary. Raises GeminiServiceError if everything fails.

    Long outputs (such as a full learning plan) can pass larger timeouts than
    the defaults, which are tuned for short extraction tasks.
    """

    attempts = [
        ("primary", PRIMARY_MODEL, primary_timeout_ms or PRIMARY_TIMEOUT_MS),
        ("fallback", FALLBACK_MODEL, fallback_timeout_ms or FALLBACK_TIMEOUT_MS),
    ]

    last_error: GeminiServiceError | None = None

    for label, model, timeout_ms in attempts:
        started = time.time()

        try:
            result = _call_model(model, timeout_ms, prompt, schema)

            logger.info(
                "[%s] %s model %s succeeded in %.1fs",
                task_name, label, model, time.time() - started,
            )
            return result

        except Exception as exc:
            service_error = classify_error(exc)
            last_error = service_error

            # Log the REAL error (type + text) for debugging. The frontend
            # only receives the clean message, never the raw exception.
            logger.warning(
                "[%s] %s model %s failed after %.1fs: %s: %s "
                "(retryable=%s)",
                task_name, label, model, time.time() - started,
                type(exc).__name__, str(exc)[:300],
                service_error.retryable,
            )

            if not service_error.retryable:
                # Permanent error - the fallback model cannot fix it.
                raise service_error from exc

            if label == "primary":
                logger.warning(
                    "[%s] trying fallback model %s", task_name, FALLBACK_MODEL
                )

    # Both models failed with temporary errors.
    assert last_error is not None
    raise last_error
