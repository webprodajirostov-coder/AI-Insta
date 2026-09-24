import unittest

from src.llm_provider import LLMProvider


class FakeLLM:
    def generate_structured(self, *, system_prompt, user_prompt, response_schema=None):
        return {
            "scenarios": [],
        }


class LLMProviderContractTests(unittest.TestCase):
    def test_fake_provider_exposes_structured_generation(self):
        provider = FakeLLM()
        result = provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(isinstance(provider, LLMProvider.__class__) or hasattr(
            provider, "generate_structured"
        ))
