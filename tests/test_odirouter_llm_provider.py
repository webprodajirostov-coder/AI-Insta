import json
import unittest

from src.odirouter_llm_provider import ODIRouterLLMProvider


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


class ODIRouterLLMProviderTests(unittest.TestCase):
    def test_provider_sends_openai_compatible_request_and_parses_json(self):
        calls = []

        def fake_post(url, **kwargs):
            calls.append((url, kwargs))
            return FakeResponse(
                payload={
                    "choices": [
                        {
                            "message": {
                                "content": '{"scenarios": [{"title": "Test"}]}'
                            }
                        }
                    ]
                }
            )

        provider = ODIRouterLLMProvider(
            api_key="test-key",
            model="test-model",
            timeout=12,
            post=fake_post,
        )

        result = provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
            response_schema={"type": "object"},
        )

        self.assertEqual(result, {"scenarios": [{"title": "Test"}]})
        self.assertEqual(len(calls), 1)

        url, kwargs = calls[0]
        self.assertEqual(
            url,
            "https://api.odirouter.ai/v1/chat/completions",
        )
        self.assertEqual(
            kwargs["headers"]["Authorization"],
            "Bearer test-key",
        )
        self.assertEqual(kwargs["json"]["model"], "test-model")
        self.assertEqual(kwargs["timeout"], 12)
        self.assertIn("RESPONSE SCHEMA", kwargs["json"]["messages"][1]["content"])

    def test_provider_parses_markdown_json_fence(self):
        def fake_post(url, **kwargs):
            return FakeResponse(
                payload={
                    "choices": [
                        {
                            "message": {
                                "content": "```json\\n{\"status\":\"ok\",\"provider\":\"odirouter\"}\\n```",
                            }
                        }
                    ]
                }
            )

        provider = ODIRouterLLMProvider(api_key="test-key", post=fake_post)

        result = provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )

        self.assertEqual(
            result,
            {"status": "ok", "provider": "odirouter"},
        )

    def test_provider_rejects_missing_api_key(self):
        with self.assertRaises(ValueError):
            ODIRouterLLMProvider(api_key="")

    def test_provider_rejects_non_200_response(self):
        def fake_post(url, **kwargs):
            return FakeResponse(status_code=429, text="rate limited")

        provider = ODIRouterLLMProvider(api_key="test-key", post=fake_post)

        with self.assertRaisesRegex(RuntimeError, "HTTP 429"):
            provider.generate_structured(
                system_prompt="system",
                user_prompt="user",
            )

    def test_provider_rejects_malformed_completion(self):
        def fake_post(url, **kwargs):
            return FakeResponse(payload={"choices": []})

        provider = ODIRouterLLMProvider(api_key="test-key", post=fake_post)

        with self.assertRaises(RuntimeError):
            provider.generate_structured(
                system_prompt="system",
                user_prompt="user",
            )

    def test_provider_rejects_invalid_json_content(self):
        def fake_post(url, **kwargs):
            return FakeResponse(
                payload={
                    "choices": [
                        {
                            "message": {
                                "content": "not json",
                            }
                        }
                    ]
                }
            )

        provider = ODIRouterLLMProvider(api_key="test-key", post=fake_post)

        with self.assertRaises(RuntimeError):
            provider.generate_structured(
                system_prompt="system",
                user_prompt="user",
            )


if __name__ == "__main__":
    unittest.main()
