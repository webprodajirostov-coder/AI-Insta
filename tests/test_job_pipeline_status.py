import json
import tempfile
import unittest
from pathlib import Path

from src.job_pipeline import update_job_state


class JobPipelineStatusTests(unittest.TestCase):
    def _write_failed_job(self, job_dir, *, visual="failed"):
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
                "visual": visual,
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

    def test_failed_job_cannot_transition_back_to_waiting(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_failed_job(job_dir, visual="waiting")

            with self.assertRaisesRegex(
                ValueError,
                "Invalid job status transition: failed -> waiting",
            ):
                update_job_state(job_dir, status="waiting")

            job = json.loads(
                (job_dir / "job.json").read_text(encoding="utf-8")
            )
            self.assertEqual(job["status"], "failed")
            self.assertEqual(job["pipeline"]["visual"], "waiting")


if __name__ == "__main__":
    unittest.main()
