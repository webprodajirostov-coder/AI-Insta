import json
import tempfile
import unittest
from pathlib import Path

from src.domain_validation import DomainValidationError
from src.production_profile_store import ProductionProfileStore


ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class ProductionProfileStoreTests(unittest.TestCase):
    def setUp(self):
        self.account = load_json(
            ROOT / "data" / "accounts" / "sales_psychology_001" / "account.json"
        )
        self.store = ProductionProfileStore(
            ROOT / "data" / "production_profiles"
        )

    def test_loads_valid_profile(self):
        profile = self.store.load("simple")

        self.assertEqual(profile["profile_id"], "simple")
        self.assertEqual(profile["duration_seconds"], {"min": 6, "max": 10})

    def test_loads_all_supported_profiles(self):
        for profile_id in ("simple", "standard", "advanced"):
            profile = self.store.resolve_for_account(
                account=self.account,
                profile_id=profile_id,
            )
            self.assertEqual(profile["profile_id"], profile_id)

    def test_rejects_unknown_profile(self):
        with self.assertRaises(DomainValidationError):
            self.store.load("missing")

    def test_rejects_profile_file_with_mismatched_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "simple.json"
            profile = load_json(ROOT / "data" / "production_profiles" / "simple.json")
            profile["profile_id"] = "standard"
            path.write_text(json.dumps(profile), encoding="utf-8")

            with self.assertRaises(DomainValidationError):
                ProductionProfileStore(tmp).load("simple")

    def test_rejects_unsupported_account_profile(self):
        account = dict(self.account)
        defaults = dict(account["production_defaults"])
        defaults["supported_complexity_levels"] = ["simple"]
        account["production_defaults"] = defaults

        with self.assertRaises(DomainValidationError):
            self.store.resolve_for_account(
                account=account,
                profile_id="advanced",
            )

    def test_rejects_non_list_supported_levels(self):
        account = dict(self.account)
        defaults = dict(account["production_defaults"])
        defaults["supported_complexity_levels"] = "simple"
        account["production_defaults"] = defaults

        with self.assertRaises(DomainValidationError):
            self.store.resolve_for_account(
                account=account,
                profile_id="simple",
            )
