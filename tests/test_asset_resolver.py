import json
import tempfile
import unittest
from pathlib import Path

from src.asset_resolver import resolve_visual_asset_for_scene


class VisualAssetResolutionTests(unittest.TestCase):
    def make_job(self, *, assets=None):
        root = Path(tempfile.mkdtemp())
        job_dir = root / "job"
        visual_dir = job_dir / "media" / "visual"
        visual_dir.mkdir(parents=True)

        (job_dir / "job.json").write_text(
            json.dumps({"job_id": "job_001"}),
            encoding="utf-8",
        )

        for index, asset in enumerate(assets or [], start=1):
            asset_id = asset.get("asset_id", f"visual_{index:03d}")
            asset = {
                "entity": "VisualAsset",
                "asset_id": asset_id,
                "job_id": asset.get("job_id", "job_001"),
                "type": asset.get("type", "image"),
                "status": asset.get("status", "ready"),
                "path": asset.get("path"),
            }
            if asset["path"] == "AUTO":
                path = visual_dir / f"{asset_id}.png"
                path.write_bytes(b"visual")
                asset["path"] = str(path.resolve())

            (visual_dir / f"{asset_id}.json").write_text(
                json.dumps(asset),
                encoding="utf-8",
            )

        return job_dir

    @staticmethod
    def scene(asset_type="image"):
        return {
            "scene_id": "scene_001",
            "visual": {
                "type": asset_type,
                "generation_required": True,
                "prompt_en": "test",
            },
        }

    def test_resolves_single_ready_matching_asset(self):
        job_dir = self.make_job(assets=[{"asset_id": "visual_001", "path": "AUTO"}])

        resolved = resolve_visual_asset_for_scene(job_dir, self.scene())

        self.assertEqual(resolved["asset_id"], "visual_001")
        self.assertTrue(Path(resolved["asset_path"]).is_file())

    def test_rejects_when_no_ready_asset_exists(self):
        job_dir = self.make_job(
            assets=[{"asset_id": "visual_001", "status": "pending", "path": None}]
        )

        with self.assertRaisesRegex(FileNotFoundError, "No ready VisualAsset"):
            resolve_visual_asset_for_scene(job_dir, self.scene())

    def test_rejects_wrong_asset_type(self):
        job_dir = self.make_job(
            assets=[{"asset_id": "visual_001", "type": "video", "path": "AUTO"}]
        )

        with self.assertRaisesRegex(FileNotFoundError, "No ready VisualAsset"):
            resolve_visual_asset_for_scene(job_dir, self.scene("image"))

    def test_rejects_multiple_ready_assets_as_ambiguous(self):
        job_dir = self.make_job(
            assets=[
                {"asset_id": "visual_001", "path": "AUTO"},
                {"asset_id": "visual_002", "path": "AUTO"},
            ]
        )

        with self.assertRaisesRegex(ValueError, "Ambiguous VisualAsset resolution"):
            resolve_visual_asset_for_scene(job_dir, self.scene())

    def test_rejects_asset_from_another_job(self):
        job_dir = self.make_job(
            assets=[
                {
                    "asset_id": "visual_001",
                    "job_id": "job_other",
                    "path": "AUTO",
                }
            ]
        )

        with self.assertRaisesRegex(FileNotFoundError, "No ready VisualAsset"):
            resolve_visual_asset_for_scene(job_dir, self.scene())

    def test_rejects_ready_asset_without_asset_id(self):
        job_dir = self.make_job(assets=[{"asset_id": "", "path": "AUTO"}])

        with self.assertRaisesRegex(FileNotFoundError, "No ready VisualAsset"):
            resolve_visual_asset_for_scene(job_dir, self.scene())

    def test_rejects_missing_physical_file(self):
        job_dir = self.make_job(
            assets=[{"asset_id": "visual_001", "path": "missing.png"}]
        )

        with self.assertRaisesRegex(FileNotFoundError, "Visual file does not exist"):
            resolve_visual_asset_for_scene(job_dir, self.scene())

    def test_rejects_path_outside_job(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            outside = Path(temp_dir) / "outside.png"
            outside.write_bytes(b"outside")

            job_dir = self.make_job(
                assets=[{"asset_id": "visual_001", "path": str(outside)}]
            )

            with self.assertRaisesRegex(
                ValueError,
                "Visual asset path escapes job directory",
            ):
                resolve_visual_asset_for_scene(job_dir, self.scene())


if __name__ == "__main__":
    unittest.main()
