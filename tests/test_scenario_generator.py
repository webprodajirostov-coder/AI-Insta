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

    def _valid(self, **overrides):
        scenario = {
            "schema_version": 2,
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
                        "generation_required": True,
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
        scenario.update(overrides)
        return scenario

    def test_generates_valid_scenario_from_concept(self):
        result = ScenarioGenerator(
            StubScenarioProvider([self._valid()])
        ).generate(
            account=self.account,
            concept=self.concept,
            production_profile=self.profile,
        )

        scenario = result.scenarios[0]
        self.assertEqual(scenario["schema_version"], 2)
        self.assertEqual(scenario["account_id"], "sales_psychology_001")
        self.assertEqual(scenario["concept_id"], "concept_001")
        self.assertEqual(scenario["production_profile"], "simple")
        self.assertEqual(scenario["scenario_id"], "scenario_001")
        self.assertEqual(len(scenario["scenes"]), 1)

    def test_rejects_provider_missing_schema_version(self):
        scenario = self._valid()
        del scenario["schema_version"]

        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(StubScenarioProvider([scenario])).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

    def test_rejects_provider_v1_schema(self):
        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(
                StubScenarioProvider([self._valid(schema_version=1)])
            ).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

    def test_rejects_provider_disabled_visual_generation(self):
        scenario = self._valid(
            scenes=[{
                **self._valid()["scenes"][0],
                "visual": {
                    "type": "image",
                    "generation_required": False,
                    "prompt_en": "Cinematic vertical portrait.",
                },
            }]
        )

        with self.assertRaisesRegex(
            DomainValidationError,
            "generation_required=true",
        ):
            ScenarioGenerator(StubScenarioProvider([scenario])).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

    def test_rejects_provider_v1_fields(self):
        scenario = self._valid(
            visual={"type": "image"},
            audio={"tts": False, "music": True},
            subtitles=None,
        )

        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(StubScenarioProvider([scenario])).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

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
            [{"production_profile": "advanced", **self._valid()}]
        )

        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(provider).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

    def test_rejects_incomplete_scenario(self):
        provider = StubScenarioProvider(
            [{
                "schema_version": 2,
                "title": "Test",
                "hook": "Test hook",
                "production_profile": "simple",
            }]
        )

        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(provider).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

    def test_rejects_duration_outside_profile(self):
        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(
                StubScenarioProvider([self._valid(duration_seconds=11)])
            ).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

    def test_rejects_unsupported_visual_type(self):
        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(
                StubScenarioProvider([
                    self._valid(
                        scenes=[{
                            **self._valid()["scenes"][0],
                            "visual": {
                                "type": "ai_video",
                                "generation_required": True,
                                "prompt_en": "test",
                            },
                        }]
                    )
                ])
            ).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

    def test_rejects_subtitles_when_profile_disables_them(self):
        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(
                StubScenarioProvider([
                    self._valid(
                        scenes=[{
                            **self._valid()["scenes"][0],
                            "subtitles": {"text": "Not allowed"},
                        }]
                    )
                ])
            ).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )

    def test_rejects_editing_mismatch(self):
        with self.assertRaises(DomainValidationError):
            ScenarioGenerator(
                StubScenarioProvider([
                    self._valid(
                        assembly={
                            "transitions": True,
                            "animation": "dynamic",
                        }
                    )
                ])
            ).generate(
                account=self.account,
                concept=self.concept,
                production_profile=self.profile,
            )


if __name__ == "__main__":
    unittest.main()

