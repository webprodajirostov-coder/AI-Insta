from __future__ import annotations

from typing import Any, Mapping


class DomainValidationError(ValueError):
    """Raised when domain entities violate a cross-entity contract."""


def _require(entity: Mapping[str, Any], field: str, label: str) -> Any:
    value = entity.get(field)
    if value in (None, ""):
        raise DomainValidationError(f"{label} is missing required field: {field}")
    return value


def validate_account(account: Mapping[str, Any]) -> None:
    _require(account, "account_id", "Account")
    _require(account, "version", "Account")
    _require(account, "status", "Account")
    _require(account, "identity", "Account")
    _require(account, "audience", "Account")
    _require(account, "content_strategy", "Account")
    _require(account, "production_defaults", "Account")


def validate_knowledge(
    knowledge: Mapping[str, Any],
    *,
    account_id: str | None = None,
) -> None:
    knowledge_id = _require(knowledge, "knowledge_id", "Knowledge")
    if account_id is not None:
        actual_account_id = _require(knowledge, "account_id", "Knowledge")
        if actual_account_id != account_id:
            raise DomainValidationError(
                f"Knowledge {knowledge_id} belongs to account "
                f"{actual_account_id!r}, expected {account_id!r}"
            )


def validate_research_insight(
    insight: Mapping[str, Any],
    *,
    account_id: str | None = None,
) -> None:
    insight_id = _require(insight, "insight_id", "ResearchInsight")
    actual_account_id = _require(insight, "account_id", "ResearchInsight")

    if account_id is not None and actual_account_id != account_id:
        raise DomainValidationError(
            f"ResearchInsight {insight_id} belongs to account "
            f"{actual_account_id!r}, expected {account_id!r}"
        )

    _require(insight, "status", "ResearchInsight")
    _require(insight, "source", "ResearchInsight")
    _require(insight, "topic", "ResearchInsight")
    _require(insight, "observation", "ResearchInsight")
    _require(insight, "evidence", "ResearchInsight")
    _require(insight, "relevance", "ResearchInsight")
    _require(insight, "content_implications", "ResearchInsight")

    evidence = insight["evidence"]
    if not isinstance(evidence, list):
        raise DomainValidationError(
            f"ResearchInsight {insight_id} evidence must be a list"
        )

    implications = insight["content_implications"]
    if not isinstance(implications, list):
        raise DomainValidationError(
            f"ResearchInsight {insight_id} content_implications must be a list"
        )

    confidence = insight.get("confidence")
    if confidence is not None and (
        not isinstance(confidence, (int, float)) or isinstance(confidence, bool)
        or not 0 <= confidence <= 1
    ):
        raise DomainValidationError(
            f"ResearchInsight {insight_id} confidence must be between 0 and 1"
        )


def validate_content_idea(
    idea: Mapping[str, Any],
    *,
    account_id: str | None = None,
) -> None:
    idea_id = _require(idea, "idea_id", "ContentIdea")
    actual_account_id = _require(idea, "account_id", "ContentIdea")

    if account_id is not None and actual_account_id != account_id:
        raise DomainValidationError(
            f"ContentIdea {idea_id} belongs to account "
            f"{actual_account_id!r}, expected {account_id!r}"
        )

    _require(idea, "production", "ContentIdea")
    _require(idea["production"], "profile", "ContentIdea.production")


def validate_content_concept(
    concept: Mapping[str, Any],
    *,
    account_id: str | None = None,
    idea_id: str | None = None,
) -> None:
    concept_id = _require(concept, "concept_id", "ContentConcept")
    actual_account_id = _require(concept, "account_id", "ContentConcept")
    actual_idea_id = _require(concept, "idea_id", "ContentConcept")

    if account_id is not None and actual_account_id != account_id:
        raise DomainValidationError(
            f"ContentConcept {concept_id} belongs to account "
            f"{actual_account_id!r}, expected {account_id!r}"
        )

    if idea_id is not None and actual_idea_id != idea_id:
        raise DomainValidationError(
            f"ContentConcept {concept_id} belongs to idea "
            f"{actual_idea_id!r}, expected {idea_id!r}"
        )

    _require(concept, "production_profile", "ContentConcept")


def validate_scenario(
    scenario: Mapping[str, Any],
    *,
    account_id: str | None = None,
    concept_id: str | None = None,
) -> None:
    scenario_id = _require(scenario, "scenario_id", "Scenario")
    actual_account_id = _require(scenario, "account_id", "Scenario")
    actual_concept_id = _require(scenario, "concept_id", "Scenario")

    if account_id is not None and actual_account_id != account_id:
        raise DomainValidationError(
            f"Scenario {scenario_id} belongs to account "
            f"{actual_account_id!r}, expected {account_id!r}"
        )

    if concept_id is not None and actual_concept_id != concept_id:
        raise DomainValidationError(
            f"Scenario {scenario_id} belongs to concept "
            f"{actual_concept_id!r}, expected {concept_id!r}"
        )

    _require(scenario, "production_profile", "Scenario")


def validate_production_profile(profile: Mapping[str, Any]) -> None:
    profile_id = _require(profile, "profile_id", "ProductionProfile")
    _require(profile, "status", "ProductionProfile")
    visual = _require(profile, "visual", "ProductionProfile")
    _require(profile, "audio", "ProductionProfile")
    _require(profile, "text", "ProductionProfile")
    _require(profile, "editing", "ProductionProfile")
    _require(profile, "duration_seconds", "ProductionProfile")

    count = _require(visual, "count", f"ProductionProfile.visual ({profile_id})")
    if not isinstance(count, int) or count < 1:
        raise DomainValidationError(
            f"ProductionProfile {profile_id} visual.count must be a positive integer"
        )

    types = _require(visual, "types", f"ProductionProfile.visual ({profile_id})")
    if not isinstance(types, list) or not types:
        raise DomainValidationError(
            f"ProductionProfile {profile_id} visual.types must be a non-empty list"
        )

    duration = profile["duration_seconds"]
    if not isinstance(duration, Mapping):
        raise DomainValidationError(
            f"ProductionProfile {profile_id} duration_seconds must be an object"
        )

    minimum = _require(
        duration,
        "min",
        f"ProductionProfile.duration_seconds ({profile_id})",
    )
    maximum = _require(
        duration,
        "max",
        f"ProductionProfile.duration_seconds ({profile_id})",
    )

    if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
        raise DomainValidationError(
            f"ProductionProfile {profile_id} duration bounds must be numeric"
        )

    if minimum > maximum:
        raise DomainValidationError(
            f"ProductionProfile {profile_id} duration min cannot exceed max"
        )


def validate_knowledge_refs(
    entity: Mapping[str, Any],
    knowledge: Mapping[str, Any],
    *,
    label: str,
) -> None:
    refs = entity.get("knowledge_refs", [])
    if not isinstance(refs, list):
        raise DomainValidationError(f"{label}.knowledge_refs must be a list")

    known_ids: set[str] = set()
    for key in (
        "core_concepts",
        "audience_insights",
        "psychological_mechanisms",
        "content_pillars",
    ):
        for item in knowledge.get(key, []):
            if isinstance(item, Mapping) and item.get("id"):
                known_ids.add(item["id"])

    missing = [ref for ref in refs if ref not in known_ids]
    if missing:
        raise DomainValidationError(
            f"{label} references unknown Knowledge ids: {missing}"
        )


def validate_research_refs(
    entity: Mapping[str, Any],
    research_insights: Mapping[str, Mapping[str, Any]] | list[Mapping[str, Any]],
    *,
    label: str,
) -> None:
    refs = entity.get("research_refs", [])
    if not isinstance(refs, list):
        raise DomainValidationError(f"{label}.research_refs must be a list")

    if isinstance(research_insights, Mapping):
        known = research_insights
    else:
        known = {
            insight.get("insight_id"): insight
            for insight in research_insights
            if isinstance(insight, Mapping) and insight.get("insight_id")
        }

    missing = [ref for ref in refs if ref not in known]
    if missing:
        raise DomainValidationError(
            f"{label} references unknown ResearchInsight ids: {missing}"
        )


def validate_content_chain(
    *,
    account: Mapping[str, Any],
    knowledge: Mapping[str, Any],
    idea: Mapping[str, Any],
    concept: Mapping[str, Any],
    scenario: Mapping[str, Any],
    profile: Mapping[str, Any],
    research_insights: Mapping[str, Mapping[str, Any]]
    | list[Mapping[str, Any]]
    | None = None,
) -> None:
    account_id = _require(account, "account_id", "Account")
    idea_id = _require(idea, "idea_id", "ContentIdea")
    concept_id = _require(concept, "concept_id", "ContentConcept")
    profile_id = _require(profile, "profile_id", "ProductionProfile")

    validate_account(account)
    validate_knowledge(knowledge, account_id=account_id)
    validate_content_idea(idea, account_id=account_id)
    validate_content_concept(
        concept,
        account_id=account_id,
        idea_id=idea_id,
    )
    validate_scenario(
        scenario,
        account_id=account_id,
        concept_id=concept_id,
    )
    validate_production_profile(profile)

    idea_profile = idea["production"]["profile"]
    concept_profile = concept["production_profile"]
    scenario_profile = scenario["production_profile"]

    if not (
        idea_profile == concept_profile == scenario_profile == profile_id
    ):
        raise DomainValidationError(
            "ProductionProfile mismatch across ContentIdea, "
            "ContentConcept, Scenario and ProductionProfile: "
            f"{idea_profile!r}, {concept_profile!r}, "
            f"{scenario_profile!r}, {profile_id!r}"
        )

    content_pillars = account.get("content_strategy", {}).get("pillars", [])
    idea_pillar = idea.get("content_pillar")
    if idea_pillar and content_pillars and idea_pillar not in content_pillars:
        raise DomainValidationError(
            f"ContentIdea {idea_id} uses unknown account content pillar: "
            f"{idea_pillar!r}"
        )

    validate_knowledge_refs(idea, knowledge, label="ContentIdea")
    validate_knowledge_refs(concept, knowledge, label="ContentConcept")

    if research_insights is None:
        if idea.get("research_refs") or concept.get("research_refs"):
            raise DomainValidationError(
                "ResearchInsight references are present but research_insights "
                "were not provided for validation"
            )
    else:
        for insight in (
            research_insights.values()
            if isinstance(research_insights, Mapping)
            else research_insights
        ):
            validate_research_insight(insight, account_id=account_id)

        validate_research_refs(
            idea, research_insights, label="ContentIdea"
        )
        validate_research_refs(
            concept, research_insights, label="ContentConcept"
        )
