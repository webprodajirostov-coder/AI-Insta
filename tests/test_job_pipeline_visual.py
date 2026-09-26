import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from src.job_pipeline import resolve_visual_stage
from src.visual_generator import generate_visual
from src.visual_poller import poll_visual


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


    def make_generation_job(self):
        job_dir = self.make_job(generation_required=True)
        job = {
            "job_id": "job_test",
            "account_id": "account_test",
            "status": "created",
            "pipeline": {stage: "pending" for stage in (
                "research", "analysis", "concept", "scenario",
                "audio", "visual", "assembly", "output",
            )},
        }
        with open(job_dir / "job.json", "w", encoding="utf-8") as f:
            json.dump(job, f)
        return job_dir

    def test_generation_creates_generating_asset_with_provider_job(self):
        job_dir = self.make_generation_job()

        class FakeProvider:
            MODEL = "kling-v3-image"
            def submit(self, **kwargs):
                return {
                    "request_id": "task_test",
                    "status_url": "https://example.test/status",
                    "response_url": "https://example.test/result",
                }

        with patch("src.visual_generator.ODIRouterImageProvider", return_value=FakeProvider()):
            asset_path = generate_visual(job_dir, provider="odirouter")

        with open(asset_path, "r", encoding="utf-8") as f:
            asset = json.load(f)

        self.assertEqual(asset["status"], "generating")
        self.assertEqual(asset["asset_id"], "visual_001")
        self.assertEqual(asset["provider_job"]["request_id"], "task_test")
        self.assertEqual(asset["provider_job"]["model"], "kling-v3-image")

    def test_poll_completed_generation_downloads_and_marks_ready(self):
        job_dir = self.make_generation_job()
        asset = {
            "entity": "VisualAsset",
            "asset_id": "visual_001",
            "status": "generating",
            "provider_job": {
                "status_url": "https://example.test/status",
                "response_url": "https://example.test/result",
            },
        }
        asset_path = job_dir / "media" / "visual" / "visual_001.json"
        with open(asset_path, "w", encoding="utf-8") as f:
            json.dump(asset, f)

        class FakeProvider:
            def get_status(self, status_url):
                return {"status": "completed"}
            def get_result(self, response_url):
                return {"output": [{"content": [{
                    "type": "image",
                    "url": "https://example.test/image.png",
                    "jobId": "provider_job_test",
                }]}]}
            def download_file(self, image_url, output_path):
                Path(output_path).write_bytes(b"fake-image")

        with patch("src.visual_poller.ODIRouterImageProvider", return_value=FakeProvider()):
            result = poll_visual(job_dir, asset_id="visual_001")

        self.assertTrue(result)
        with open(asset_path, "r", encoding="utf-8") as f:
            updated = json.load(f)
        self.assertEqual(updated["status"], "ready")
        self.assertTrue(Path(updated["path"]).is_file())
        self.assertTrue(updated["metadata"]["completed"])

    def test_poll_processing_generation_stays_generating(self):
        job_dir = self.make_generation_job()
        asset = {
            "entity": "VisualAsset",
            "asset_id": "visual_001",
            "status": "generating",
            "provider_job": {
                "status_url": "https://example.test/status",
                "response_url": "https://example.test/result",
            },
        }
        asset_path = job_dir / "media" / "visual" / "visual_001.json"
        with open(asset_path, "w", encoding="utf-8") as f:
            json.dump(asset, f)

        class FakeProvider:
            def get_status(self, status_url):
                return {"status": "processing"}

        with patch("src.visual_poller.ODIRouterImageProvider", return_value=FakeProvider()):
            result = poll_visual(job_dir, asset_id="visual_001")

        self.assertFalse(result)
        with open(asset_path, "r", encoding="utf-8") as f:
            updated = json.load(f)
        self.assertEqual(updated["status"], "generating")

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
