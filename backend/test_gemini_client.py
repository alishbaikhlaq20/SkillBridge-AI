"""
Tests for the shared Gemini helper: retries, fallback rules and error
classification. Gemini itself is never called and no test really waits.

Run from the backend folder:  python -m pytest -v
"""

import httpx
import pytest
from google.genai import errors
from pydantic import BaseModel

from services import gemini_client as gc


class Answer(BaseModel):
    value: str = ""


OK = Answer(value="ok")
P, F = gc.PRIMARY_MODEL, gc.FALLBACK_MODEL


def server_error(code):
    return errors.ServerError(code, {"error": {"code": code, "message": "x", "status": "S"}})


def client_error(code):
    return errors.ClientError(code, {"error": {"code": code, "message": "x", "status": "S"}})


def run(monkeypatch, outcomes, **kwargs):
    """
    Run generate_structured with a scripted list of results, one per model call.
    Returns (result, error, models_called, seconds_slept).
    """
    calls, sleeps = [], []
    script = iter(outcomes)

    def fake_call(model, timeout_ms, prompt, schema):
        calls.append((model, timeout_ms))
        outcome = next(script)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(gc, "_call_model", fake_call)
    monkeypatch.setattr(gc.time, "sleep", lambda seconds: sleeps.append(seconds))

    try:
        result = gc.generate_structured("prompt", Answer, "test", **kwargs)
        return result, None, calls, sleeps
    except gc.GeminiServiceError as error:
        return None, error, calls, sleeps


# --------------------------------------------------------------------------
# Success
# --------------------------------------------------------------------------

def test_primary_success_makes_one_call_and_never_waits(monkeypatch):
    result, error, calls, sleeps = run(monkeypatch, [OK])
    assert result == OK
    assert [c[0] for c in calls] == [P]
    assert sleeps == []


# --------------------------------------------------------------------------
# Quick temporary failures: wait, then try the SAME model again
# --------------------------------------------------------------------------

@pytest.mark.parametrize("failure", [
    server_error(503),             # "high demand" - the real case from the logs
    server_error(500),
    client_error(429),
    httpx.ConnectError("refused"),
])
def test_quick_temporary_failure_is_retried_on_the_same_model(monkeypatch, failure):
    result, error, calls, sleeps = run(monkeypatch, [failure, OK])
    assert result == OK
    assert [c[0] for c in calls] == [P, P]
    assert sleeps == [gc.RETRY_DELAY_SECONDS]


def test_after_two_failed_tries_the_fallback_model_is_used(monkeypatch):
    result, error, calls, sleeps = run(
        monkeypatch, [server_error(503), server_error(503), OK]
    )
    assert result == OK
    assert [c[0] for c in calls] == [P, P, F]
    assert sleeps == [gc.RETRY_DELAY_SECONDS]          # waited only between the primary tries


def test_the_fallback_model_also_gets_a_second_try(monkeypatch):
    result, error, calls, sleeps = run(
        monkeypatch, [server_error(503), server_error(503), server_error(503), OK]
    )
    assert result == OK
    assert [c[0] for c in calls] == [P, P, F, F]
    assert sleeps == [gc.RETRY_DELAY_SECONDS, gc.RETRY_DELAY_SECONDS]


def test_both_models_down_gives_503_after_four_tries(monkeypatch):
    # exactly the situation in the log: "high demand" on both models
    result, error, calls, sleeps = run(monkeypatch, [server_error(503)] * 4)
    assert result is None
    assert error.status_code == 503
    assert [c[0] for c in calls] == [P, P, F, F]
    assert len(sleeps) == 2


def test_rate_limit_everywhere_gives_429(monkeypatch):
    _, error, calls, _ = run(monkeypatch, [client_error(429)] * 4)
    assert error.status_code == 429
    assert len(calls) == 4


# --------------------------------------------------------------------------
# Slow or unreadable failures: NO waiting, go straight to the fallback
# --------------------------------------------------------------------------

@pytest.mark.parametrize("failure", [
    server_error(504),
    httpx.ReadTimeout("t"),
    httpx.ConnectTimeout("t"),
    ValueError("bad json"),
])
def test_timeouts_and_bad_answers_skip_the_retry_and_use_the_fallback(monkeypatch, failure):
    result, error, calls, sleeps = run(monkeypatch, [failure, OK])
    assert result == OK
    assert [c[0] for c in calls] == [P, F]
    assert sleeps == []


def test_both_models_timing_out_gives_504_without_waiting(monkeypatch):
    _, error, calls, sleeps = run(
        monkeypatch, [httpx.ReadTimeout("t"), httpx.ConnectTimeout("t")]
    )
    assert error.status_code == 504
    assert [c[0] for c in calls] == [P, F]
    assert sleeps == []


# --------------------------------------------------------------------------
# Permanent errors: never retried, never sent to the fallback
# --------------------------------------------------------------------------

@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_permanent_errors_are_not_retried(monkeypatch, code):
    result, error, calls, sleeps = run(monkeypatch, [client_error(code)])
    assert result is None
    assert error.status_code == 500 and not error.retryable
    assert [c[0] for c in calls] == [P]
    assert sleeps == []


def test_permanent_error_on_the_fallback_stops_with_500(monkeypatch):
    _, error, calls, _ = run(
        monkeypatch, [server_error(503), server_error(503), client_error(404)]
    )
    assert error.status_code == 500
    assert [c[0] for c in calls] == [P, P, F]


# --------------------------------------------------------------------------
# Timeouts and classification
# --------------------------------------------------------------------------

def test_custom_timeouts_are_used_for_each_model(monkeypatch):
    _, _, calls, _ = run(
        monkeypatch, [server_error(504), OK],
        primary_timeout_ms=45_000, fallback_timeout_ms=60_000,
    )
    assert calls == [(P, 45_000), (F, 60_000)]


def test_a_retry_uses_the_same_timeout_as_the_first_try(monkeypatch):
    _, _, calls, _ = run(
        monkeypatch, [server_error(503), OK],
        primary_timeout_ms=45_000, fallback_timeout_ms=60_000,
    )
    assert calls == [(P, 45_000), (P, 45_000)]


def test_default_timeouts_are_used_when_none_are_given(monkeypatch):
    _, _, calls, _ = run(monkeypatch, [server_error(504), OK])
    assert calls == [(P, gc.PRIMARY_TIMEOUT_MS), (F, gc.FALLBACK_TIMEOUT_MS)]


def test_status_codes_for_each_error_type():
    assert gc.classify_error(server_error(504)).status_code == 504
    assert gc.classify_error(server_error(500)).status_code == 503
    assert gc.classify_error(server_error(503)).status_code == 503
    assert gc.classify_error(client_error(429)).status_code == 429
    assert gc.classify_error(httpx.ReadTimeout("t")).status_code == 504
    assert gc.classify_error(httpx.ConnectError("c")).status_code == 503
    assert gc.classify_error(ValueError("v")).status_code == 502
    assert gc.classify_error(RuntimeError("r")).status_code == 500


def test_only_quick_temporary_errors_are_marked_for_a_retry():
    transient = {
        "503": gc.classify_error(server_error(503)).transient,
        "500": gc.classify_error(server_error(500)).transient,
        "429": gc.classify_error(client_error(429)).transient,
        "connect": gc.classify_error(httpx.ConnectError("c")).transient,
        "504": gc.classify_error(server_error(504)).transient,
        "read timeout": gc.classify_error(httpx.ReadTimeout("t")).transient,
        "bad json": gc.classify_error(ValueError("v")).transient,
        "404": gc.classify_error(client_error(404)).transient,
        "unknown": gc.classify_error(RuntimeError("r")).transient,
    }
    assert transient == {
        "503": True, "500": True, "429": True, "connect": True,
        "504": False, "read timeout": False, "bad json": False,
        "404": False, "unknown": False,
    }


def test_missing_api_key_is_a_clear_server_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(gc.GeminiServiceError) as info:
        gc.get_gemini_client(1000)
    assert info.value.status_code == 500 and not info.value.retryable
