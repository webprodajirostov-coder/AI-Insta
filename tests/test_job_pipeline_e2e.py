import base64
import json
import tempfile
import unittest
from pathlib import Path

from src.job_pipeline import run_pipeline
from src.job_service import create_job


ONE_BY_ONE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "YAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


class JobPipelineE2ETests(unittest.TestCase):
    def test_created_job_runs_to_completed_without_external_visual_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            scenario_path = tmp / "scenario.json"
            jobs_root = tmp / "jobs"

            scenario = {
                "schema_version": 2,
                "entity": "Scenario",
                "scenario_id": "scenario_pipeline_e2e",
                "account_id": "sales_psychology_001",
                "concept_id": "concept_001",
                "production_profile": "simple",
                "status": "ready",
                "language": "en",
                "title": "Pipeline E2E",
                "hook": "Test hook",
                "caption": "Test caption",
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
                            "prompt_en": "Minimal cinematic test image.",
                        },
                        "text_overlay": None,
                        "subtitles": None,
                    }
                ],
                "assembly": {
                    "transitions": False,
                    "animation": "minimal",
                },
            }
            scenario_path.write_text(
                json.dumps(scenario),
                encoding="utf-8",
            )

            job_dir = create_job(
                content_idea_path="data/ideas/content_idea_001.json",
                content_concept_path="data/ideas/content_concept_001.json",
                scenario_path=scenario_path,
                production_profile_path="data/production_profiles/simple.json",
                jobs_root=jobs_root,
            )

            visual_dir = job_dir / "media" / "visual"
            visual_path = visual_dir / "visual_001.png"
            visual_path.write_bytes(ONE_BY_ONE_PNG)

            visual_asset = {
                "schema_version": 1,
                "entity": "VisualAsset",
                "asset_id": "visual_001",
                "job_id": json.loads(
                    (job_dir / "job.json").read_text(encoding="utf-8")
                )["job_id"],
                "type": "image",
                "status": "ready",
                "source": {
                    "provider": "local-test",
                    "prompt": "Minimal cinematic test image.",
                },
                "path": str(visual_path.resolve()),
                "metadata": {
                    "language": "en",
                },
                "provider_job": None,
            }
            (visual_dir / "visual_001.json").write_text(
                json.dumps(visual_asset),
                encoding="utf-8",
            )

            result = run_pipeline(job_dir)

            self.assertTrue(result)

            job = json.loads(
                (job_dir / "job.json").read_text(encoding="utf-8")
            )

            self.assertEqual(job["status"], "completed")
            self.assertEqual(
                job["pipeline"],
                {
                    "research": "skipped",
                    "analysis": "skipped",
                    "concept": "completed",
                    "scenario": "completed",
                    "audio": "completed",
                    "visual": "completed",
                    "assembly": "completed",
                    "output": "completed",
                },
            )

            self.assertTrue(
                (job_dir / "media" / "audio" / "music_001.mp3").is_file()
            )
            self.assertTrue(
                (job_dir / "assembly" / "assembly_plan.json").is_file()
            )
            self.assertTrue(
                (job_dir / "output" / "final.mp4").is_file()
            )
            self.assertEqual(
                Path(job["artifacts"]["output"]).resolve(),
                (job_dir / "output" / "final.mp4").resolve(),
            )

            # Terminal idempotency: a completed Job is validated and skipped.
            self.assertTrue(run_pipeline(job_dir))


if __name__ == "__main__":
    unittest.main()
