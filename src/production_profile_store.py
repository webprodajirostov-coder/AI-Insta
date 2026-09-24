from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.domain_validation import (
    DomainValidationError,
    validate_account,
    validate_production_profile,
)


class ProductionProfileStore:
    """Load validated static ProductionProfile definitions."""

    def __init__(self, profiles_dir: str | Path):
        self.profiles_dir = Path(profiles_dir)

    def load(self, profile_id: str) -> dict[str, Any]:
        if not profile_id:
            raise DomainValidationError("ProductionProfile id is required")

        path = self.profiles_dir / f"{profile_id}.json"
        if not path.is_file():
            raise DomainValidationError(
                f"ProductionProfile {profile_id!r} does not exist"
            )

        try:
            profile = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DomainValidationError(
                f"ProductionProfile {profile_id!r} could not be loaded"
            ) from exc

        if not isinstance(profile, Mapping):
            raise DomainValidationError(
                f"ProductionProfile {profile_id!r} must be an object"
            )

        validate_production_profile(profile)

        actual_id = profile["profile_id"]
        if actual_id != profile_id:
            raise DomainValidationError(
                f"ProductionProfile file {path.name!r} contains id "
                f"{actual_id!r}, expected {profile_id!r}"
            )

        return dict(profile)

    def resolve_for_account(
        self,
        *,
        account: Mapping[str, Any],
        profile_id: str,
    ) -> dict[str, Any]:
        validate_account(account)
        profile = self.load(profile_id)

        supported = account["production_defaults"].get(
            "supported_complexity_levels",
            [],
        )
        if not isinstance(supported, list):
            raise DomainValidationError(
                "Account production_defaults.supported_complexity_levels "
                "must be a list"
            )

        if profile_id not in supported:
            raise DomainValidationError(
                f"ProductionProfile {profile_id!r} is not supported by "
                f"Account {account['account_id']!r}"
            )

        return profile
