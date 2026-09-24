import tempfile
import unittest
from pathlib import Path

from src.domain_validation import DomainValidationError
from src.research_store import (
    load_research_directory,
    load_research_insight,
    load_research_record,
)


class ResearchStoreTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self):
        for path in sorted(self.root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        self.root.rmdir()

    def write(self, name, data):
        path = self.root / name
        path.write_text(data, encoding="utf-8")
        return path

    def test_loads_research_record_for_account(self):
        path = self.write(
            "research.json",
            """{
                "entity": "ResearchRecord",
                "research_id": "research_001",
                "account_id": "sales_psychology_001",
                "status": "completed",
                "source": {"type": "competitor_video"},
                "raw_material": "raw",
                "analysis": {"summary": "summary", "patterns": []}
            }""",
        )

        record = load_research_record(
            path,
            account_id="sales_psychology_001",
        )

        self.assertEqual(record["research_id"], "research_001")

    def test_rejects_cross_account_record(self):
        path = self.write(
            "research.json",
            """{
                "entity": "ResearchRecord",
                "research_id": "research_001",
                "account_id": "sales_psychology_001",
                "status": "completed",
                "source": {"type": "competitor_video"},
                "raw_material": "raw",
                "analysis": {"summary": "summary", "patterns": []}
            }""",
        )

        with self.assertRaises(DomainValidationError):
            load_research_record(path, account_id="other_account")

    def test_loads_and_validates_research_insight(self):
        path = self.write(
            "insight.json",
            """{
                "entity": "ResearchInsight",
                "insight_id": "insight_001",
                "account_id": "sales_psychology_001",
                "status": "ready",
                "source": {"type": "competitor_video"},
                "topic": "pricing",
                "observation": "rejection avoidance",
                "evidence": ["evidence"],
                "relevance": "relevant",
                "content_implications": ["implication"],
                "confidence": 0.8
            }""",
        )

        insight = load_research_insight(
            path,
            account_id="sales_psychology_001",
        )

        self.assertEqual(insight["insight_id"], "insight_001")

    def test_loads_records_and_insights_from_directory(self):
        self.write(
            "research.json",
            """{
                "entity": "ResearchRecord",
                "research_id": "research_001",
                "account_id": "sales_psychology_001",
                "status": "completed",
                "source": {"type": "competitor_video"},
                "raw_material": "raw",
                "analysis": {"summary": "summary", "patterns": []}
            }""",
        )
        self.write(
            "insight.json",
            """{
                "entity": "ResearchInsight",
                "insight_id": "insight_001",
                "account_id": "sales_psychology_001",
                "status": "ready",
                "source": {"type": "competitor_video"},
                "topic": "pricing",
                "observation": "rejection avoidance",
                "evidence": ["evidence"],
                "relevance": "relevant",
                "content_implications": ["implication"],
                "confidence": 0.8
            }""",
        )

        loaded = load_research_directory(
            self.root,
            account_id="sales_psychology_001",
        )

        self.assertEqual(
            set(loaded),
            {"research_001", "insight_001"},
        )

    def test_directory_rejects_cross_account_insight(self):
        self.write(
            "insight.json",
            """{
                "entity": "ResearchInsight",
                "insight_id": "insight_001",
                "account_id": "other_account",
                "status": "ready",
                "source": {"type": "competitor_video"},
                "topic": "pricing",
                "observation": "rejection avoidance",
                "evidence": ["evidence"],
                "relevance": "relevant",
                "content_implications": ["implication"],
                "confidence": 0.8
            }""",
        )

        with self.assertRaises(DomainValidationError):
            load_research_directory(
                self.root,
                account_id="sales_psychology_001",
            )


if __name__ == "__main__":
    unittest.main()
