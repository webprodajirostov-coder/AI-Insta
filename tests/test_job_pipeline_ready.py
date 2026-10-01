import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.job_pipeline import run_ready_pipeline


class ReadyPipelineCompatibilityTests(unittest.TestCase):
    def test_ready_pipeline_delegates_to_canonical_orchestrator(self):
        job_dir = Path(tempfile.mkdtemp())
        orchestrator = unittest.mock.Mock()
        orchestrator.run.return_value = True

        with patch(
            "src.pipeline_orchestrator.PipelineOrchestrator",
            return_value=orchestrator,
        ) as orchestrator_cls:
            result = run_ready_pipeline(job_dir)

        self.assertTrue(result)
        orchestrator_cls.assert_called_once_with(job_dir)
        orchestrator.run.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
