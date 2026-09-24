from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, Sequence

from src.domain_validation import (
    DomainValidationError,
    validate_account,
    validate_content_concept,
    validate_content_idea,
    validate_knowledge,
    validate_knowledge_refs,
    validate_research_insight,
    validate_research_refs,
)


class ContentConceptProvider(Protocol):
    def generate_content_concepts(
        self,
        *,
        account: Mapping[str, Any],
        knowledge: Mapping[str, Any],
        idea: Mapping[str, Any],
        research_insights: Sequence[Mapping[str, Any]],
    ) -> Sequence[Mapping[str, Any]]:
        ...


@dataclass(frozen=True)
class ContentConceptGenerationResult:
    concepts: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {"concepts": [dict(concept) for concept in self.concepts]}


class ContentConceptGenerator:
    """Generate domain-valid ContentConcept entities behind a pluggable provider."""

    _FORBIDDEN_PRODUCTION_FIELDS = {
        "caption",
        "voiceover",
        "visual",
        "audio",
        "scenario",
        "scenes",
    }

    def __init__(self, provider: ContentConceptProvider):
        self.provider = provider

    def generate(
        self,
        *,
        account: Mapping[str, Any],
        knowledge: Mapping[str, Any],
        idea: Mapping[str, Any],
        research_insights: Sequence[Mapping[str, Any]],
    ) -> ContentConceptGenerationResult:
        validate_account(account)
        account_id = account["account_id"]
        validate_knowledge(knowledge, account_id=account_id)
        validate_content_idea(idea, account_id=account_id)
        validate_knowledge_refs(idea, knowledge, label="ContentIdea")

        insights = list(research_insights)
        for insight in insights:
            validate_research_insight(insight, account_id=account_id)

        if insights:
            validate_research_refs(idea, insights, label="ContentIdea")
            if not idea["research_refs"]:
                raise DomainValidationError(
                    f"ContentIdea {idea['idea_id']} must reference at least one "
                    "ResearchInsight when research insights are provided"
                )

        generated = self.provider.generate_content_concepts(
            account=account,
            knowledge=knowledge,
            idea=idea,
            research_insights=insights,
        )

        if not isinstance(generated, Sequence) or isinstance(
            generated, (str, bytes, Mapping)
        ):
            raise DomainValidationError(
                "ContentConcept provider must return a sequence of concepts"
            )

        concepts: list[dict[str, Any]] = []
        for raw_concept in generated:
            if not isinstance(raw_concept, Mapping):
                raise DomainValidationError(
                    "ContentConcept provider returned a non-object concept"
                )

            forbidden = self._FORBIDDEN_PRODUCTION_FIELDS.intersection(raw_concept)
            if forbidden:
                raise DomainValidationError(
                    "ContentConcept must not contain production/media fields: "
                    f"{sorted(forbidden)}"
                )

            concept = dict(raw_concept)
            concept.setdefault("schema_version", 1)
            concept.setdefault("entity", "ContentConcept")
            concept.setdefault("status", "draft")
            concept.setdefault("account_id", account_id)
            concept.setdefault("idea_id", idea["idea_id"])
            concept.setdefault("knowledge_refs", list(idea["knowledge_refs"]))
            concept.setdefault("research_refs", list(idea["research_refs"]))
            concept.setdefault(
                "production_profile",
                idea["production"]["profile"],
            )
            concept.setdefault("created_at", self._now())
            concept.setdefault("updated_at", concept["created_at"])

            validate_content_concept(
                concept,
                account_id=account_id,
                idea_id=idea["idea_id"],
            )
            validate_knowledge_refs(concept, knowledge, label="ContentConcept")

            if insights:
                validate_research_refs(
                    concept,
                    insights,
                    label="ContentConcept",
                )
                if not concept["research_refs"]:
                    raise DomainValidationError(
                        f"ContentConcept {concept['concept_id']} must reference at least "
                        "one ResearchInsight when research insights are provided"
                    )

            if concept["production_profile"] != idea["production"]["profile"]:
                raise DomainValidationError(
                    f"ContentConcept {concept['concept_id']} production_profile "
                    "must match ContentIdea production profile"
                )

            concepts.append(concept)

        return ContentConceptGenerationResult(tuple(concepts))

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
