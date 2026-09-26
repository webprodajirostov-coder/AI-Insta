import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.job_pipeline import run_ready_pipeline


class VisualLifecycleTests(unittest.TestCase):
    def make_job(self):
        job_dir = Path(tempfile.mkdtemp())
        (job_dir / "content").mkdir()
        (job_dir / "media" / "audio").mkdir(parents=True)
        (job_dir / "media" / "visual").mkdir(parents=True)
        (job_dir / "assembly").mkdir()

        scenario = {
            "schema_version": 2,
            "entity": "Scenario",
            "scenario_id": "scenario_test",
            "account_id": "account_test",
            "concept_id": "concept_test",
            "production_profile": "simple",
            "status": "ready",
            "language": "en",
            "title": "Test",
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
                        "prompt_en": "Test visual prompt",
                    },
                    "text_overlay": {
                        "text": "Test overlay",
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

        job = {
            "job_id": "job_test",
            "account_id": "account_test",
            "status": "created",
            "pipeline": {
                "research": "pending",
                "analysis": "pending",
                "concept": "pending",
                "scenario": "pending",
                "audio": "completed",
                "visual": "pending",
                "assembly": "pending",
                "output": "pending",
            },
        }

        (job_dir / "content" / "scenario.json").write_text(
            json.dumps(scenario),
            encoding="utf-8",
        )
        (job_dir / "job.json").write_text(
            json.dumps(job),
            encoding="utf-8",
        )
        return job_dir

    @staticmethod
    def finalize_stub(job_dir):
        job_dir = Path(job_dir)
        output_dir = job_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / "final.mp4"
        output_path.write_bytes(b"final")

        plan = {
            "output": {
                "path": str(output_path.resolve()),
            }
        }
        (job_dir / "assembly" / "assembly_plan.json").write_text(
            json.dumps(plan),
            encoding="utf-8",
        )

        from src.job_pipeline import complete_job_after_output_validation

        complete_job_after_output_validation(job_dir)
        return True

    def test_generating_visual_is_polled_and_never_resubmitted(self):
        job_dir = self.make_job()

        class Provider:
            MODEL = "kling-v3-image"

            def __init__(self):
                self.submit_calls = 0
                self.status_calls = 0

            def submit(self, **kwargs):
                self.submit_calls += 1
                return {
                    "request_id": "request_001",
                    "status_url": "https://example.test/status",
                    "response_url": "https://example.test/result",
                }

            def get_status(self, status_url):
                self.status_calls += 1
                return {"status": "completed"}

            def get_result(self, response_url):
                return {
                    "output": [
                        {
                            "content": [
                                {
                                    "type": "image",
                                    "url": "https://example.test/image.png",
                                    "jobId": "request_001",
                                }
                            ]
                        }
                    ]
                }

            def download_file(self, file_url, output_path):
                Path(output_path).write_bytes(b"visual")

        provider = Provider()

        with patch(
            "src.visual_generator.ODIRouterImageProvider",
            return_value=provider,
        ), patch(
            "src.visual_poller.ODIRouterImageProvider",
            return_value=provider,
        ), patch(
            "src.assembly.build_assembly_plan",
        ), patch(
            "src.assembly_runner.run_assembly",
        ), patch(
            "src.finalizer.finalize",
            side_effect=self.finalize_stub,
        ), patch(
            "src.output_validator.validate_output",
        ):
            first = run_ready_pipeline(job_dir)
            self.assertFalse(first)

            job = json.loads(
                (job_dir / "job.json").read_text(encoding="utf-8")
            )
            self.assertEqual(job["status"], "waiting")
            self.assertEqual(job["pipeline"]["visual"], "waiting")

            asset = json.loads(
                (
                    job_dir / "media" / "visual" / "visual_001.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(asset["status"], "generating")
            self.assertEqual(
                asset["provider_job"]["request_id"],
                "request_001",
            )

            second = run_ready_pipeline(job_dir)
            self.assertTrue(second)

        self.assertEqual(provider.submit_calls, 1)
        self.assertEqual(provider.status_calls, 1)

        asset = json.loads(
            (job_dir / "media" / "visual" / "visual_001.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(asset["status"], "ready")
        self.assertTrue(Path(asset["path"]).is_file())

    def test_ready_visual_is_reused_without_provider_call(self):
        job_dir = self.make_job()

        visual_path = job_dir / "media" / "visual" / "visual_001.png"
        visual_path.write_bytes(b"existing")

        asset = {
            "schema_version": 1,
            "entity": "VisualAsset",
            "asset_id": "visual_001",
            "job_id": "job_test",
            "type": "image",
            "status": "ready",
            "source": {
                "provider": "odirouter",
                "prompt": "Existing",
            },
            "path": str(visual_path.resolve()),
            "provider_job": None,
        }
        (job_dir / "media" / "visual" / "visual_001.json").write_text(
            json.dumps(asset),
            encoding="utf-8",
        )

        with patch(
            "src.visual_generator.ODIRouterImageProvider",
        ) as provider, patch(
            "src.visual_poller.ODIRouterImageProvider",
        ) as poller, patch(
            "src.assembly.build_assembly_plan",
        ), patch(
            "src.assembly_runner.run_assembly",
        ), patch(
            "src.finalizer.finalize",
            side_effect=self.finalize_stub,
        ), patch(
            "src.output_validator.validate_output",
        ):
            result = run_ready_pipeline(job_dir)

        self.assertTrue(result)
        provider.assert_not_called()
        poller.assert_not_called()

        job = json.loads(
            (job_dir / "job.json").read_text(encoding="utf-8")
        )
        self.assertEqual(job["pipeline"]["visual"], "completed")
        self.assertEqual(job["pipeline"]["output"], "completed")
        self.assertEqual(job["status"], "completed")


if __name__ == "__main__":
    unittest.main()
