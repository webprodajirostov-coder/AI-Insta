import json
import tempfile
import unittest
from pathlib import Path

from src.content_concept_generator import ContentConceptGenerator
from src.content_creation_orchestrator import ContentCreationOrchestrator
from src.content_idea_generator import ContentIdeaGenerator
from src.scenario_generator import ScenarioGenerator


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


class ContentCreationOrchestratorTests(unittest.TestCase):
    def test_generates_content_chain_and_creates_job(self):
        account = {
            "account_id": "account_001",
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
            "knowledge_id": "knowledge_001",
            "account_id": "account_001",
            "core_concepts": [{"id": "kc_001"}],
            "audience_insights": [{"id": "ai_001"}],
            "psychological_mechanisms": [],
            "content_pillars": [],
        }
        idea = {
            "idea_id": "idea_001",
            "account_id": "account_001",
            "status": "draft",
            "source": {"type": "knowledge", "source_ids": ["kc_001"]},
            "topic": "pricing",
            "content_pillar": "Relatable Pain",
            "funnel_stage": "tofu",
            "angle": "Pricing hesitation can protect from rejection.",
            "audience_problem": "Naming the price feels unsafe.",
            "audience_desire": "Charge appropriately.",
            "hook_direction": "Reveal the hidden reason.",
            "why_now": "Pricing is often treated as tactics only.",
            "knowledge_refs": ["kc_001"],
            "research_refs": [],
            "production": {"profile": "simple"},
        }
        concept = {
            "concept_id": "concept_001",
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
            "scenario_id": "scenario_001",
            "account_id": "account_001",
            "concept_id": "concept_001",
            "production_profile": "simple",
            "status": "ready",
            "language": "en",
            "title": "Pricing",
            "hook": "You might not be undercharging because you're modest.",
            "caption": "Pricing can feel unsafe.",
            "duration_seconds": 8,
            "scenes": [{
                "scene_id": "scene_001",
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
            account_path = root / "account.json"
            knowledge_path = root / "knowledge.json"
            profile_path = root / "profile.json"
            account_path.write_text(json.dumps(account), encoding="utf-8")
            knowledge_path.write_text(json.dumps(knowledge), encoding="utf-8")
            profile_path.write_text(json.dumps(profile), encoding="utf-8")

            calls = []

            def pipeline_runner(job_dir):
                calls.append(Path(job_dir))
                return True

            orchestrator = ContentCreationOrchestrator(
                idea_generator=ContentIdeaGenerator(StubIdeaProvider(idea)),
                concept_generator=ContentConceptGenerator(
                    StubConceptProvider(concept)
                ),
                scenario_generator=ScenarioGenerator(
                    StubScenarioProvider(scenario)
                ),
                pipeline_runner=pipeline_runner,
            )

            job_dir = orchestrator.create(
                account_path=account_path,
                knowledge_path=knowledge_path,
                production_profile_path=profile_path,
                jobs_root=root / "jobs",
                accounts_root=root / "accounts",
                run=True,
            )

            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0], job_dir)

            job = json.loads(
                (job_dir / "job.json").read_text(encoding="utf-8")
            )
            self.assertEqual(job["account_id"], "account_001")
            self.assertEqual(job["content"]["concept_id"], "concept_001")
            self.assertEqual(job["content"]["scenario_id"], "scenario_001")
            self.assertEqual(
                json.loads(
                    (job_dir / "input" / "content_idea.json").read_text(
                        encoding="utf-8"
                    )
                )["idea_id"],
                "idea_001",
            )


if __name__ == "__main__":
    unittest.main()
