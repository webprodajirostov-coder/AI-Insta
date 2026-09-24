from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class ResearchAnalysisResult:
    research_id: str
    account_id: str
    summary: str
    patterns: list[str]
    observations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "research_id": self.research_id,
            "account_id": self.account_id,
            "summary": self.summary,
            "patterns": list(self.patterns),
            "observations": list(self.observations),
        }


class ResearchAnalysisProvider(Protocol):
    def analyze(self, research_record: Mapping[str, Any]) -> ResearchAnalysisResult:
        ...


class ResearchAnalyzer:
    def __init__(self, provider: ResearchAnalysisProvider) -> None:
        self.provider = provider

    def analyze(
        self,
        research_record: Mapping[str, Any],
        *,
        account_id: str | None = None,
    ) -> ResearchAnalysisResult:
        research_id = research_record.get("research_id")
        actual_account_id = research_record.get("account_id")

        if not research_id:
            raise ValueError("ResearchRecord is missing required field: research_id")
        if not actual_account_id:
            raise ValueError("ResearchRecord is missing required field: account_id")
        if account_id is not None and actual_account_id != account_id:
            raise ValueError(
                f"ResearchRecord {research_id} belongs to account "
                f"{actual_account_id!r}, expected {account_id!r}"
            )

        result = self.provider.analyze(research_record)

        if result.research_id != research_id:
            raise ValueError(
                "ResearchAnalysisResult research_id does not match ResearchRecord"
            )
        if result.account_id != actual_account_id:
            raise ValueError(
                "ResearchAnalysisResult account_id does not match ResearchRecord"
            )

        return result
