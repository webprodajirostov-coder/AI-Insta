import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.pipeline_orchestrator import PipelineOrchestrator


class PipelineOrchestratorResumeTests(unittest.TestCase):
    def _write_job(self, job_dir):
        job = {
            "job_id": "job_resume_001",
            "account_id": "account_001",
            "status": "created",
            "pipeline": {
                "research": "skipped",
                "analysis": "skipped",
                "concept": "completed",
                "scenario": "completed",
                "audio": "completed",
                "visual": "pending",
                "assembly": "pending",
                "output": "pending",
            },
            "artifacts": {"output": None},
            "error": None,
        }
        (job_dir / "job.json").write_text(
            json.dumps(job),
            encoding="utf-8",
        )

    def test_waiting_job_resumes_after_visual_asset_becomes_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_job(job_dir)

            assembly_calls = []
            output_calls = []

            def finish_assembly():
                job_path = job_dir / "job.json"
                job = json.loads(job_path.read_text(encoding="utf-8"))
                job["pipeline"]["assembly"] = "completed"
                assembly_calls.append(True)
                job_path.write_text(
                    json.dumps(job),
                    encoding="utf-8",
                )

            def finish_output():
                job_path = job_dir / "job.json"
                job = json.loads(job_path.read_text(encoding="utf-8"))
                job["pipeline"]["output"] = "completed"
                job["status"] = "completed"
                job["artifacts"]["output"] = str(
                    job_dir / "output" / "final.mp4"
                )
                output_calls.append(True)
                job_path.write_text(
                    json.dumps(job),
                    encoding="utf-8",
                )
                return True

            with patch(
                "src.pipeline_orchestrator.resolve_visual_stage",
                side_effect=[
                    ("generate", None),
                    ("ready", "visual_001"),
                ],
            ), patch(
                "src.pipeline_orchestrator.run_visual_stage",
                return_value="waiting",
            ), patch.object(
                PipelineOrchestrator,
                "_run_audio",
            ), patch.object(
                PipelineOrchestrator,
                "_run_assembly",
                side_effect=finish_assembly,
            ), patch.object(
                PipelineOrchestrator,
                "_run_output",
                side_effect=finish_output,
            ), patch(
                "src.pipeline_orchestrator.validate_completed_job",
            ):
                first_run = PipelineOrchestrator(job_dir).run()

                first_job = json.loads(
                    (job_dir / "job.json").read_text(encoding="utf-8")
                )
                self.assertFalse(first_run)
                self.assertEqual(first_job["status"], "waiting")
                self.assertEqual(first_job["pipeline"]["visual"], "waiting")
                self.assertEqual(first_job["pipeline"]["assembly"], "pending")
                self.assertEqual(first_job["pipeline"]["output"], "pending")
                self.assertEqual(assembly_calls, [])
                self.assertEqual(output_calls, [])

                second_run = PipelineOrchestrator(job_dir).run()

                second_job = json.loads(
                    (job_dir / "job.json").read_text(encoding="utf-8")
                )
                self.assertTrue(second_run)
                self.assertEqual(second_job["status"], "completed")
                self.assertEqual(second_job["pipeline"]["visual"], "completed")
                self.assertEqual(second_job["pipeline"]["assembly"], "completed")
                self.assertEqual(second_job["pipeline"]["output"], "completed")
                self.assertEqual(assembly_calls, [True])
                self.assertEqual(output_calls, [True])


if __name__ == "__main__":
    unittest.main()
