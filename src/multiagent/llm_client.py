import time

from openai import APIStatusError, OpenAI


class LLMClient:
    def __init__(self, api_key, model, base_url, max_retries=3, retry_backoff=2):
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
                if error.status_code < 500:
                    raise
                time.sleep(self.retry_backoff * (attempt + 1))
        raise last_error
