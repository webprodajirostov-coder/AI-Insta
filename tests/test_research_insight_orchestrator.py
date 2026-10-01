import json
import tempfile
import unittest
from pathlib import Path

from src.domain_validation import DomainValidationError
from src.research_insight_generator import ResearchInsightGenerator
from src.research_insight_orchestrator import ResearchInsightOrchestrator


class StubProvider:
    def __init__(self, insights):
        self.insights = insights
        self.calls = 0

    def generate_research_insights(self, *, account, research):
        self.calls += 1
        return self.insights


class ResearchInsightOrchestratorTests(unittest.TestCase):
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
            "material": [{"id": "item_001", "type": "video", "content": "Pricing pattern."}],
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
            "evidence": ["Observed in supplied material."],
            "relevance": "Relevant.",
            "content_implications": ["Explore rejection avoidance."],
            "confidence": 0.8,
        }

    def _write(self, root, name, value):
        path = root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_loads_research_and_persists_insights(self):
        provider = StubProvider([self.insight])
        orchestrator = ResearchInsightOrchestrator(
            ResearchInsightGenerator(provider)
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_path = self._write(root, "account.json", self.account)
            research_path = self._write(root, "research.json", self.research)

            output = orchestrator.generate(
                account_path=account_path,
                research_paths=[research_path],
                output_path=root / "insights.json",
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["research_insights"][0]["insight_id"],
                "insight_001",
            )
            self.assertEqual(provider.calls, 1)

    def test_cross_account_research_is_rejected_before_provider_call(self):
        broken = dict(self.research, account_id="other_account")
        provider = StubProvider([self.insight])
        orchestrator = ResearchInsightOrchestrator(
            ResearchInsightGenerator(provider)
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_path = self._write(root, "account.json", self.account)
            research_path = self._write(root, "research.json", broken)

            with self.assertRaises(DomainValidationError):
                orchestrator.generate(
                    account_path=account_path,
                    research_paths=[research_path],
                    output_path=root / "insights.json",
                )

            self.assertEqual(provider.calls, 0)


if __name__ == "__main__":
    unittest.main()
