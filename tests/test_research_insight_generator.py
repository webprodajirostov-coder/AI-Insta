import unittest

from src.domain_validation import DomainValidationError
from src.research_insight_generator import ResearchInsightGenerator


class StubProvider:
    def __init__(self, insights):
        self.insights = insights
        self.calls = 0
        self.last_inputs = None

    def generate_research_insights(self, *, account, research):
        self.calls += 1
        self.last_inputs = (account, list(research))
        return self.insights


class ResearchInsightGeneratorTests(unittest.TestCase):
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
        self.research = {
            "research_id": "research_001",
            "account_id": "account_001",
            "status": "ready",
            "source": {"type": "competitor_analysis", "reference": "competitor_001"},
            "subject": "competitor_001",
            "material": [
                {
                    "id": "item_001",
                    "type": "video",
                    "content": "Competitor repeatedly frames pricing around fear of rejection.",
                }
            ],
        }
        self.insight = {
            "insight_id": "insight_001",
            "schema_version": 2,
            "source": {
                "research_id": "research_001",
                "material_refs": ["item_001"],
                "type": "competitor_analysis",
                "reference": "competitor_001",
            },
            "topic": "pricing",
            "observation": "Pricing content repeatedly uses rejection framing.",
            "evidence": ["Observed in supplied competitor material."],
            "relevance": "Useful for the account's pricing theme.",
            "content_implications": ["Explore the emotional reason behind undercharging."],
            "confidence": 0.8,
        }

    def test_generates_valid_insights_from_research(self):
        provider = StubProvider([self.insight])
        result = ResearchInsightGenerator(provider).generate(
            account=self.account,
            research=[self.research],
        )

        self.assertEqual(len(result.insights), 1)
        self.assertEqual(result.insights[0]["insight_id"], "insight_001")
        self.assertEqual(
            result.insights[0]["source"]["research_id"],
            "research_001",
        )
        self.assertEqual(provider.calls, 1)

    def test_rejects_cross_account_research_before_provider_call(self):
        broken = dict(self.research)
        broken["account_id"] = "other_account"
        provider = StubProvider([self.insight])

        with self.assertRaises(DomainValidationError):
            ResearchInsightGenerator(provider).generate(
                account=self.account,
                research=[broken],
            )

        self.assertEqual(provider.calls, 0)

    def test_rejects_insight_from_unknown_research(self):
        broken = dict(self.insight)
        broken["source"] = dict(broken["source"], research_id="missing")
        provider = StubProvider([broken])

        with self.assertRaises(DomainValidationError):
            ResearchInsightGenerator(provider).generate(
                account=self.account,
                research=[self.research],
            )

    def test_rejects_unknown_research_material_reference(self):
        broken = dict(self.insight)
        broken["source"] = dict(
            broken["source"],
            material_refs=["missing_material"],
        )
        provider = StubProvider([broken])

        with self.assertRaises(DomainValidationError):
            ResearchInsightGenerator(provider).generate(
                account=self.account,
                research=[self.research],
            )

    def test_rejects_missing_material_references(self):
        broken = dict(self.insight)
        broken["source"] = dict(broken["source"])
        broken["source"].pop("material_refs")
        provider = StubProvider([broken])

        with self.assertRaises(DomainValidationError):
            ResearchInsightGenerator(provider).generate(
                account=self.account,
                research=[self.research],
            )

    def test_rejects_invalid_confidence(self):
        broken = dict(self.insight)
        broken["confidence"] = 2
        provider = StubProvider([broken])

        with self.assertRaises(DomainValidationError):
            ResearchInsightGenerator(provider).generate(
                account=self.account,
                research=[self.research],
            )

    def test_rejects_provider_non_object(self):
        provider = StubProvider(["invalid"])

        with self.assertRaises(DomainValidationError):
            ResearchInsightGenerator(provider).generate(
                account=self.account,
                research=[self.research],
            )


if __name__ == "__main__":
    unittest.main()
