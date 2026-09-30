import json
import tempfile
import unittest
from pathlib import Path

from src.content_concept_generator import ContentConceptGenerator
from src.content_concept_orchestrator import ContentConceptOrchestrator
from src.content_idea_generator import ContentIdeaGenerator
from src.content_idea_orchestrator import ContentIdeaOrchestrator
from src.research_insight_generator import ResearchInsightGenerator
from src.research_insight_orchestrator import ResearchInsightOrchestrator


class ResearchInsightProviderStub:
    def __init__(self, insights):
        self.insights = insights
        self.calls = 0

    def generate_research_insights(self, *, account, research):
        self.calls += 1
        return self.insights


class ContentIdeaProviderStub:
    def __init__(self, ideas):
        self.ideas = ideas
        self.calls = 0

    def generate_content_ideas(self, *, account, knowledge, research_insights):
        self.calls += 1
        self.research_insights = list(research_insights)
        return self.ideas


class ContentConceptProviderStub:
    def __init__(self, concepts):
        self.concepts = concepts
        self.calls = 0

    def generate_content_concepts(
        self,
        *,
        account,
        knowledge,
        idea,
        research_insights,
    ):
        self.calls += 1
        self.idea = idea
        self.research_insights = list(research_insights)
        return self.concepts


class ResearchToConceptIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.account = {
            "account_id": "account_001",
            "version": 1,
            "status": "active",
            "identity": {},
            "audience": {},
            "content_strategy": {"pillars": ["Relatable Pain"]},
            "production_defaults": {"baseline_format": "simple"},
        }
        self.knowledge = {
            "knowledge_id": "knowledge_001",
            "account_id": "account_001",
            "core_concepts": [{"id": "kc_001"}],
            "audience_insights": [{"id": "ai_001"}],
            "psychological_mechanisms": [],
            "content_pillars": [],
        }
        self.research = {
            "research_id": "research_001",
            "account_id": "account_001",
            "status": "ready",
            "source": {"type": "competitor", "reference": "competitor_001"},
            "subject": "competitor pricing content",
            "material": [
                {
                    "id": "material_001",
                    "type": "post",
                    "text": "Pricing content repeatedly addresses fear of rejection.",
                }
            ],
        }
        self.insight = {
            "insight_id": "insight_001",
            "schema_version": 2,
            "account_id": "account_001",
            "status": "ready",
            "source": {
                "type": "research",
                "research_id": "research_001",
                "material_refs": ["material_001"],
                "reference": "material_001",
            },
            "topic": "pricing",
            "observation": "Competitor content repeatedly links pricing hesitation with rejection.",
            "evidence": ["material_001"],
            "relevance": "This gives the account a concrete audience pain to explore.",
            "content_implications": ["Explore rejection avoidance behind undercharging."],
            "confidence": 0.8,
        }
        self.idea = {
            "idea_id": "idea_001",
            "account_id": "account_001",
            "status": "draft",
            "source": {"type": "research", "source_ids": ["insight_001"]},
            "topic": "undercharging",
            "content_pillar": "Relatable Pain",
            "funnel_stage": "tofu",
            "angle": "The hidden reason behind undercharging.",
            "audience_problem": "Pricing feels emotionally unsafe.",
            "audience_desire": "Charge appropriately without guilt.",
            "hook_direction": "Expose the hidden pattern.",
            "why_now": "Pricing is often treated as a tactics problem only.",
            "knowledge_refs": ["kc_001"],
            "research_refs": ["insight_001"],
            "production": {"profile": "simple"},
            "priority": 50,
        }
        self.concept = {
            "concept_id": "concept_001",
            "core_message": "Undercharging can protect against rejection.",
            "problem": "The expert lowers price before being asked.",
            "reframe": "Pricing can be emotionally safer than it feels.",
            "psychological_mechanism": "rejection_avoidance",
            "key_points": ["Notice the emotion before naming the price."],
            "hook": "You might not be undercharging because you're modest.",
            "emotional_direction": "recognition to reflection",
            "audience_takeaway": "Notice what happens before naming your price.",
            "cta": {"type": "none", "text": ""},
            "account_id": "account_001",
            "idea_id": "idea_001",
            "knowledge_refs": ["kc_001"],
            "research_refs": ["insight_001"],
            "production_profile": "simple",
        }

    def _write(self, root, name, value):
        path = root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_research_insight_flows_into_idea_and_concept(self):
        research_provider = ResearchInsightProviderStub([self.insight])
        research_orchestrator = ResearchInsightOrchestrator(
            ResearchInsightGenerator(research_provider)
        )

        idea_provider = ContentIdeaProviderStub([self.idea])
        idea_orchestrator = ContentIdeaOrchestrator(
            ContentIdeaGenerator(idea_provider)
        )

        concept_provider = ContentConceptProviderStub([self.concept])
        concept_orchestrator = ContentConceptOrchestrator(
            ContentConceptGenerator(concept_provider)
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_path = self._write(root, "account.json", self.account)
            knowledge_path = self._write(root, "knowledge.json", self.knowledge)
            research_path = self._write(root, "research.json", self.research)
            insights_path = root / "research_insights.json"
            idea_path = root / "idea.json"
            concept_path = root / "concept.json"

            research_orchestrator.generate(
                account_path=account_path,
                research_paths=[research_path],
                output_path=insights_path,
            )
            idea_orchestrator.generate(
                account_path=account_path,
                knowledge_path=knowledge_path,
                research_paths=[insights_path],
                output_path=idea_path,
            )
            persisted_idea_payload = json.loads(idea_path.read_text(encoding="utf-8"))
            persisted_idea_for_concept = root / "idea_for_concept.json"
            persisted_idea_for_concept.write_text(
                json.dumps(persisted_idea_payload["ideas"][0]), encoding="utf-8"
            )

            concept_orchestrator.generate(
                account_path=account_path,
                knowledge_path=knowledge_path,
                idea_path=persisted_idea_for_concept,
                research_paths=[insights_path],
                output_path=concept_path,
            )

            persisted_insights = json.loads(
                insights_path.read_text(encoding="utf-8")
            )["research_insights"]
            persisted_idea = json.loads(
                idea_path.read_text(encoding="utf-8")
            )["ideas"][0]
            persisted_concept = json.loads(
                concept_path.read_text(encoding="utf-8")
            )["concepts"][0]

            self.assertEqual(research_provider.calls, 1)
            self.assertEqual(
                persisted_insights[0]["source"]["research_id"],
                "research_001",
            )
            self.assertEqual(persisted_insights[0]["account_id"], "account_001")

            self.assertEqual(persisted_idea["account_id"], "account_001")
            self.assertEqual(persisted_idea["research_refs"], ["insight_001"])
            self.assertEqual(
                idea_provider.research_insights[0]["insight_id"],
                "insight_001",
            )

            self.assertEqual(persisted_concept["account_id"], "account_001")
            self.assertEqual(persisted_concept["idea_id"], "idea_001")
            self.assertEqual(persisted_concept["research_refs"], ["insight_001"])
            self.assertEqual(
                concept_provider.research_insights[0]["insight_id"],
                "insight_001",
            )

            self.assertNotIn("hook", persisted_idea)
            self.assertNotIn("caption", persisted_idea)
            self.assertNotIn("scenes", persisted_idea)
            self.assertNotIn("scenes", persisted_concept)
            self.assertNotIn("visual", persisted_concept)
            self.assertEqual(persisted_concept["production_profile"], "simple")


if __name__ == "__main__":
    unittest.main()
