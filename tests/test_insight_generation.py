import unittest

from src.insight_generation import InsightGenerator
from src.research_analysis import ResearchAnalysisResult, ResearchAnalyzer


ACCOUNT = {
    "account_id": "sales_psychology_001",
    "version": 1,
    "status": "active",
    "identity": {
        "language": "en",
        "content_language": "English",
        "niche": "Money Psychology / Sales Psychology / Mindset",
    },
    "audience": {},
    "content_strategy": {
        "pillars": [
            "Relatable Pain",
            "Mindset Paradigm Shift",
            "Micro-Tools & Quick Tips",
            "Hard Truths & Myths",
        ]
    },
    "production_defaults": {},
}

KNOWLEDGE = {
    "knowledge_id": "sales_psychology_001_knowledge",
    "account_id": "sales_psychology_001",
    "version": 1,
    "status": "active",
}


RESEARCH_RECORD = {
    "research_id": "research_001",
    "account_id": "sales_psychology_001",
}

ANALYSIS = ResearchAnalysisResult(
    research_id="research_001",
    account_id="sales_psychology_001",
    summary="The source connects pricing behavior with fear of rejection.",
    patterns=["Avoiding social risk can influence pricing behavior."],
    observations=["Undercharging may function as protection from rejection."],
)


class DeterministicInsightProvider:
    def generate(
        self,
        research_record,
        analysis_result,
        account,
        knowledge,
    ):
        return [
            {
                "insight_id": "insight_001",
                "account_id": "sales_psychology_001",
                "status": "draft",
                "source": {
                    "type": "competitor_video",
                    "reference": "research_001",
                },
                "topic": "pricing objections",
                "observation": (
                    "Undercharging may function as protection from rejection."
                ),
                "evidence": [
                    "The analyzed source connects pricing behavior with fear of rejection."
                ],
                "relevance": (
                    "This is relevant to an audience that struggles with undercharging."
                ),
                "content_implications": [
                    "Explore the relationship between pricing and rejection avoidance."
                ],
                "confidence": 0.8,
            }
        ]


class InsightGenerationTests(unittest.TestCase):
    def test_generates_research_insight(self):
        generator = InsightGenerator(DeterministicInsightProvider())

        insights = generator.generate(
            RESEARCH_RECORD,
            ANALYSIS,
            ACCOUNT,
            KNOWLEDGE,
        )

        self.assertEqual(len(insights), 1)

        insight = insights[0]

        self.assertEqual(insight.insight_id, "insight_001")
        self.assertEqual(insight.account_id, "sales_psychology_001")
        self.assertEqual(insight.source["reference"], "research_001")
        self.assertEqual(insight.topic, "pricing objections")
        self.assertEqual(insight.confidence, 0.8)

    def test_generates_multiple_insights_from_one_research_record(self):
        class MultipleInsightProvider:
            def generate(self, *args):
                return [
                    {
                        "insight_id": "insight_001",
                        "account_id": "sales_psychology_001",
                        "status": "draft",
                        "source": {"reference": "research_001"},
                        "topic": "pricing objections",
                        "observation": "Undercharging may function as protection from rejection.",
                        "evidence": ["Pricing behavior can be linked to fear of rejection."],
                        "relevance": "Relevant to the account audience.",
                        "content_implications": [
                            "Explore rejection avoidance behind undercharging."
                        ],
                        "confidence": 0.8,
                    },
                    {
                        "insight_id": "insight_002",
                        "account_id": "sales_psychology_001",
                        "status": "draft",
                        "source": {"reference": "research_001"},
                        "topic": "social risk",
                        "observation": "Lower prices may reduce perceived social risk.",
                        "evidence": ["The source connects pricing with social risk."],
                        "relevance": "Relevant to the account audience.",
                        "content_implications": [
                            "Explore how perceived social risk affects pricing."
                        ],
                        "confidence": 0.7,
                    },
                ]

        generator = InsightGenerator(MultipleInsightProvider())

        insights = generator.generate(
            RESEARCH_RECORD,
            ANALYSIS,
            ACCOUNT,
            KNOWLEDGE,
        )

        self.assertEqual(len(insights), 2)
        self.assertEqual(
            [insight.insight_id for insight in insights],
            ["insight_001", "insight_002"],
        )
        self.assertEqual(
            [insight.source["reference"] for insight in insights],
            ["research_001", "research_001"],
        )
        self.assertTrue(
            all(
                insight.account_id == "sales_psychology_001"
                for insight in insights
            )
        )

    def test_research_analysis_to_insight_generation_chain(self):
        class DeterministicResearchProvider:
            def analyze(self, research_record):
                return ResearchAnalysisResult(
                    research_id=research_record["research_id"],
                    account_id=research_record["account_id"],
                    summary="The source connects pricing behavior with fear of rejection.",
                    patterns=[
                        "Avoiding social risk can influence pricing behavior."
                    ],
                    observations=[
                        "Undercharging may function as protection from rejection."
                    ],
                )

        research_analyzer = ResearchAnalyzer(
            DeterministicResearchProvider()
        )

        analysis_result = research_analyzer.analyze(
            RESEARCH_RECORD,
            account_id=ACCOUNT["account_id"],
        )

        insight_generator = InsightGenerator(
            DeterministicInsightProvider()
        )

        insights = insight_generator.generate(
            RESEARCH_RECORD,
            analysis_result,
            ACCOUNT,
            KNOWLEDGE,
        )

        self.assertEqual(len(insights), 1)
        self.assertEqual(
            analysis_result.research_id,
            insights[0].source["reference"],
        )
        self.assertEqual(
            analysis_result.account_id,
            insights[0].account_id,
        )
        self.assertIn(
            "rejection",
            insights[0].observation.lower(),
        )

    def test_invalid_confidence_is_rejected(self):
        class InvalidConfidenceProvider:
            def generate(self, *args):
                return [
                    {
                        "insight_id": "insight_001",
                        "account_id": "sales_psychology_001",
                        "status": "draft",
                        "source": {"reference": "research_001"},
                        "topic": "pricing objections",
                        "observation": "Observation",
                        "evidence": ["Evidence"],
                        "relevance": "Relevant",
                        "content_implications": ["Implication"],
                        "confidence": 1.7,
                    }
                ]

        generator = InsightGenerator(InvalidConfidenceProvider())

        with self.assertRaises(Exception):
            generator.generate(
                RESEARCH_RECORD,
                ANALYSIS,
                ACCOUNT,
                KNOWLEDGE,
            )

    def test_non_list_evidence_is_rejected(self):
        class InvalidEvidenceProvider:
            def generate(self, *args):
                return [
                    {
                        "insight_id": "insight_001",
                        "account_id": "sales_psychology_001",
                        "status": "draft",
                        "source": {"reference": "research_001"},
                        "topic": "pricing objections",
                        "observation": "Observation",
                        "evidence": "Evidence",
                        "relevance": "Relevant",
                        "content_implications": ["Implication"],
                        "confidence": 0.8,
                    }
                ]

        generator = InsightGenerator(InvalidEvidenceProvider())

        with self.assertRaises(Exception):
            generator.generate(
                RESEARCH_RECORD,
                ANALYSIS,
                ACCOUNT,
                KNOWLEDGE,
            )

    def test_missing_observation_is_rejected(self):
        class MissingObservationProvider:
            def generate(self, *args):
                return [
                    {
                        "insight_id": "insight_001",
                        "account_id": "sales_psychology_001",
                        "status": "draft",
                        "source": {"reference": "research_001"},
                        "topic": "pricing objections",
                        "evidence": ["Evidence"],
                        "relevance": "Relevant",
                        "content_implications": ["Implication"],
                        "confidence": 0.8,
                    }
                ]

        generator = InsightGenerator(MissingObservationProvider())

        with self.assertRaises(Exception):
            generator.generate(
                RESEARCH_RECORD,
                ANALYSIS,
                ACCOUNT,
                KNOWLEDGE,
            )

    def test_result_has_no_creative_production_fields(self):
        generator = InsightGenerator(DeterministicInsightProvider())

        insights = generator.generate(
            RESEARCH_RECORD,
            ANALYSIS,
            ACCOUNT,
            KNOWLEDGE,
        )

        data = insights[0].to_dict()

        forbidden_fields = {
            "hook",
            "cta",
            "target_emotion",
            "visual",
            "audio",
            "scenario",
            "production",
        }

        self.assertTrue(forbidden_fields.isdisjoint(data))

    def test_cross_account_research_is_rejected(self):
        generator = InsightGenerator(DeterministicInsightProvider())

        foreign_record = {
            "research_id": "research_001",
            "account_id": "other_account",
        }

        with self.assertRaises(ValueError):
            generator.generate(
                foreign_record,
                ANALYSIS,
                ACCOUNT,
                KNOWLEDGE,
            )

    def test_cross_account_insight_is_rejected(self):
        class ForeignInsightProvider:
            def generate(self, *args):
                return [
                    {
                        "insight_id": "insight_001",
                        "account_id": "other_account",
                        "status": "draft",
                        "source": {"reference": "research_001"},
                        "topic": "pricing",
                        "observation": "Observation",
                        "evidence": ["Evidence"],
                        "relevance": "Relevant",
                        "content_implications": ["Implication"],
                        "confidence": 0.8,
                    }
                ]

        generator = InsightGenerator(ForeignInsightProvider())

        with self.assertRaises(Exception):
            generator.generate(
                RESEARCH_RECORD,
                ANALYSIS,
                ACCOUNT,
                KNOWLEDGE,
            )


if __name__ == "__main__":
    unittest.main()
