import unittest

from src.content_idea_generator import ContentIdeaGenerator
from src.domain_validation import DomainValidationError


class StubContentIdeaProvider:
    def __init__(self, ideas):
        self.ideas = ideas
        self.calls = 0

    def generate_content_ideas(self, *, account, knowledge, research_insights):
        self.calls += 1
        return self.ideas


class ContentIdeaGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.account = {
            "account_id": "account_001",
            "version": 1,
            "status": "active",
            "identity": {},
            "audience": {},
            "content_strategy": {
                "pillars": ["Relatable Pain", "Mindset Paradigm Shift"]
            },
            "production_defaults": {"baseline_format": "simple"},
        }
        self.knowledge = {
            "knowledge_id": "knowledge_001",
            "account_id": "account_001",
            "core_concepts": [
                {"id": "kc_001", "statement": "Undercharging can protect from rejection."}
            ],
            "audience_insights": [
                {"id": "ai_001", "statement": "Experts may hesitate to charge their value."}
            ],
            "psychological_mechanisms": [],
            "content_pillars": [
                {"id": "pillar_001", "name": "Relatable Pain"}
            ],
        }
        self.insight = {
            "insight_id": "insight_001",
            "account_id": "account_001",
            "status": "ready",
            "source": {"type": "competitor_video", "reference": "research_001"},
            "topic": "pricing",
            "observation": "Pricing hesitation can involve rejection avoidance.",
            "evidence": ["Observed in source material."],
            "relevance": "Relevant to the account's pricing theme.",
            "content_implications": ["Explore rejection avoidance."],
            "confidence": 0.8,
        }
        self.idea = {
            "idea_id": "idea_002",
            "account_id": "account_001",
            "status": "draft",
            "source": {
                "type": "research_insight",
                "source_ids": ["insight_001"],
            },
            "topic": "undercharging",
            "content_pillar": "Relatable Pain",
            "funnel_stage": "tofu",
            "angle": "Undercharging can reduce the perceived risk of rejection.",
            "audience_problem": "An expert lowers their price before being asked.",
            "audience_desire": "Name an appropriate price without guilt.",
            "hook_direction": "Expose the hidden emotional reason behind undercharging.",
            "why_now": "Pricing is often treated only as a tactical sales problem.",
            "knowledge_refs": ["kc_001", "ai_001"],
            "research_refs": ["insight_001"],
            "production": {"profile": "simple"},
            "priority": 70,
        }

    def test_generates_valid_ideas_from_research_and_knowledge(self):
        provider = StubContentIdeaProvider([self.idea])
        result = ContentIdeaGenerator(provider).generate(
            account=self.account,
            knowledge=self.knowledge,
            research_insights=[self.insight],
        )

        self.assertEqual(len(result.ideas), 1)
        self.assertEqual(result.ideas[0]["idea_id"], "idea_002")
        self.assertEqual(result.ideas[0]["research_refs"], ["insight_001"])
        self.assertEqual(provider.calls, 1)

    def test_rejects_cross_account_research_insight(self):
        broken = dict(self.insight)
        broken["account_id"] = "other_account"

        with self.assertRaises(DomainValidationError):
            ContentIdeaGenerator(StubContentIdeaProvider([self.idea])).generate(
                account=self.account,
                knowledge=self.knowledge,
                research_insights=[broken],
            )

    def test_rejects_unknown_knowledge_reference(self):
        broken = dict(self.idea)
        broken["knowledge_refs"] = ["missing_knowledge"]

        with self.assertRaises(DomainValidationError):
            ContentIdeaGenerator(StubContentIdeaProvider([broken])).generate(
                account=self.account,
                knowledge=self.knowledge,
                research_insights=[self.insight],
            )

    def test_rejects_unknown_research_reference(self):
        broken = dict(self.idea)
        broken["research_refs"] = ["missing_insight"]

        with self.assertRaises(DomainValidationError):
            ContentIdeaGenerator(StubContentIdeaProvider([broken])).generate(
                account=self.account,
                knowledge=self.knowledge,
                research_insights=[self.insight],
            )

    def test_rejects_creative_production_fields(self):
        broken = dict(self.idea)
        broken["hook"] = "You are undercharging."

        with self.assertRaises(DomainValidationError):
            ContentIdeaGenerator(StubContentIdeaProvider([broken])).generate(
                account=self.account,
                knowledge=self.knowledge,
                research_insights=[self.insight],
            )

    def test_rejects_provider_non_object(self):
        provider = StubContentIdeaProvider(["not-an-idea"])

        with self.assertRaises(DomainValidationError):
            ContentIdeaGenerator(provider).generate(
                account=self.account,
                knowledge=self.knowledge,
                research_insights=[self.insight],
            )


if __name__ == "__main__":
    unittest.main()
