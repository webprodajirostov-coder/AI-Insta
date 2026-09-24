from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, Sequence

from src.domain_validation import (
    DomainValidationError,
    validate_account,
    validate_content_idea,
    validate_knowledge,
    validate_knowledge_refs,
    validate_research_insight,
    validate_research_refs,
)


class ContentIdeaProvider(Protocol):
    def generate_content_ideas(
        self,
        *,
        account: Mapping[str, Any],
        knowledge: Mapping[str, Any],
        research_insights: Sequence[Mapping[str, Any]],
    ) -> Sequence[Mapping[str, Any]]:
        ...


@dataclass(frozen=True)
class ContentIdeaGenerationResult:
    ideas: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {"ideas": [dict(idea) for idea in self.ideas]}


class ContentIdeaGenerator:
    """Generate domain-valid ContentIdea entities behind a pluggable provider."""

    _FORBIDDEN_CREATIVE_FIELDS = {
        "hook",
        "cta",
        "caption",
        "voiceover",
        "visual",
        "audio",
        "scenario",
        "scenes",
    }

    def __init__(self, provider: ContentIdeaProvider):
        self.provider = provider

    def generate(
        self,
        *,
        account: Mapping[str, Any],
        knowledge: Mapping[str, Any],
        research_insights: Sequence[Mapping[str, Any]],
    ) -> ContentIdeaGenerationResult:
        validate_account(account)
        account_id = account["account_id"]
        validate_knowledge(knowledge, account_id=account_id)

        insights = list(research_insights)
        for insight in insights:
            validate_research_insight(insight, account_id=account_id)

        generated = self.provider.generate_content_ideas(
            account=account,
            knowledge=knowledge,
            research_insights=insights,
        )

        if not isinstance(generated, Sequence) or isinstance(
            generated, (str, bytes, Mapping)
        ):
            raise DomainValidationError(
                "ContentIdea provider must return a sequence of ideas"
            )

        ideas: list[dict[str, Any]] = []
        for raw_idea in generated:
            if not isinstance(raw_idea, Mapping):
                raise DomainValidationError(
                    "ContentIdea provider returned a non-object idea"
                )

            forbidden = self._FORBIDDEN_CREATIVE_FIELDS.intersection(raw_idea)
            if forbidden:
                raise DomainValidationError(
                    "ContentIdea must not contain production/creative fields: "
                    f"{sorted(forbidden)}"
                )

            idea = dict(raw_idea)
            idea.setdefault("schema_version", 1)
            idea.setdefault("entity", "ContentIdea")
            idea.setdefault("status", "draft")
            idea.setdefault("created_at", self._now())
            idea.setdefault("updated_at", idea["created_at"])

            validate_content_idea(idea, account_id=account_id)
            validate_knowledge_refs(idea, knowledge, label="ContentIdea")

            if insights:
                validate_research_refs(
                    idea,
                    insights,
                    label="ContentIdea",
                )

            ideas.append(idea)

        return ContentIdeaGenerationResult(tuple(ideas))

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
