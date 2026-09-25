class FakeLLMClient:
    def __init__(self, responses=None, default_response="fake response"):
        self.responses = list(responses or [])
        self.default_response = default_response
        self.calls = []

    def complete(self, prompt, system=None, max_tokens=1500, temperature=0.0):
        self.calls.append({"prompt": prompt, "system": system})
        if self.responses:
            return self.responses.pop(0)
        return self.default_response


class RaisingLLMClient:
    def complete(self, *args, **kwargs):
        raise RuntimeError("simulated LLM failure")
