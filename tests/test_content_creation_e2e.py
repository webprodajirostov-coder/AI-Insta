import base64
import json
import tempfile
import unittest
from pathlib import Path

from src.content_concept_generator import ContentConceptGenerator
from src.content_creation_orchestrator import ContentCreationOrchestrator
from src.content_idea_generator import ContentIdeaGenerator
from src.scenario_generator import ScenarioGenerator
from src.job_pipeline import run_pipeline


class StubIdeaProvider:
    def __init__(self, idea):
        self.idea = idea

    def generate_content_ideas(self, **kwargs):
        return [self.idea]


class StubConceptProvider:
    def __init__(self, concept):
        self.concept = concept

    def generate_content_concepts(self, **kwargs):
        return [self.concept]


class StubScenarioProvider:
    def __init__(self, scenario):
        self.scenario = scenario

    def generate_scenarios(self, **kwargs):
        return [self.scenario]


class ContentCreationE2ETests(unittest.TestCase):
    def test_content_creation_reaches_completed_final_asset(self):
        account = {
            "account_id": "account_e2e",
            "version": 1,
            "status": "active",
            "identity": {"language": "en"},
            "audience": {},
            "content_strategy": {"pillars": ["Relatable Pain"]},
            "production_defaults": {
                "baseline_format": "simple",
                "supported_complexity_levels": ["simple"],
            },
        }
        knowledge = {
            "knowledge_id": "knowledge_e2e",
            "account_id": "account_e2e",
            "core_concepts": [{"id": "kc_e2e"}],
            "audience_insights": [{"id": "ai_e2e"}],
            "psychological_mechanisms": [],
            "content_pillars": [],
        }
        idea = {
            "idea_id": "idea_e2e",
            "account_id": "account_e2e",
            "status": "draft",
            "source": {"type": "knowledge", "source_ids": ["kc_e2e"]},
            "topic": "pricing",
            "content_pillar": "Relatable Pain",
            "funnel_stage": "tofu",
            "angle": "Pricing hesitation can protect from rejection.",
            "audience_problem": "Naming the price feels unsafe.",
            "audience_desire": "Charge appropriately.",
            "hook_direction": "Reveal the hidden reason.",
            "why_now": "Pricing is often treated as tactics only.",
            "knowledge_refs": ["kc_e2e"],
            "research_refs": [],
            "production": {"profile": "simple"},
        }
        concept = {
            "concept_id": "concept_e2e",
            "core_message": "Pricing hesitation can protect from rejection.",
            "problem": "The expert lowers price before being asked.",
            "reframe": "The problem may be emotional safety.",
            "psychological_mechanism": "rejection_avoidance",
            "key_points": ["Notice the emotion before naming the price."],
            "hook": "You might not be undercharging because you're modest.",
            "emotional_direction": "recognition to reflection",
            "audience_takeaway": "Notice the emotion before naming the price.",
            "cta": {"type": "none", "text": ""},
        }
        scenario = {
            "schema_version": 2,
            "entity": "Scenario",
            "scenario_id": "scenario_e2e",
            "account_id": "account_e2e",
            "concept_id": "concept_e2e",
            "production_profile": "simple",
            "status": "ready",
            "language": "en",
            "title": "Pricing",
            "hook": "You might not be undercharging because you're modest.",
            "caption": "Pricing can feel unsafe.",
            "duration_seconds": 8,
            "scenes": [{
                "scene_id": "scene_e2e",
                "order": 1,
                "duration_seconds": 8,
                "voiceover_text": "",
                "visual": {
                    "type": "image",
                    "generation_required": True,
                    "prompt_en": "Minimal cinematic pricing scene.",
                },
                "text_overlay": None,
                "subtitles": None,
            }],
            "assembly": {"transitions": False, "animation": "minimal"},
        }
        profile = {
            "profile_id": "simple",
            "version": 1,
            "status": "active",
            "visual": {"count": 1, "types": ["image", "video"]},
            "audio": {"tts": False, "music": True},
            "text": {
                "hook_overlay": True,
                "subtitles": False,
                "dynamic_subtitles": False,
            },
            "editing": {"transitions": False, "animation": "minimal"},
            "duration_seconds": {"min": 6, "max": 10},
            "cost_level": 1,
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_root = root / "accounts" / "account_e2e"
            account_root.mkdir(parents=True)

            (account_root / "account.json").write_text(
                json.dumps(account), encoding="utf-8"
            )
            (account_root / "knowledge.json").write_text(
                json.dumps(knowledge), encoding="utf-8"
            )

            account_path = root / "account_input.json"
            knowledge_path = root / "knowledge_input.json"
            profile_path = root / "profile.json"

            account_path.write_text(json.dumps(account), encoding="utf-8")
            knowledge_path.write_text(json.dumps(knowledge), encoding="utf-8")
            profile_path.write_text(json.dumps(profile), encoding="utf-8")

            def pipeline_runner(job_dir):
                job_dir = Path(job_dir)
                visual_dir = job_dir / "media" / "visual"
                visual_path = visual_dir / "visual_001.png"
                visual_asset_path = visual_dir / "visual_001.json"

                if not visual_asset_path.exists():
                    visual_path.write_bytes(
                        base64.b64decode(
                            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
                            "+A8AAQUBAScY42YAAAAASUVORK5CYII="
                        )
                    )

                    job = json.loads(
                        (job_dir / "job.json").read_text(encoding="utf-8")
                    )
                    visual_asset = {
                        "schema_version": 1,
                        "entity": "VisualAsset",
                        "asset_id": "visual_001",
                        "job_id": job["job_id"],
                        "type": "image",
                        "status": "ready",
                        "source": {
                            "provider": "test",
                            "prompt": scenario["scenes"][0]["visual"]["prompt_en"],
                        },
                        "path": str(visual_path.resolve()),
                        "provider_job": None,
                    }
                    visual_asset_path.write_text(
                        json.dumps(visual_asset),
                        encoding="utf-8",
                    )

                return run_pipeline(job_dir)

            orchestrator = ContentCreationOrchestrator(
                idea_generator=ContentIdeaGenerator(
                    StubIdeaProvider(idea)
                ),
                concept_generator=ContentConceptGenerator(
                    StubConceptProvider(concept)
                ),
                scenario_generator=ScenarioGenerator(
                    StubScenarioProvider(scenario)
                ),
                pipeline_runner=pipeline_runner,
            )

            result = orchestrator.create(
                account_path=account_path,
                knowledge_path=knowledge_path,
                production_profile_path=profile_path,
                jobs_root=root / "jobs",
                accounts_root=root / "accounts",
                run=True,
            )

            self.assertEqual(result.status, "completed")
            self.assertIsNotNone(result.output_path)
            self.assertEqual(
                result.output_path.resolve(),
                (result.job_dir / "output" / "final.mp4").resolve(),
            )

            job_dir = result.job_dir
            job = json.loads(
                (job_dir / "job.json").read_text(encoding="utf-8")
            )

            self.assertEqual(job["status"], "completed")
            self.assertEqual(
                job["pipeline"],
                {
                    "research": "skipped",
                    "analysis": "skipped",
                    "concept": "completed",
                    "scenario": "completed",
                    "audio": "completed",
                    "visual": "completed",
                    "assembly": "completed",
                    "output": "completed",
                },
            )

            output_path = job_dir / "output" / "final.mp4"
            self.assertTrue(output_path.is_file())
            self.assertEqual(
                Path(job["artifacts"]["output"]).resolve(),
                output_path.resolve(),
            )

            plan = json.loads(
                (job_dir / "assembly" / "assembly_plan.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(plan["job_id"], job["job_id"])
            self.assertEqual(plan["scenario_id"], "scenario_e2e")
            self.assertEqual(
                plan["scenes"][0]["visual"]["asset_id"],
                "visual_001",
            )
            self.assertEqual(
                plan["inputs"]["audio"]["music"]["asset_id"],
                "music_001",
            )

            music_asset = json.loads(
                (job_dir / "media" / "audio" / "music_001.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(music_asset["job_id"], job["job_id"])
            self.assertEqual(music_asset["type"], "music")
            self.assertEqual(music_asset["status"], "ready")

            stored_scenario = json.loads(
                (job_dir / "content" / "scenario.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(stored_scenario["concept_id"], "concept_e2e")
            self.assertEqual(stored_scenario["account_id"], "account_e2e")

            self.assertTrue(run_pipeline(job_dir))

            rerun_job = json.loads(
                (job_dir / "job.json").read_text(encoding="utf-8")
            )
            self.assertEqual(rerun_job["status"], "completed")
            self.assertEqual(rerun_job["pipeline"]["output"], "completed")
            self.assertTrue(output_path.is_file())


if __name__ == "__main__":
    unittest.main()
