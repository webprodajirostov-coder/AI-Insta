import json
import unittest
from pathlib import Path

from src.domain_validation import DomainValidationError
from src.scenario_generator import ScenarioGenerator


ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class StubScenarioProvider:
    def __init__(self, scenarios):
        self.scenarios = scenarios

    def generate_scenarios(self, **kwargs):
        return self.scenarios


class ScenarioGeneratorTests(unittest.TestCase):
    def setUp(self):
        account_dir = ROOT / "data" / "accounts" / "sales_psychology_001"
        self.account = load_json(account_dir / "account.json")
        self.concept = load_json(ROOT / "data" / "ideas" / "content_concept_001.json")
        self.profile = load_json(ROOT / "data" / "production_profiles" / "simple.json")

    def test_generates_valid_scenario_from_concept(self):
        provider = StubScenarioProvider(
            [{
                "title": "The Hidden Reason You Undercharge",
                "hook": "You might not be undercharging because you're modest.",
                "caption": "Sometimes the lower price is about safety.",
                "visual": {
                    "type": "image",
                    "generation_required": True,
                    "prompt_en": "Cinematic vertical portrait.",
                },
                "text_overlay": {
                    "text": "The hidden reason",
                    "position": "center",
                    "animation": "minimal",
                },
                "audio": {"tts": False, "music": True},
                "subtitles": {"enabled": False},
                "duration_seconds": 8,
                "assembly": {
                    "transitions": False,
                    "animation": "minimal",
                },
            }]
        )

        result = ScenarioGenerator(provider).generate(
            account=self.account,
            concept=self.concept,
            production_profile=self.profile,
        )

        scenario = result.scenarios[0]
        self.assertEqual(scenario["account_id"], "sales_psychology_001")
        self.assertEqual(scenario["concept_id"], "concept_001")
        self.assertEqual(scenario["production_profile"], "simple")
        self.assertEqual(scenario["scenario_id"], "scenario_001")

    def test_rejects_cross_account_concept(self):
        concept = dict(self.concept)
        concept["account_id"] = "other_account"

        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(StubScenarioProvider([])).generate(
                account=self.account,
                concept=concept,
                production_profile=self.profile,
            )

    def test_rejects_profile_mismatch(self):
        concept = dict(self.concept)
        concept["production_profile"] = "advanced"

        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(StubScenarioProvider([])).generate(
                account=self.account,
                concept=concept,
                production_profile=self.profile,
            )

    def test_rejects_provider_non_object(self):
        provider = StubScenarioProvider(["invalid"])

        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(provider).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

    def test_rejects_provider_profile_mismatch(self):
        provider = StubScenarioProvider(
            [{"production_profile": "advanced"}]
        )

        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(provider).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

    def test_defaults_identity_fields(self):
        provider = StubScenarioProvider(
            [{
                "title": "Test",
                "hook": "Test hook",
                "production_profile": "simple",
            }]
        )

        result = ScenarioGenerator(provider).generate(
            account=self.account,
            concept=self.concept,
            production_profile=self.profile,
        )

        scenario = result.scenarios[0]
        self.assertEqual(scenario["entity"], "Scenario")
        self.assertEqual(scenario["schema_version"], 1)
        self.assertEqual(scenario["status"], "draft")
        self.assertEqual(scenario["language"], "en")


if __name__ == "__main__":
    unittest.main()
