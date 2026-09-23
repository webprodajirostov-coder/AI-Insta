import unittest

from src.domain_validation import (
    DomainValidationError,
    validate_research_insight,
)


class ResearchInsightValidationTests(unittest.TestCase):
    def setUp(self):
        self.insight = {
            "schema_version": 1,
            "entity": "ResearchInsight",
            "insight_id": "insight_001",
            "account_id": "sales_psychology_001",
            "status": "ready",
            "source": {
                "type": "competitor_video",
                "reference": "video_001",
            },
            "topic": "pricing objections",
            "observation": "Pricing fear is often framed through rejection avoidance.",
            "evidence": ["Repeated pattern in analyzed source material."],
            "relevance": "Useful for pricing anxiety content.",
            "content_implications": [
                "Explore rejection avoidance as a content angle."
            ],
            "confidence": 0.8,
        }

    def test_valid_research_insight(self):
        validate_research_insight(
            self.insight,
            account_id="sales_psychology_001",
        )

    def test_rejects_cross_account_insight(self):
        with self.assertRaises(DomainValidationError):
            validate_research_insight(
                self.insight,
                account_id="other_account",
            )

    def test_rejects_invalid_confidence(self):
        broken = dict(self.insight)
        broken["confidence"] = 1.5

        with self.assertRaises(DomainValidationError):
            validate_research_insight(broken)

    def test_rejects_non_list_evidence(self):
        broken = dict(self.insight)
        broken["evidence"] = "not-a-list"

        with self.assertRaises(DomainValidationError):
            validate_research_insight(broken)


if __name__ == "__main__":
    unittest.main()
