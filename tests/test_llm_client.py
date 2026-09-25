import httpx
import pytest
from openai import APIStatusError

from multiagent.llm_client import DailyQuotaExceededError, LLMClient


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeCompletion:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


def make_status_error(status_code):
    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(status_code, request=request, json={"error": "boom"})
    return APIStatusError("boom", response=response, body={"error": "boom"})


def make_daily_quota_error():
    request = httpx.Request("POST", "https://example.com")
    body = {
        "error": {
            "code": 429,
            "message": "daily quota exceeded",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                    "violations": [
                        {
                            "quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
                        }
                    ],
                }
            ],
        }
    }
    response = httpx.Response(429, request=request, json=body)
    return APIStatusError("daily quota exceeded", response=response, body=body)


def make_rate_limit_error(retry_delay_seconds):
    request = httpx.Request("POST", "https://example.com")
    body = {
        "error": {
            "code": 429,
            "message": "rate limited",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.RetryInfo",
                    "retryDelay": f"{retry_delay_seconds}s",
                }
            ],
        }
    }
    response = httpx.Response(429, request=request, json=body)
    return APIStatusError("rate limited", response=response, body=body)


def test_complete_returns_stripped_content(monkeypatch):
    client = LLMClient(api_key="key", model="test-model", base_url="https://example.com")
    monkeypatch.setattr(
        client._client.chat.completions,
        "create",
        lambda **kwargs: FakeCompletion("  hello world  "),
    )

    result = client.complete("hi")

    assert result == "hello world"


def test_complete_fails_fast_on_daily_quota_without_retrying(monkeypatch):
    client = LLMClient(api_key="key", model="test-model", base_url="https://example.com")
    calls = {"count": 0}

    def failing_create(**kwargs):
        calls["count"] += 1
        raise make_daily_quota_error()

    monkeypatch.setattr(client._client.chat.completions, "create", failing_create)

    with pytest.raises(DailyQuotaExceededError):
        client.complete("hi")

    assert calls["count"] == 1


def test_complete_retries_on_server_error_then_succeeds(monkeypatch):
    client = LLMClient(
        api_key="key", model="test-model", base_url="https://example.com", retry_backoff=0
    )
    calls = {"count": 0}

    def flaky_create(**kwargs):
        calls["count"] += 1
        if calls["count"] < 2:
            raise make_status_error(503)
        return FakeCompletion("recovered")

    monkeypatch.setattr(client._client.chat.completions, "create", flaky_create)

    result = client.complete("hi")

    assert result == "recovered"
    assert calls["count"] == 2


def test_complete_retries_on_rate_limit_using_retry_delay_hint(monkeypatch):
    client = LLMClient(api_key="key", model="test-model", base_url="https://example.com")
    calls = {"count": 0}
    sleeps = []

    def flaky_create(**kwargs):
        calls["count"] += 1
        if calls["count"] < 2:
            raise make_rate_limit_error(retry_delay_seconds=3)
        return FakeCompletion("recovered")

    monkeypatch.setattr(client._client.chat.completions, "create", flaky_create)
    monkeypatch.setattr("multiagent.llm_client.time.sleep", lambda s: sleeps.append(s))

    result = client.complete("hi")

    assert result == "recovered"
    assert calls["count"] == 2
    assert sleeps == [4.0]


def test_complete_does_not_retry_on_bad_request(monkeypatch):
    client = LLMClient(api_key="key", model="test-model", base_url="https://example.com")
    calls = {"count": 0}

    def failing_create(**kwargs):
        calls["count"] += 1
        raise make_status_error(400)

    monkeypatch.setattr(client._client.chat.completions, "create", failing_create)

    with pytest.raises(APIStatusError):
        client.complete("hi")

    assert calls["count"] == 1


def test_complete_passes_system_message(monkeypatch):
    client = LLMClient(api_key="key", model="test-model", base_url="https://example.com")
    captured = {}

    def capturing_create(**kwargs):
        captured.update(kwargs)
        return FakeCompletion("ok")

    monkeypatch.setattr(client._client.chat.completions, "create", capturing_create)

    client.complete("question", system="be helpful")

    assert captured["messages"][0] == {"role": "system", "content": "be helpful"}
    assert captured["messages"][1] == {"role": "user", "content": "question"}


def test_complete_logs_structured_error_on_daily_quota_failure(monkeypatch, caplog):
    client = LLMClient(api_key="key", model="test-model", base_url="https://example.com")

    def failing_create(**kwargs):
        raise make_daily_quota_error()

    monkeypatch.setattr(client._client.chat.completions, "create", failing_create)

    with caplog.at_level("ERROR", logger="multiagent.llm_client"):
        with pytest.raises(DailyQuotaExceededError):
            client.complete("hi")

    error_records = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(error_records) == 1
    assert error_records[0].fields["error_type"] == "DailyQuotaExceededError"
    assert error_records[0].fields["model"] == "test-model"
