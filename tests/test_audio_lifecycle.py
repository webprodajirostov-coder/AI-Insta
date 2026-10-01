import json
import os
import tempfile
import unittest
from pathlib import Path

from src.job_pipeline import (
    _get_single_ready_audio_asset,
    run_audio_stage,
)
from src.production_profile_store import ProductionProfileStore
from src.audio_generator import generate_audio, generate_mock_music

ROOT = Path(__file__).resolve().parents[1]


class AudioLifecycleTests(unittest.TestCase):
    def _write_job_and_scenario(self, job_dir):
        (job_dir / "content").mkdir(parents=True, exist_ok=True)
        (job_dir / "media" / "audio").mkdir(parents=True, exist_ok=True)

        job = {
            "job_id": "job_audio_test",
            "account_id": "account_001",
            "status": "created",
            "production": {
                "profile": "simple",
                "profile_definition": ProductionProfileStore(
                    ROOT / "data" / "production_profiles"
                ).load("simple"),
            },
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


    def _write_mutated_global_profile(self, root, *, music_enabled):
        profile = ProductionProfileStore(
            ROOT / "data" / "production_profiles"
        ).load("simple")
        profile["audio"] = dict(profile["audio"])
        profile["audio"]["music"] = music_enabled

        profile_path = root / "data" / "production_profiles" / "simple.json"
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(
            json.dumps(profile),
            encoding="utf-8",
        )

    def test_mock_music_uses_job_snapshot_when_global_profile_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            job_dir = root / "job"
            self._write_job_and_scenario(job_dir)
            self._write_mutated_global_profile(root, music_enabled=False)

            previous_cwd = Path.cwd()
            os.chdir(root)
            try:
                result = generate_mock_music(job_dir)
            finally:
                os.chdir(previous_cwd)

            self.assertTrue(result.is_file())
            self.assertTrue(
                (job_dir / "media" / "audio" / "music_001.mp3").is_file()
            )

    def test_generate_audio_uses_job_snapshot_when_global_profile_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            job_dir = root / "job"
            self._write_job_and_scenario(job_dir)
            self._write_mutated_global_profile(root, music_enabled=False)

            previous_cwd = Path.cwd()
            os.chdir(root)
            try:
                result = generate_audio(job_dir, audio_type="music")
            finally:
                os.chdir(previous_cwd)

            self.assertTrue(result.is_file())
            asset = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(asset["type"], "music")
            self.assertEqual(asset["status"], "pending")

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
