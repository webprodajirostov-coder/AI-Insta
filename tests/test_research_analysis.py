import unittest

from src.research_analysis import ResearchAnalysisResult, ResearchAnalyzer


class DeterministicProvider:
    def analyze(self, research_record):
        return ResearchAnalysisResult(
            research_id=research_record["research_id"],
            account_id=research_record["account_id"],
            summary="Pricing hesitation is linked to perceived social risk.",
            patterns=["Pricing hesitation is connected to rejection risk."],
            observations=["The source frames pricing fear as avoidance of rejection."],
        )


class MismatchedProvider:
    def analyze(self, research_record):
        return ResearchAnalysisResult(
            research_id="other_research",
            account_id=research_record["account_id"],
            summary="summary",
            patterns=[],
            observations=[],
        )


class ResearchAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "research_id": "research_001",
            "account_id": "sales_psychology_001",
            "source": {"type": "competitor_video"},
            "raw_material": "raw research material",
        }

    def test_analyzes_research_record_with_deterministic_provider(self):
        result = ResearchAnalyzer(DeterministicProvider()).analyze(
            self.record,
            account_id="sales_psychology_001",
        )

        self.assertEqual(result.research_id, "research_001")
        self.assertEqual(result.account_id, "sales_psychology_001")
        self.assertEqual(result.observations[0], "The source frames pricing fear as avoidance of rejection.")

    def test_rejects_cross_account_record(self):
        with self.assertRaises(ValueError):
            ResearchAnalyzer(DeterministicProvider()).analyze(
                self.record,
                account_id="other_account",
            )

    def test_rejects_provider_research_id_mismatch(self):
        with self.assertRaises(ValueError):
            ResearchAnalyzer(MismatchedProvider()).analyze(self.record)

    def test_result_does_not_require_creative_fields(self):
        result = ResearchAnalyzer(DeterministicProvider()).analyze(self.record)

        data = result.to_dict()
        self.assertNotIn("our_angle", data)
        self.assertNotIn("target_emotion", data)
        self.assertNotIn("hook", data)
        self.assertNotIn("cta", data)


if __name__ == "__main__":
    unittest.main()
