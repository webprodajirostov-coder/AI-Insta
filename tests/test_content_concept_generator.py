import unittest
from pathlib import Path
import json

from src.content_concept_generator import ContentConceptGenerator
from src.domain_validation import DomainValidationError


ROOT = Path(__file__).resolve().parents[1]


class StubProvider:
    def __init__(self, concepts):
        self.concepts = concepts

    def generate_content_concepts(self, **kwargs):
        return self.concepts


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class ContentConceptGeneratorTests(unittest.TestCase):
    def setUp(self):
        account_dir = ROOT / "data" / "accounts" / "sales_psychology_001"
        self.account = load_json(account_dir / "account.json")
        self.knowledge = load_json(account_dir / "knowledge.json")
        self.idea = load_json(ROOT / "data" / "ideas" / "content_idea_001.json")

        self.base_concept = {
            "concept_id": "concept_test",
            "core_message": "Undercharging can protect against rejection.",
            "problem": "The expert lowers price before being asked.",
            "reframe": "Pricing can be emotionally safer than it feels.",
            "psychological_mechanism": "rejection_avoidance",
            "key_points": ["Notice the emotion before naming the price."],
            "hook": "You might not be undercharging because you're modest.",
            "emotional_direction": "recognition to reflection",
            "audience_takeaway": "Notice what happens in your body before naming your price.",
            "cta": {"type": "none", "text": ""},
        }

    def _generate(self, concepts=None, insights=None):
        provider = StubProvider(concepts or [self.base_concept])
        return ContentConceptGenerator(provider).generate(
            account=self.account,
            knowledge=self.knowledge,
            idea=self.idea,
            research_insights=insights or [],
        )

    def test_generates_valid_concept_from_idea(self):
        result = self._generate()
        concept = result.concepts[0]

        self.assertEqual(concept["account_id"], self.account["account_id"])
        self.assertEqual(concept["idea_id"], self.idea["idea_id"])
        self.assertEqual(concept["knowledge_refs"], self.idea["knowledge_refs"])
        self.assertEqual(
            concept["production_profile"],
            self.idea["production"]["profile"],
        )

    def test_rejects_cross_account_idea(self):
        broken = dict(self.idea)
        broken["account_id"] = "other_account"

        with self.assertRaises(DomainValidationError):
            ContentConceptGenerator(StubProvider([self.base_concept])).generate(
                account=self.account,
                knowledge=self.knowledge,
                idea=broken,
                research_insights=[],
            )

    def test_rejects_provider_non_object(self):
        with self.assertRaises(DomainValidationError):
            self._generate(concepts=[["invalid"]])

    def test_rejects_production_fields(self):
        broken = dict(self.base_concept)
        broken["voiceover"] = "Narration"

        with self.assertRaises(DomainValidationError):
            self._generate([broken])

    def test_rejects_profile_mismatch(self):
        broken = dict(self.base_concept)
        broken["production_profile"] = "advanced"

        with self.assertRaises(DomainValidationError):
            self._generate([broken])

    def test_rejects_unknown_knowledge_reference(self):
        broken = dict(self.base_concept)
        broken["knowledge_refs"] = ["missing_ref"]

        with self.assertRaises(DomainValidationError):
            self._generate([broken])

    def test_rejects_unknown_research_reference(self):
        insight = {
            "insight_id": "insight_001",
            "account_id": self.account["account_id"],
            "status": "ready",
            "source": {"type": "competitor_video", "reference": "video_001"},
            "topic": "pricing objections",
            "observation": "Pricing fear can be framed through rejection avoidance.",
            "evidence": ["Repeated pattern."],
            "relevance": "Useful for pricing anxiety content.",
            "content_implications": ["Explore rejection avoidance."],
            "confidence": 0.8,
        }
        idea = dict(self.idea)
        idea["research_refs"] = ["missing_insight"]

        with self.assertRaises(DomainValidationError):
            ContentConceptGenerator(StubProvider([self.base_concept])).generate(
                account=self.account,
                knowledge=self.knowledge,
                idea=idea,
                research_insights=[insight],
            )

    def test_research_refs_propagate_from_idea(self):
        insight = {
            "insight_id": "insight_001",
            "account_id": self.account["account_id"],
            "status": "ready",
            "source": {"type": "competitor_video", "reference": "video_001"},
            "topic": "pricing objections",
            "observation": "Pricing fear can be framed through rejection avoidance.",
            "evidence": ["Repeated pattern."],
            "relevance": "Useful for pricing anxiety content.",
            "content_implications": ["Explore rejection avoidance."],
            "confidence": 0.8,
        }
        idea = dict(self.idea)
        idea["research_refs"] = ["insight_001"]

        result = ContentConceptGenerator(StubProvider([self.base_concept])).generate(
            account=self.account,
            knowledge=self.knowledge,
            idea=idea,
            research_insights=[insight],
        )

        self.assertEqual(result.concepts[0]["research_refs"], ["insight_001"])

    def test_rejects_concept_for_different_idea(self):
        broken = dict(self.base_concept)
        broken["idea_id"] = "idea_other"

        with self.assertRaises(DomainValidationError):
            self._generate([broken])
