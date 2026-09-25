import httpx
import pytest
from openai import APIStatusError

from multiagent.llm_client import LLMClient


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


def test_complete_returns_stripped_content(monkeypatch):
    client = LLMClient(api_key="key", model="test-model", base_url="https://example.com")
    monkeypatch.setattr(
        client._client.chat.completions,
        "create",
        lambda **kwargs: FakeCompletion("  hello world  "),
    )

    result = client.complete("hi")

    assert result == "hello world"


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


def test_complete_does_not_retry_on_client_error(monkeypatch):
    client = LLMClient(api_key="key", model="test-model", base_url="https://example.com")
    calls = {"count": 0}

    def failing_create(**kwargs):
        calls["count"] += 1
        raise make_status_error(429)

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
