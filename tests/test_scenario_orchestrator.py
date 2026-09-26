import json
import tempfile
import unittest
from pathlib import Path

from src.scenario_generator import ScenarioGenerationResult, ScenarioGenerator
from src.scenario_orchestrator import ScenarioOrchestrator


ROOT = Path(__file__).resolve().parents[1]


class StubScenarioGenerator:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class ScenarioOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.account_path = (
            ROOT / "data" / "accounts" / "sales_psychology_001" / "account.json"
        )
        self.concept_path = ROOT / "data" / "ideas" / "content_concept_001.json"
        self.profile_path = ROOT / "data" / "production_profiles" / "simple.json"

        self.scenario = {
            "schema_version": 2,
            "entity": "Scenario",
            "scenario_id": "scenario_001",
            "account_id": "sales_psychology_001",
            "concept_id": "concept_001",
            "production_profile": "simple",
            "status": "ready",
            "language": "en",
            "title": "Test scenario",
            "hook": "Test hook",
            "caption": "Test caption",
            "duration_seconds": 8,
            "scenes": [],
            "assembly": {
                "transitions": False,
                "animation": "minimal",
            },
        }

    def _orchestrator(self, scenarios=None):
        if scenarios is None:
            scenarios = [self.scenario]
        generator = StubScenarioGenerator(
            ScenarioGenerationResult(tuple(scenarios))
        )
        return ScenarioOrchestrator(generator), generator

    def test_loads_inputs_calls_generator_and_persists_result(self):
        orchestrator, generator = self._orchestrator()

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scenarios.json"

            result = orchestrator.generate(
                content_concept_path=self.concept_path,
                production_profile_path=self.profile_path,
                output_path=output,
            )

            self.assertEqual(result, output)
            self.assertEqual(len(generator.calls), 1)
            self.assertEqual(
                generator.calls[0]["account"]["account_id"],
                "sales_psychology_001",
            )
            self.assertEqual(
                generator.calls[0]["concept"]["concept_id"],
                "concept_001",
            )
            self.assertEqual(
                generator.calls[0]["production_profile"]["profile_id"],
                "simple",
            )
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                {"scenarios": [self.scenario]},
            )

    def test_supports_multiple_generated_scenarios(self):
        second = dict(self.scenario, scenario_id="scenario_002")
        orchestrator, _ = self._orchestrator([self.scenario, second])

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scenarios.json"

            orchestrator.generate(
                content_concept_path=self.concept_path,
                production_profile_path=self.profile_path,
                output_path=output,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                [item["scenario_id"] for item in payload["scenarios"]],
                ["scenario_001", "scenario_002"],
            )

    def test_rejects_cross_account_concept_before_provider_call(self):
        broken = dict(
            json.loads(self.concept_path.read_text(encoding="utf-8")),
            account_id="other_account",
        )

        provider = StubScenarioGenerator([self.scenario])
        generator = ScenarioGenerator(provider)
        orchestrator = ScenarioOrchestrator(generator)

        with tempfile.TemporaryDirectory() as tmp:
            accounts_root = Path(tmp) / "accounts"
            account_dir = accounts_root / "other_account"
            account_dir.mkdir(parents=True)
            (account_dir / "account.json").write_text(
                self.account_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            concept_path = Path(tmp) / "concept.json"
            output = Path(tmp) / "scenarios.json"
            concept_path.write_text(
                json.dumps(broken),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                orchestrator.generate(
                    content_concept_path=concept_path,
                    production_profile_path=self.profile_path,
                    output_path=output,
                    accounts_root=accounts_root,
                )

            self.assertEqual(provider.calls, [])

    def test_requires_at_least_one_generated_scenario(self):
        orchestrator, generator = self._orchestrator([])

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scenarios.json"

            with self.assertRaises(ValueError):
                orchestrator.generate(
                    content_concept_path=self.concept_path,
                    production_profile_path=self.profile_path,
                    output_path=output,
                )

            self.assertFalse(output.exists())
            self.assertEqual(len(generator.calls), 1)

    def test_generation_failure_does_not_write_output(self):
        class FailingGenerator:
            def generate(self, **kwargs):
                raise RuntimeError("generation failed")

        orchestrator = ScenarioOrchestrator(FailingGenerator())

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scenarios.json"

            with self.assertRaisesRegex(RuntimeError, "generation failed"):
                orchestrator.generate(
                    content_concept_path=self.concept_path,
                    production_profile_path=self.profile_path,
                    output_path=output,
                )

            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
