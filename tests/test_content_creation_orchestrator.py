import json
import tempfile
import unittest
from pathlib import Path

from src.content_concept_generator import ContentConceptGenerator
from src.content_creation_orchestrator import ContentCreationOrchestrator
from src.content_idea_generator import ContentIdeaGenerator
from src.domain_validation import DomainValidationError
from src.production_profile_store import ProductionProfileStore
from src.research_insight_generator import ResearchInsightGenerator
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


class StubResearchInsightProvider:
    def __init__(self, insight):
        self.insight = insight
        self.calls = 0

    def generate_research_insights(self, *, account, research):
        self.calls += 1
        return [self.insight]


class StubScenarioProvider:
    def __init__(self, scenario):
        self.scenario = scenario
        self.calls = 0

    def generate_scenarios(self, **kwargs):
        self.calls += 1
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
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_path = root / "account.json"
            knowledge_path = root / "knowledge.json"
            account_path.write_text(json.dumps(account), encoding="utf-8")
            knowledge_path.write_text(json.dumps(knowledge), encoding="utf-8")

            account_root = root / "accounts" / "account_001"
            account_root.mkdir(parents=True)
            (account_root / "account.json").write_text(
                json.dumps(account),
                encoding="utf-8",
            )
            (account_root / "knowledge.json").write_text(
                json.dumps(knowledge),
                encoding="utf-8",
            )

            calls = []

            def pipeline_runner(job_dir):
                job_dir = Path(job_dir)
                calls.append(job_dir)
                job_path = job_dir / "job.json"
                job = json.loads(job_path.read_text(encoding="utf-8"))
                job["status"] = "completed"
                job["pipeline"]["output"] = "completed"
                job["artifacts"]["output"] = str(
                    job_dir / "output" / "final.mp4"
                )
                job_path.write_text(json.dumps(job), encoding="utf-8")
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
                production_profile_store=ProductionProfileStore(
                    Path(__file__).resolve().parents[1] / "data" / "production_profiles"
                ),
            )

            result = orchestrator.create(
                account_path=account_path,
                knowledge_path=knowledge_path,
                jobs_root=root / "jobs",
                accounts_root=root / "accounts",
                run=True,
            )

            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0], result.job_dir)
            self.assertEqual(result.status, "completed")

            job = json.loads(
                (result.job_dir / "job.json").read_text(encoding="utf-8")
            )
            self.assertEqual(job["account_id"], "account_001")
            self.assertEqual(job["content"]["concept_id"], "concept_001")
            self.assertEqual(job["content"]["scenario_id"], "scenario_001")
            self.assertEqual(
                json.loads(
                    (result.job_dir / "input" / "content_idea.json").read_text(
                        encoding="utf-8"
                    )
                )["idea_id"],
                "idea_001",
            )

    def test_raw_research_flows_through_content_creation(self):
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
            "audience_insights": [],
            "psychological_mechanisms": [],
            "content_pillars": [],
        }
        research = {
            "research_id": "research_001",
            "account_id": "account_001",
            "status": "ready",
            "source": {"type": "competitor", "reference": "competitor_001"},
            "subject": "competitor pricing content",
            "material": [{"id": "material_001", "type": "post", "text": "Pricing fear."}],
        }
        insight = {
            "insight_id": "insight_001",
            "source": {
                "research_id": "research_001",
                "type": "competitor",
                "reference": "material_001",
            },
            "topic": "pricing",
            "observation": "Pricing content links hesitation with rejection.",
            "evidence": ["material_001"],
            "relevance": "Useful content angle.",
            "content_implications": ["Explore rejection avoidance."],
            "confidence": 0.8,
        }
        idea = {
            "idea_id": "idea_001",
            "account_id": "account_001",
            "status": "draft",
            "source": {"type": "research", "source_ids": ["insight_001"]},
            "topic": "undercharging",
            "content_pillar": "Relatable Pain",
            "funnel_stage": "tofu",
            "angle": "The hidden reason behind undercharging.",
            "audience_problem": "Pricing feels unsafe.",
            "audience_desire": "Charge appropriately.",
            "hook_direction": "Expose the hidden pattern.",
            "why_now": "Pricing is often treated as tactics.",
            "knowledge_refs": ["kc_001"],
            "research_refs": ["insight_001"],
            "production": {"profile": "simple"},
        }
        concept = {
            "concept_id": "concept_001",
            "account_id": "account_001",
            "idea_id": "idea_001",
            "knowledge_refs": ["kc_001"],
            "research_refs": ["insight_001"],
            "production_profile": "simple",
            "core_message": "Undercharging can protect against rejection.",
            "problem": "The expert lowers price before being asked.",
            "reframe": "Pricing can feel emotionally unsafe.",
            "psychological_mechanism": "rejection_avoidance",
            "key_points": ["Notice the emotion before naming the price."],
            "hook": "You might not be undercharging because you're modest.",
            "emotional_direction": "recognition to reflection",
            "audience_takeaway": "Notice the emotion before naming your price.",
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

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_path = root / "account.json"
            knowledge_path = root / "knowledge.json"
            research_path = root / "research.json"
            account_path.write_text(json.dumps(account), encoding="utf-8")
            knowledge_path.write_text(json.dumps(knowledge), encoding="utf-8")
            research_path.write_text(json.dumps(research), encoding="utf-8")

            account_root = root / "accounts" / "account_001"
            account_root.mkdir(parents=True)
            (account_root / "account.json").write_text(json.dumps(account), encoding="utf-8")
            (account_root / "knowledge.json").write_text(json.dumps(knowledge), encoding="utf-8")

            calls = []

            def pipeline_runner(job_dir):
                calls.append(Path(job_dir))
                job_path = Path(job_dir) / "job.json"
                job = json.loads(job_path.read_text(encoding="utf-8"))
                job["status"] = "completed"
                job["pipeline"]["output"] = "completed"
                job["artifacts"]["output"] = str(Path(job_dir) / "output" / "final.mp4")
                job_path.write_text(json.dumps(job), encoding="utf-8")
                return True

            insight_provider = StubResearchInsightProvider(insight)
            orchestrator = ContentCreationOrchestrator(
                idea_generator=ContentIdeaGenerator(StubIdeaProvider(idea)),
                concept_generator=ContentConceptGenerator(StubConceptProvider(concept)),
                scenario_generator=ScenarioGenerator(StubScenarioProvider(scenario)),
                research_insight_generator=ResearchInsightGenerator(insight_provider),
                pipeline_runner=pipeline_runner,
                production_profile_store=ProductionProfileStore(
                    Path(__file__).resolve().parents[1] / "data" / "production_profiles"
                ),
            )

            result = orchestrator.create(
                account_path=account_path,
                knowledge_path=knowledge_path,
                raw_research_paths=[research_path],
                jobs_root=root / "jobs",
                accounts_root=root / "accounts",
                run=True,
            )

            self.assertEqual(result.status, "completed")
            self.assertEqual(insight_provider.calls, 1)
            self.assertEqual(len(calls), 1)
            job = json.loads((result.job_dir / "job.json").read_text(encoding="utf-8"))
            persisted_idea = json.loads(
                (result.job_dir / "input" / "content_idea.json").read_text(encoding="utf-8")
            )
            persisted_concept = json.loads(
                (result.job_dir / "content" / "content_concept.json").read_text(encoding="utf-8")
            )
            self.assertEqual(persisted_idea["research_refs"], ["insight_001"])
            self.assertEqual(persisted_concept["research_refs"], ["insight_001"])
            persisted_research = json.loads(
                (result.job_dir / "research" / "research_insights.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                persisted_research["research_insights"][0]["insight_id"],
                "insight_001",
            )
            self.assertEqual(job["content"]["concept_id"], "concept_001")

    def test_rejects_unsupported_concept_profile_before_scenario_generation(self):
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
            "production": {"profile": "standard"},
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
            "production_profile": "standard",
        }
        scenario_provider = StubScenarioProvider({})
        orchestrator = ContentCreationOrchestrator(
            idea_generator=ContentIdeaGenerator(StubIdeaProvider(idea)),
            concept_generator=ContentConceptGenerator(
                StubConceptProvider(concept)
            ),
            scenario_generator=ScenarioGenerator(scenario_provider),
            production_profile_store=ProductionProfileStore(
                Path(__file__).resolve().parents[1] / "data" / "production_profiles"
            ),
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_path = root / "account.json"
            knowledge_path = root / "knowledge.json"
            account_path.write_text(json.dumps(account), encoding="utf-8")
            knowledge_path.write_text(json.dumps(knowledge), encoding="utf-8")

            with self.assertRaises(DomainValidationError):
                orchestrator.create(
                    account_path=account_path,
                    knowledge_path=knowledge_path,
                    jobs_root=root / "jobs",
                    accounts_root=root / "accounts",
                    run=False,
                )

        self.assertEqual(scenario_provider.calls, 0)

    def test_result_mapping_preserves_waiting_and_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            waiting_dir = root / "waiting_job"
            waiting_dir.mkdir()
            (waiting_dir / "job.json").write_text(
                json.dumps({"status": "waiting"}),
                encoding="utf-8",
            )

            failed_dir = root / "failed_job"
            failed_dir.mkdir()
            (failed_dir / "job.json").write_text(
                json.dumps({
                    "status": "failed",
                    "error": "visual generation failed",
                }),
                encoding="utf-8",
            )

            waiting = ContentCreationOrchestrator._result_from_job(waiting_dir)
            failed = ContentCreationOrchestrator._result_from_job(failed_dir)

            self.assertEqual(waiting.status, "waiting")
            self.assertEqual(waiting.job_dir, waiting_dir)
            self.assertIsNone(waiting.output_path)
            self.assertIsNone(waiting.error)

            self.assertEqual(failed.status, "failed")
            self.assertEqual(failed.job_dir, failed_dir)
            self.assertIsNone(failed.output_path)
            self.assertEqual(failed.error, "visual generation failed")


if __name__ == "__main__":
    unittest.main()
