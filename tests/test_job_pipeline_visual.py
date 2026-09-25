import json
import tempfile
import unittest
from pathlib import Path

from src.job_pipeline import resolve_visual_stage


class VisualGenerationLifecycleTests(unittest.TestCase):
    def make_job(self, generation_required):
        job_dir = Path(tempfile.mkdtemp())
        (job_dir / "content").mkdir()
        (job_dir / "media" / "visual").mkdir(parents=True)

        scenario = {
            "schema_version": 2,
            "entity": "Scenario",
            "scenario_id": "scenario_test",
            "production_profile": "simple",
            "duration_seconds": 8,
            "scenes": [
                {
                    "scene_id": "scene_001",
                    "order": 1,
                    "duration_seconds": 8,
                    "voiceover_text": "",
                    "visual": {
                        "type": "image",
                        "generation_required": generation_required,
                        "prompt_en": "test prompt",
                    },
                    "text_overlay": None,
                    "subtitles": None,
                }
            ],
        }

        with open(
            job_dir / "content" / "scenario.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(scenario, f)

        return job_dir

    def test_generation_disabled_without_asset_fails(self):
        job_dir = self.make_job(generation_required=False)

        action, asset_id = resolve_visual_stage(job_dir)

        self.assertEqual(action, "failed")
        self.assertIsNone(asset_id)

    def test_generation_required_without_asset_generates(self):
        job_dir = self.make_job(generation_required=True)

        action, asset_id = resolve_visual_stage(job_dir)

        self.assertEqual(action, "generate")
        self.assertIsNone(asset_id)

    def test_ready_asset_wins_over_generation_requirement(self):
        job_dir = self.make_job(generation_required=False)

        asset = {
            "entity": "VisualAsset",
            "asset_id": "visual_001",
            "job_id": "job_test",
            "status": "ready",
            "path": str(job_dir / "media" / "visual" / "visual_001.png"),
        }

        job = {
            "job_id": "job_test",
            "account_id": "account_test",
            "status": "created",
            "pipeline": {
                "research": "pending",
                "analysis": "pending",
                "concept": "pending",
                "scenario": "pending",
                "audio": "pending",
                "visual": "pending",
                "assembly": "pending",
                "output": "pending",
            },
        }

        with open(job_dir / "job.json", "w", encoding="utf-8") as f:
            json.dump(job, f)

        asset_path = Path(asset["path"])
        asset_path.touch()

        with open(
            job_dir / "media" / "visual" / "visual_001.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(asset, f)

        action, asset_id = resolve_visual_stage(job_dir)

        self.assertEqual(action, "ready")
        self.assertEqual(asset_id, "visual_001")


if __name__ == "__main__":
    unittest.main()
