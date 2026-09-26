import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.job_pipeline import run_ready_pipeline


class ReadyPipelineAudioOrchestrationTests(unittest.TestCase):
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
            "scenes": [],
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
                stage: "pending"
                for stage in (
                    "research",
                    "analysis",
                    "concept",
                    "scenario",
                    "audio",
                    "visual",
                    "assembly",
                    "output",
                )
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

    def test_ready_pipeline_delegates_audio_to_audio_stage(self):
        job_dir = self.make_job()

        with patch(
            "src.job_pipeline.run_audio_stage",
            return_value="completed",
        ) as run_audio, patch(
            "src.job_pipeline.run_visual_stage",
            return_value="completed",
        ), patch(
            "src.assembly.build_assembly_plan",
        ), patch(
            "src.assembly_runner.run_assembly",
        ), patch(
            "src.finalizer.finalize",
            return_value=True,
        ):
            result = run_ready_pipeline(job_dir)

        self.assertTrue(result)
        run_audio.assert_called_once_with(job_dir)

        job = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
        self.assertEqual(job["pipeline"]["audio"], "completed")


if __name__ == "__main__":
    unittest.main()
