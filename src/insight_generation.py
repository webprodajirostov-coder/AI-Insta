from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from src.domain_validation import (
    validate_account,
    validate_knowledge,
    validate_research_analysis,
    validate_research_insight,
)
from src.research_analysis import ResearchAnalysisResult


@dataclass(frozen=True)
class ResearchInsight:
    insight_id: str
    account_id: str
    status: str
    source: dict[str, Any]
    topic: str
    observation: str
    evidence: list[str]
    relevance: str
    content_implications: list[str]
    confidence: float
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "entity": "ResearchInsight",
            "insight_id": self.insight_id,
            "account_id": self.account_id,
            "status": self.status,
            "source": dict(self.source),
            "topic": self.topic,
            "observation": self.observation,
            "evidence": list(self.evidence),
            "relevance": self.relevance,
            "content_implications": list(self.content_implications),
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class InsightGenerationProvider(Protocol):
    def generate(
        self,
        research_record: Mapping[str, Any],
        analysis_result: ResearchAnalysisResult,
        account: Mapping[str, Any],
        knowledge: Mapping[str, Any],
    ) -> list[Mapping[str, Any]]:
        ...


class InsightGenerator:
    def __init__(self, provider: InsightGenerationProvider) -> None:
        self.provider = provider

    def generate(
        self,
        research_record: Mapping[str, Any],
        analysis_result: ResearchAnalysisResult,
        account: Mapping[str, Any],
        knowledge: Mapping[str, Any],
    ) -> list[ResearchInsight]:
        research_id = research_record.get("research_id")
        research_account_id = research_record.get("account_id")
        account_id = account.get("account_id")

        if not research_id:
            raise ValueError("ResearchRecord is missing required field: research_id")

        if not research_account_id:
            raise ValueError("ResearchRecord is missing required field: account_id")

        if not account_id:
            raise ValueError("Account is missing required field: account_id")

        if research_account_id != account_id:
            raise ValueError(
                f"ResearchRecord {research_id} belongs to account "
                f"{research_account_id!r}, expected {account_id!r}"
            )

        validate_account(account)
        validate_knowledge(knowledge, account_id=account_id)
        validate_research_analysis(
            analysis_result.to_dict(),
            research_id=research_id,
            account_id=account_id,
        )

        candidates = self.provider.generate(
            research_record,
            analysis_result,
            account,
            knowledge,
        )

        insights: list[ResearchInsight] = []

        for candidate in candidates:
            validate_research_insight(
                candidate,
                account_id=account_id,
            )

            insight = ResearchInsight(
                insight_id=str(candidate["insight_id"]),
                account_id=str(candidate["account_id"]),
                status=str(candidate["status"]),
                source=dict(candidate["source"]),
                topic=str(candidate["topic"]),
                observation=str(candidate["observation"]),
                evidence=list(candidate["evidence"]),
                relevance=str(candidate["relevance"]),
                content_implications=list(candidate["content_implications"]),
                confidence=float(candidate["confidence"]),
                created_at=str(candidate.get("created_at", "")),
                updated_at=str(candidate.get("updated_at", "")),
            )

            validate_research_insight(
                insight.to_dict(),
                account_id=account_id,
            )

            if insight.source.get("reference") != research_id:
                raise ValueError(
                    f"ResearchInsight {insight.insight_id} source does not "
                    f"reference ResearchRecord {research_id}"
                )

            insights.append(insight)

        return insights
