from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, Sequence

from src.domain_validation import (
    DomainValidationError,
    validate_account,
    validate_research,
    validate_research_insight,
)


class ResearchInsightProvider(Protocol):
    def generate_research_insights(
        self,
        *,
        account: Mapping[str, Any],
        research: Sequence[Mapping[str, Any]],
    ) -> Sequence[Mapping[str, Any]]:
        ...


@dataclass(frozen=True)
class ResearchInsightGenerationResult:
    insights: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {"research_insights": [dict(item) for item in self.insights]}


class ResearchInsightGenerator:
    """Normalize raw Research material into account-scoped ResearchInsights."""

    def __init__(self, provider: ResearchInsightProvider):
        self.provider = provider

    def generate(
        self,
        *,
        account: Mapping[str, Any],
        research: Sequence[Mapping[str, Any]],
    ) -> ResearchInsightGenerationResult:
        validate_account(account)
        account_id = account["account_id"]

        sources = list(research)
        for item in sources:
            validate_research(item, account_id=account_id)

        generated = self.provider.generate_research_insights(
            account=account,
            research=sources,
        )

        if not isinstance(generated, Sequence) or isinstance(
            generated, (str, bytes, Mapping)
        ):
            raise DomainValidationError(
                "ResearchInsight provider must return a sequence of insights"
            )

        insights: list[dict[str, Any]] = []
        research_ids = {item["research_id"] for item in sources}

        for raw_insight in generated:
            if not isinstance(raw_insight, Mapping):
                raise DomainValidationError(
                    "ResearchInsight provider returned a non-object insight"
                )

            insight = dict(raw_insight)
            insight.setdefault("schema_version", 1)
            insight.setdefault("entity", "ResearchInsight")
            insight.setdefault("status", "ready")
            insight.setdefault("account_id", account_id)
            insight.setdefault("created_at", self._now())
            insight.setdefault("updated_at", insight["created_at"])

            source = insight.get("source")
            if not isinstance(source, Mapping):
                raise DomainValidationError(
                    "ResearchInsight source must be an object"
                )

            source_research_id = source.get("research_id")
            if source_research_id not in research_ids:
                raise DomainValidationError(
                    f"ResearchInsight {insight.get('insight_id', '<unknown>')} "
                    "must reference one of the supplied Research records"
                )

            validate_research_insight(insight, account_id=account_id)
            insights.append(insight)

        return ResearchInsightGenerationResult(tuple(insights))

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
