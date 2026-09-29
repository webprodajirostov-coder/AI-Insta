import json
import tempfile
import unittest
from pathlib import Path

from src.job_pipeline import (
    _get_single_ready_audio_asset,
    run_audio_stage,
)


class AudioLifecycleTests(unittest.TestCase):
    def _write_job_and_scenario(self, job_dir):
        (job_dir / "content").mkdir(parents=True, exist_ok=True)
        (job_dir / "media" / "audio").mkdir(parents=True, exist_ok=True)

        job = {
            "job_id": "job_audio_test",
            "account_id": "account_001",
            "status": "created",
            "production": {"profile": "simple"},
        }
        scenario = {
            "production_profile": "simple",
            "language": "en",
            "duration_seconds": 8,
        }

        (job_dir / "job.json").write_text(
            json.dumps(job),
            encoding="utf-8",
        )
        (job_dir / "content" / "scenario.json").write_text(
            json.dumps(scenario),
            encoding="utf-8",
        )

    def _write_ready_asset(self, job_dir, asset_id, asset_type):
        audio_dir = job_dir / "media" / "audio"
        audio_path = audio_dir / f"{asset_id}.mp3"
        audio_path.write_bytes(b"test audio")

        asset = {
            "schema_version": 1,
            "entity": "AudioAsset",
            "asset_id": asset_id,
            "job_id": "job_audio_test",
            "type": asset_type,
            "status": "ready",
            "source": {
                "provider": "test",
                "text": None,
                "voice": None,
            },
            "path": str(audio_path.resolve()),
            "metadata": {
                "language": "en",
            },
        }

        (audio_dir / f"{asset_id}.json").write_text(
            json.dumps(asset),
            encoding="utf-8",
        )

    def test_ready_tts_does_not_satisfy_music_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_job_and_scenario(job_dir)
            self._write_ready_asset(job_dir, "tts_001", "tts")

            result = run_audio_stage(job_dir)

            self.assertEqual(result, "completed")
            self.assertTrue(
                (job_dir / "media" / "audio" / "music_001.mp3").is_file()
            )

            music_asset = json.loads(
                (
                    job_dir / "media" / "audio" / "music_001.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(music_asset["type"], "music")
            self.assertEqual(music_asset["status"], "ready")

    def test_multiple_ready_assets_of_same_type_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_job_and_scenario(job_dir)
            self._write_ready_asset(job_dir, "music_001", "music")
            self._write_ready_asset(job_dir, "music_002", "music")

            with self.assertRaisesRegex(
                ValueError,
                "Multiple ready AudioAssets found for type=music",
            ):
                _get_single_ready_audio_asset(job_dir, "music")


if __name__ == "__main__":
    unittest.main()
