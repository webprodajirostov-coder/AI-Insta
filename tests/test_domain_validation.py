import json
import tempfile
import unittest
from pathlib import Path

from src.domain_validation import DomainValidationError, validate_content_chain
from src.job_creator import create_job


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
    def test_job_creator_validates_and_creates_isolated_job(self):
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


if __name__ == "__main__":
    unittest.main()
