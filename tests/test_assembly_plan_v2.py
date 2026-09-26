import json
import tempfile
import unittest
from pathlib import Path

from src.assembly import build_assembly_plan
from src.assembly_renderer import render_assembly


class AssemblyPlanV2Tests(unittest.TestCase):
    def _create_simple_job(self, root: Path):
        job_dir = root / "job"
        (job_dir / "content").mkdir(parents=True)
        (job_dir / "media" / "visual").mkdir(parents=True)
        (job_dir / "media" / "audio").mkdir(parents=True)

        job = {
            "job_id": "job_001",
            "account_id": "account_001",
        }
        scenario = {
            "schema_version": 2,
            "entity": "Scenario",
            "scenario_id": "scenario_001",
            "account_id": "account_001",
            "concept_id": "concept_001",
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
                        "prompt_en": "test",
                    },
                    "text_overlay": {
                        "text": "Test hook",
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

        (job_dir / "job.json").write_text(
            json.dumps(job, indent=2),
            encoding="utf-8",
        )
        (job_dir / "content" / "scenario.json").write_text(
            json.dumps(scenario, indent=2),
            encoding="utf-8",
        )

        visual_file = job_dir / "media" / "visual" / "visual_001.png"
        music_file = job_dir / "media" / "audio" / "music_001.mp3"
        visual_file.write_bytes(b"visual")
        music_file.write_bytes(b"music")

        visual_asset = {
            "entity": "VisualAsset",
            "asset_id": "visual_001",
            "job_id": "job_001",
            "type": "image",
            "status": "ready",
            "path": str(visual_file),
        }
        music_asset = {
            "entity": "AudioAsset",
            "asset_id": "music_001",
            "job_id": "job_001",
            "type": "music",
            "status": "ready",
            "path": str(music_file),
        }

        (job_dir / "media" / "visual" / "visual_001.json").write_text(
            json.dumps(visual_asset, indent=2),
            encoding="utf-8",
        )
        (job_dir / "media" / "audio" / "music_001.json").write_text(
            json.dumps(music_asset, indent=2),
            encoding="utf-8",
        )

        return job_dir

    def test_builds_scene_aware_assembly_plan(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = self._create_simple_job(Path(temp_dir))

            plan = build_assembly_plan(job_dir)

            self.assertEqual(plan["schema_version"], 2)
            self.assertEqual(plan["entity"], "AssemblyPlan")
            self.assertEqual(len(plan["scenes"]), 1)

            scene = plan["scenes"][0]
            self.assertEqual(scene["scene_id"], "scene_001")
            self.assertEqual(scene["order"], 1)
            self.assertEqual(scene["duration_seconds"], 8)
            self.assertEqual(
                scene["visual"]["asset_id"],
                "visual_001",
            )
            self.assertEqual(
                scene["visual"]["asset_path"],
                str(job_dir / "media" / "visual" / "visual_001.png"),
            )

            self.assertEqual(
                plan["inputs"]["audio"]["music"]["asset_path"],
                str(job_dir / "media" / "audio" / "music_001.mp3"),
            )
            self.assertNotIn("visual", plan["inputs"])

    def test_simple_renderer_rejects_visual_path_outside_job(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = self._create_simple_job(Path(temp_dir))
            plan = build_assembly_plan(job_dir)
            plan["scenes"][0]["visual"]["asset_path"] = str(
                Path(temp_dir).parent / "outside.png"
            )

            assembly_dir = job_dir / "assembly"
            assembly_dir.mkdir(exist_ok=True)
            (assembly_dir / "assembly_plan.json").write_text(
                json.dumps(plan, indent=2),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "Visual asset path escapes job directory",
            ):
                render_assembly(job_dir)

    def test_simple_renderer_rejects_output_path_outside_job(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = self._create_simple_job(Path(temp_dir))
            plan = build_assembly_plan(job_dir)
            plan["output"]["path"] = str(
                Path(temp_dir).parent / "outside.mp4"
            )

            assembly_dir = job_dir / "assembly"
            assembly_dir.mkdir(exist_ok=True)
            (assembly_dir / "assembly_plan.json").write_text(
                json.dumps(plan, indent=2),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "Output path escapes job directory",
            ):
                render_assembly(job_dir)

    def test_simple_renderer_rejects_multiple_scenes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = self._create_simple_job(Path(temp_dir))
            plan = build_assembly_plan(job_dir)
            plan["scenes"].append(
                dict(plan["scenes"][0], scene_id="scene_002", order=2)
            )

            assembly_dir = job_dir / "assembly"
            assembly_dir.mkdir(exist_ok=True)
            (assembly_dir / "assembly_plan.json").write_text(
                json.dumps(plan, indent=2),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "Simple Renderer currently supports exactly one scene",
            ):
                render_assembly(job_dir)


if __name__ == "__main__":
    unittest.main()
