import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.pipeline_orchestrator import PipelineOrchestrator


class PipelineOrchestratorFailedTests(unittest.TestCase):
    def _write_failed_job(self, job_dir):
        job = {
            "job_id": "job_failed_001",
            "account_id": "account_001",
            "status": "failed",
            "pipeline": {
                "research": "skipped",
                "analysis": "skipped",
                "concept": "completed",
                "scenario": "completed",
                "audio": "completed",
                "visual": "failed",
                "assembly": "pending",
                "output": "pending",
            },
            "artifacts": {"output": None},
            "error": "Visual stage failed",
        }
        (job_dir / "job.json").write_text(
            json.dumps(job),
            encoding="utf-8",
        )

    def test_failed_job_is_terminal_for_normal_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_failed_job(job_dir)

            with patch(
                "src.pipeline_orchestrator.materialize_preproduction_stages"
            ) as materialize, patch.object(
                PipelineOrchestrator,
                "_run_audio",
            ) as run_audio, patch.object(
                PipelineOrchestrator,
                "_run_visual",
            ) as run_visual, patch.object(
                PipelineOrchestrator,
                "_run_assembly",
            ) as run_assembly, patch.object(
                PipelineOrchestrator,
                "_run_output",
            ) as run_output:
                result = PipelineOrchestrator(job_dir).run()

            job = json.loads(
                (job_dir / "job.json").read_text(encoding="utf-8")
            )

            self.assertFalse(result)
            self.assertEqual(job["status"], "failed")
            self.assertEqual(job["error"], "Visual stage failed")
            materialize.assert_not_called()
            run_audio.assert_not_called()
            run_visual.assert_not_called()
            run_assembly.assert_not_called()
            run_output.assert_not_called()


if __name__ == "__main__":
    unittest.main()
