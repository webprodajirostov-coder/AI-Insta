import json
import tempfile
import unittest
from pathlib import Path

from src.update_job_stage import update_stage


class UpdateJobStageTests(unittest.TestCase):
    def _write_job(self, job_dir, *, visual="pending"):
        job = {
            "job_id": "job_stage_001",
            "account_id": "account_001",
            "status": "created",
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
            "error": None,
        }
        (job_dir / "job.json").write_text(
            json.dumps(job),
            encoding="utf-8",
        )

    def _read_job(self, job_dir):
        return json.loads(
            (job_dir / "job.json").read_text(encoding="utf-8")
        )

    def test_visual_waiting_can_resume_to_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_job(job_dir)

            update_stage(job_dir, "visual", "waiting")
            update_stage(job_dir, "visual", "completed")

            job = self._read_job(job_dir)
            self.assertEqual(job["pipeline"]["visual"], "completed")

    def test_rejects_transition_from_completed_back_to_waiting(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_job(job_dir, visual="completed")

            with self.assertRaisesRegex(
                ValueError,
                "Invalid pipeline transition for visual",
            ):
                update_stage(job_dir, "visual", "waiting")

    def test_output_completion_is_reserved_for_finalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_job(job_dir)

            with self.assertRaisesRegex(
                ValueError,
                "Output completion is reserved for final job completion",
            ):
                update_stage(job_dir, "output", "completed")

            job = self._read_job(job_dir)
            self.assertEqual(job["pipeline"]["output"], "pending")


if __name__ == "__main__":
    unittest.main()
