import re
import time

from openai import APIStatusError, OpenAI


class DailyQuotaExceededError(Exception):
    pass


class LLMClient:
    def __init__(self, api_key, model, base_url, max_retries=6, retry_backoff=2):
        self.model = model
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def complete(self, prompt, system=None, max_tokens=1500, temperature=0.0):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()
            except APIStatusError as error:
                last_error = error
                if error.status_code == 429 and self._is_daily_quota_error(error):
                    raise DailyQuotaExceededError(
                        "Daily request quota exhausted for this model/key. "
                        "Retrying will not help until the quota resets."
                    ) from error
                retryable = error.status_code >= 500 or error.status_code == 429
                if not retryable:
                    raise
                delay = self._retry_delay_seconds(error, attempt)
                time.sleep(delay)
        raise last_error

    def _is_daily_quota_error(self, error):
        return "PerDay" in str(error.body)

    def _retry_delay_seconds(self, error, attempt):
        match = re.search(
            r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", str(error.body)
        )
        if match:
            return float(match.group(1)) + 1
        return self.retry_backoff * (attempt + 1)
