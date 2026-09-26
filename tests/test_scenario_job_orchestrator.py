import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.scenario_generator import ScenarioGenerationResult
from src.scenario_job_orchestrator import ScenarioJobOrchestrator


ROOT = Path(__file__).resolve().parents[1]


class StubScenarioGenerator:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class ScenarioJobOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.account_dir = ROOT / "data" / "accounts" / "sales_psychology_001"
        self.idea_path = ROOT / "data" / "ideas" / "content_idea_001.json"
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
            "created_at": "2026-09-26T00:00:00",
            "updated_at": "2026-09-26T00:00:00",
        }

    def test_generates_scenario_file_before_creating_job(self):
        generator = StubScenarioGenerator(
            ScenarioGenerationResult((self.scenario,))
        )
        job_creator = Mock(return_value=Path("data/jobs/test_job"))
        orchestrator = ScenarioJobOrchestrator(
            generator,
            job_creator=job_creator,
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scenario.json"

            job_dir = orchestrator.generate_scenario_and_create_job(
                content_idea_path=self.idea_path,
                content_concept_path=self.concept_path,
                production_profile_path=self.profile_path,
                scenario_output_path=output,
            )

            self.assertEqual(job_dir, Path("data/jobs/test_job"))
            self.assertEqual(len(generator.calls), 1)
            self.assertTrue(output.is_file())
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                self.scenario,
            )

            job_creator.assert_called_once_with(
                content_idea_path=self.idea_path,
                content_concept_path=self.concept_path,
                scenario_path=output,
                production_profile_path=self.profile_path,
                jobs_root="data/jobs",
                accounts_root="data/accounts",
            )

    def test_full_content_concept_to_scenario_to_job_e2e(self):
        generator = StubScenarioGenerator(
            ScenarioGenerationResult(({
                **self.scenario,
                "scenes": [{
                    "scene_id": "scene_001",
                    "order": 1,
                    "duration_seconds": 8,
                    "voiceover_text": "",
                    "visual": {
                        "type": "image",
                        "generation_required": True,
                        "prompt_en": "Minimal cinematic business portrait.",
                    },
                    "text_overlay": None,
                    "subtitles": None,
                }],
            },))
        )
        orchestrator = ScenarioJobOrchestrator(generator)

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            scenario_output = tmp / "scenarios" / "scenario.json"
            jobs_root = tmp / "jobs"

            job_dir = orchestrator.generate_scenario_and_create_job(
                content_idea_path=self.idea_path,
                content_concept_path=self.concept_path,
                production_profile_path=self.profile_path,
                scenario_output_path=scenario_output,
                jobs_root=jobs_root,
            )

            self.assertTrue(job_dir.is_dir())
            self.assertTrue((job_dir / "job.json").is_file())
            self.assertTrue((job_dir / "content" / "scenario.json").is_file())
            self.assertFalse(
                scenario_output.with_suffix(
                    scenario_output.suffix + ".bundle"
                ).exists()
            )

            job = json.loads(
                (job_dir / "job.json").read_text(encoding="utf-8")
            )
            persisted_scenario = json.loads(
                (job_dir / "content" / "scenario.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(job["status"], "created")
            self.assertEqual(job["account_id"], "sales_psychology_001")
            self.assertEqual(
                job["content"],
                {
                    "concept_id": "concept_001",
                    "scenario_id": "scenario_001",
                },
            )
            self.assertEqual(job["production"]["profile"], "simple")
            self.assertEqual(
                persisted_scenario["schema_version"],
                2,
            )
            self.assertEqual(
                persisted_scenario["concept_id"],
                "concept_001",
            )
            self.assertEqual(
                persisted_scenario["account_id"],
                "sales_psychology_001",
            )
            self.assertEqual(
                persisted_scenario["production_profile"],
                "simple",
            )
            self.assertEqual(
                persisted_scenario["scenes"][0]["visual"][
                    "generation_required"
                ],
                True,
            )

    def test_does_not_create_job_for_multiple_scenarios(self):
        generator = StubScenarioGenerator(
            ScenarioGenerationResult((self.scenario, self.scenario))
        )
        job_creator = Mock()
        orchestrator = ScenarioJobOrchestrator(
            generator,
            job_creator=job_creator,
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scenario.json"

            with self.assertRaises(ValueError):
                orchestrator.generate_scenario_and_create_job(
                    content_idea_path=self.idea_path,
                    content_concept_path=self.concept_path,
                    production_profile_path=self.profile_path,
                    scenario_output_path=output,
                )

            self.assertFalse(output.exists())
            job_creator.assert_not_called()

    def test_generation_failure_does_not_create_job(self):
        class FailingGenerator:
            def generate(self, **kwargs):
                raise RuntimeError("generation failed")

        job_creator = Mock()
        orchestrator = ScenarioJobOrchestrator(
            FailingGenerator(),
            job_creator=job_creator,
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scenario.json"

            with self.assertRaisesRegex(RuntimeError, "generation failed"):
                orchestrator.generate_scenario_and_create_job(
                    content_idea_path=self.idea_path,
                    content_concept_path=self.concept_path,
                    production_profile_path=self.profile_path,
                    scenario_output_path=output,
                )

            self.assertFalse(output.exists())
            job_creator.assert_not_called()


if __name__ == "__main__":
    unittest.main()
