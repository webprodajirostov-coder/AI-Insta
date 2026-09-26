import json
import tempfile
import unittest
from pathlib import Path

from src.domain_validation import DomainValidationError, validate_content_chain
from src.job_service import create_job


ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class DomainValidationTests(unittest.TestCase):
    def setUp(self):
        account_dir = ROOT / "data" / "accounts" / "sales_psychology_001"
        self.account = load_json(account_dir / "account.json")
        self.knowledge = load_json(account_dir / "knowledge.json")
        self.idea = load_json(ROOT / "data" / "ideas" / "content_idea_001.json")
        self.concept = load_json(
            ROOT / "data" / "ideas" / "content_concept_001.json"
        )
        self.scenario = load_json(
            ROOT / "data" / "scenarios" / "scenario_001.json"
        )
        self.profile = load_json(
            ROOT / "data" / "production_profiles" / "simple.json"
        )

    def test_valid_content_chain(self):
        validate_content_chain(
            account=self.account,
            knowledge=self.knowledge,
            idea=self.idea,
            concept=self.concept,
            scenario=self.scenario,
            profile=self.profile,
        )

    def test_validates_scenario_v2_content_chain(self):
        scenario = dict(self.scenario)
        for field in ("visual", "text_overlay", "audio", "subtitles"):
            scenario.pop(field, None)

        scenario.update(
            {
                "schema_version": 2,
                "scenes": [
                    {
                        "scene_id": "scene_001",
                        "order": 1,
                        "duration_seconds": 8,
                        "voiceover_text": "",
                        "visual": {
                            "type": "image",
                            "generation_required": True,
                            "prompt_en": "Test visual prompt",
                        },
                        "text_overlay": None,
                        "subtitles": None,
                    }
                ],
                "duration_seconds": 8,
                "assembly": {
                    "transitions": False,
                    "animation": "minimal",
                },
            }
        )

        validate_content_chain(
            account=self.account,
            knowledge=self.knowledge,
            idea=self.idea,
            concept=self.concept,
            scenario=scenario,
            profile=self.profile,
        )

    def test_rejects_cross_account_concept(self):
        broken = dict(self.concept)
        broken["account_id"] = "other_account"

        with self.assertRaises(DomainValidationError):
            validate_content_chain(
                account=self.account,
                knowledge=self.knowledge,
                idea=self.idea,
                concept=broken,
                scenario=self.scenario,
                profile=self.profile,
            )

    def test_rejects_profile_mismatch(self):
        broken = dict(self.scenario)
        broken["production_profile"] = "advanced"

        with self.assertRaises(DomainValidationError):
            validate_content_chain(
                account=self.account,
                knowledge=self.knowledge,
                idea=self.idea,
                concept=self.concept,
                scenario=broken,
                profile=self.profile,
            )

    def test_rejects_scenario_visual_count_outside_profile(self):
        scenario = dict(self.scenario)
        for field in ("visual", "text_overlay", "audio", "subtitles"):
            scenario.pop(field, None)

        scenario.update(
            {
                "schema_version": 2,
                "scenes": [
                    {
                        "scene_id": "scene_001",
                        "order": 1,
                        "duration_seconds": 20,
                        "voiceover_text": "Test voiceover",
                        "visual": {
                            "type": "image",
                            "generation_required": True,
                            "prompt_en": "Test visual prompt",
                        },
                        "text_overlay": None,
                        "subtitles": None,
                    },
                ],
                "duration_seconds": 20,
                "assembly": {
                    "transitions": True,
                    "animation": "moderate",
                },
            }
        )

        standard = load_json(
            ROOT / "data" / "production_profiles" / "standard.json"
        )
        scenario["production_profile"] = "standard"

        with self.assertRaises(DomainValidationError):
            validate_content_chain(
                account=self.account,
                knowledge=self.knowledge,
                idea=dict(self.idea, production={"profile": "standard"}),
                concept=dict(self.concept, production_profile="standard"),
                scenario=scenario,
                profile=standard,
            )

    def test_rejects_non_mapping_subtitles_when_profile_requires_them(self):
        scenario = dict(self.scenario)
        for field in ("visual", "text_overlay", "audio", "subtitles"):
            scenario.pop(field, None)

        standard = load_json(
            ROOT / "data" / "production_profiles" / "standard.json"
        )
        scenario.update(
            {
                "schema_version": 2,
                "production_profile": "standard",
                "scenes": [
                    {
                        "scene_id": "scene_001",
                        "order": 1,
                        "duration_seconds": 20,
                        "voiceover_text": "Pricing fear is often about rejection.",
                        "visual": {
                            "type": "image",
                            "generation_required": True,
                            "prompt_en": "Test visual prompt",
                        },
                        "text_overlay": None,
                        "subtitles": "invalid",
                    },
                    {
                        "scene_id": "scene_002",
                        "order": 2,
                        "duration_seconds": 5,
                        "voiceover_text": "You can work with that fear.",
                        "visual": {
                            "type": "image",
                            "generation_required": True,
                            "prompt_en": "Test visual prompt",
                        },
                        "text_overlay": None,
                        "subtitles": {},
                    },
                ],
                "duration_seconds": 25,
                "assembly": {
                    "transitions": True,
                    "animation": "moderate",
                },
            }
        )

        with self.assertRaises(DomainValidationError):
            validate_content_chain(
                account=self.account,
                knowledge=self.knowledge,
                idea=dict(self.idea, production={"profile": "standard"}),
                concept=dict(self.concept, production_profile="standard"),
                scenario=scenario,
                profile=standard,
            )

    def test_rejects_unknown_knowledge_reference(self):
        broken = dict(self.idea)
        broken["knowledge_refs"] = list(self.idea["knowledge_refs"]) + ["missing_ref"]

        with self.assertRaises(DomainValidationError):
            validate_content_chain(
                account=self.account,
                knowledge=self.knowledge,
                idea=broken,
                concept=self.concept,
                scenario=self.scenario,
                profile=self.profile,
            )


class JobCreatorDomainIntegrationTests(unittest.TestCase):
    def test_job_service_validates_and_creates_isolated_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = create_job(
                ROOT / "data" / "ideas" / "content_idea_001.json",
                ROOT / "data" / "ideas" / "content_concept_001.json",
                ROOT / "data" / "scenarios" / "scenario_001.json",
                ROOT / "data" / "production_profiles" / "simple.json",
                jobs_root=Path(tmp),
            )

            self.assertTrue((job_dir / "job.json").exists())
            self.assertTrue(
                (job_dir / "input" / "content_idea.json").exists()
            )
            self.assertTrue(
                (job_dir / "content" / "content_concept.json").exists()
            )
            self.assertTrue(
                (job_dir / "content" / "scenario.json").exists()
            )


class ResearchReferenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        DomainValidationTests.setUp(self)

    def _validate(self, idea, concept, research_insights):
        validate_content_chain(
            account=self.account,
            knowledge=self.knowledge,
            idea=idea,
            concept=concept,
            scenario=self.scenario,
            profile=self.profile,
            research_insights=research_insights,
        )

    def test_accepts_valid_research_reference(self):
        insight = {
            "insight_id": "insight_001",
            "account_id": "sales_psychology_001",
            "status": "ready",
            "source": {"type": "competitor_video", "reference": "video_001"},
            "topic": "pricing objections",
            "observation": "Pricing fear is often framed through rejection avoidance.",
            "evidence": ["Repeated pattern in analyzed source material."],
            "relevance": "Useful for pricing anxiety content.",
            "content_implications": ["Explore rejection avoidance as a content angle."],
            "confidence": 0.8,
        }
        idea = dict(self.idea)
        idea["research_refs"] = ["insight_001"]

        self._validate(idea, self.concept, {"insight_001": insight})

    def test_rejects_unknown_research_reference(self):
        idea = dict(self.idea)
        idea["research_refs"] = ["missing_insight"]

        with self.assertRaises(DomainValidationError):
            self._validate(idea, self.concept, {})

    def test_rejects_cross_account_research_insight(self):
        insight = {
            "insight_id": "insight_001",
            "account_id": "other_account",
            "status": "ready",
            "source": {"type": "competitor_video", "reference": "video_001"},
            "topic": "pricing objections",
            "observation": "Pricing fear is often framed through rejection avoidance.",
            "evidence": ["Repeated pattern in analyzed source material."],
            "relevance": "Useful for pricing anxiety content.",
            "content_implications": ["Explore rejection avoidance as a content angle."],
            "confidence": 0.8,
        }
        concept = dict(self.concept)
        concept["research_refs"] = ["insight_001"]

        with self.assertRaises(DomainValidationError):
            self._validate(self.idea, concept, {"insight_001": insight})


if __name__ == "__main__":
    unittest.main()
