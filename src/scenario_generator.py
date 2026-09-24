from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Protocol, Sequence

from src.domain_validation import (
    DomainValidationError,
    validate_account,
    validate_content_concept,
    validate_production_profile,
    validate_scenario,
)


class ScenarioProvider(Protocol):
    def generate_scenarios(
        self,
        *,
        account: Mapping[str, Any],
        concept: Mapping[str, Any],
        production_profile: Mapping[str, Any],
    ) -> Sequence[Mapping[str, Any]]:
        ...


@dataclass(frozen=True)
class ScenarioGenerationResult:
    scenarios: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {"scenarios": list(self.scenarios)}


class ScenarioGenerator:
    """Generate production-ready Scenario contracts from a ContentConcept."""

    def __init__(self, provider: ScenarioProvider):
        self.provider = provider

    def generate(
        self,
        *,
        account: Mapping[str, Any],
        concept: Mapping[str, Any],
        production_profile: Mapping[str, Any],
    ) -> ScenarioGenerationResult:
        validate_account(account)
        account_id = account["account_id"]

        validate_content_concept(
            concept,
            account_id=account_id,
        )
        validate_production_profile(production_profile)

        profile_id = production_profile["profile_id"]
        if concept["production_profile"] != profile_id:
            raise DomainValidationError(
                f"ContentConcept {concept['concept_id']} uses "
                f"ProductionProfile {concept['production_profile']!r}, "
                f"expected {profile_id!r}"
            )

        scenarios = self.provider.generate_scenarios(
            account=account,
            concept=concept,
            production_profile=production_profile,
        )

        if isinstance(scenarios, (str, bytes)) or not isinstance(scenarios, Sequence):
            raise DomainValidationError(
                "Scenario provider must return a sequence of objects"
            )

        generated: list[dict[str, Any]] = []
        now = datetime.now().replace(microsecond=0).isoformat()

        for index, raw in enumerate(scenarios, start=1):
            if not isinstance(raw, Mapping):
                raise DomainValidationError(
                    f"Scenario provider item {index} must be an object"
                )

            scenario = dict(raw)
            scenario.setdefault("schema_version", 1)
            scenario.setdefault("entity", "Scenario")
            scenario.setdefault("scenario_id", f"scenario_{index:03d}")
            scenario.setdefault("account_id", account_id)
            scenario.setdefault("concept_id", concept["concept_id"])
            scenario.setdefault("production_profile", profile_id)
            scenario.setdefault("status", "draft")
            scenario.setdefault(
                "language",
                account.get("identity", {}).get("language", "en"),
            )
            scenario.setdefault("created_at", now)
            scenario.setdefault("updated_at", now)

            if scenario["account_id"] != account_id:
                raise DomainValidationError(
                    f"Scenario {scenario['scenario_id']} belongs to account "
                    f"{scenario['account_id']!r}, expected {account_id!r}"
                )

            if scenario["concept_id"] != concept["concept_id"]:
                raise DomainValidationError(
                    f"Scenario {scenario['scenario_id']} belongs to concept "
                    f"{scenario['concept_id']!r}, expected {concept['concept_id']!r}"
                )

            if scenario["production_profile"] != profile_id:
                raise DomainValidationError(
                    f"Scenario {scenario['scenario_id']} uses ProductionProfile "
                    f"{scenario['production_profile']!r}, expected {profile_id!r}"
                )

            validate_scenario(
                scenario,
                account_id=account_id,
                concept_id=concept["concept_id"],
                production_profile=production_profile,
            )
            generated.append(scenario)

        return ScenarioGenerationResult(tuple(generated))
