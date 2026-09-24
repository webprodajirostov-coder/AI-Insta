import json
import unittest
from pathlib import Path

from src.domain_validation import DomainValidationError
from src.scenario_generator import ScenarioGenerator
from src.scenario_llm_provider import LLMScenarioProvider


ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class FakeLLM:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate_structured(self, *, system_prompt, user_prompt, response_schema=None):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": response_schema,
            }
        )
        return self.result


class ScenarioLLMProviderTests(unittest.TestCase):
    def setUp(self):
        account_dir = ROOT / "data" / "accounts" / "sales_psychology_001"
        self.account = load_json(account_dir / "account.json")
        self.concept = load_json(ROOT / "data" / "ideas" / "content_concept_001.json")
        self.profile = load_json(ROOT / "data" / "production_profiles" / "simple.json")

        self.valid = {
            "title": "The Hidden Reason You Undercharge",
            "hook": "You might not be undercharging because you're modest.",
            "caption": "Sometimes the lower price is about safety.",
            "duration_seconds": 8,
            "scenes": [
                {
                    "scene_id": "scene_001",
                    "order": 1,
                    "duration_seconds": 8,
                    "voiceover_text": "",
                    "visual": {
                        "type": "image",
                        "generation_required": False,
                        "prompt_en": "Cinematic vertical portrait.",
                    },
                    "text_overlay": {
                        "text": "The hidden reason",
                        "position": "center",
                        "animation": "minimal",
                    },
                    "subtitles": None,
                }
            ],
            "assembly": {
                "transitions": False,
                "animation": "minimal",
            },
        }

    def test_adapter_extracts_scenarios_from_wrapped_result(self):
        llm = FakeLLM({"scenarios": [self.valid]})
        provider = LLMScenarioProvider(llm)

        scenarios = provider.generate_scenarios(
            account=self.account,
            concept=self.concept,
            production_profile=self.profile,
        )

        self.assertEqual(scenarios, [self.valid])
        self.assertEqual(len(llm.calls), 1)
        self.assertIn("CONTENT CONCEPT", llm.calls[0]["user_prompt"])
        self.assertIn("PRODUCTION PROFILE", llm.calls[0]["user_prompt"])
        self.assertIn("Scenario v2", llm.calls[0]["system_prompt"])
        self.assertIn("Do not add a Scenario-level audio object", llm.calls[0]["system_prompt"])

    def test_adapter_passes_direct_sequence_result(self):
        provider = LLMScenarioProvider(FakeLLM([self.valid]))

        scenarios = provider.generate_scenarios(
            account=self.account,
            concept=self.concept,
            production_profile=self.profile,
        )

        self.assertEqual(scenarios, [self.valid])

    def test_adapter_can_feed_scenario_generator(self):
        provider = LLMScenarioProvider(FakeLLM([self.valid]))

        result = ScenarioGenerator(provider).generate(
            account=self.account,
            concept=self.concept,
            production_profile=self.profile,
        )

        self.assertEqual(len(result.scenarios), 1)
        self.assertEqual(result.scenarios[0]["scenario_id"], "scenario_001")
        self.assertEqual(result.scenarios[0]["schema_version"], 2)

    def test_adapter_rejects_invalid_llm_result(self):
        provider = LLMScenarioProvider(FakeLLM({"scenario": self.valid}))

        with self.assertRaises(DomainValidationError):
            provider.generate_scenarios(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )


if __name__ == "__main__":
    unittest.main()
