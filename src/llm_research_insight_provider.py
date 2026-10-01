from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.domain_validation import DomainValidationError
from src.llm_provider import LLMProvider


class LLMResearchInsightProvider:
    """ResearchInsight provider adapter backed by a generic structured LLM."""

    SYSTEM_PROMPT = """You are a research analyst for an account-aware content system.

Turn supplied Research records into concrete ResearchInsight objects.

Return ONLY a JSON array of ResearchInsight objects. Do not return markdown or commentary.

Each ResearchInsight must contain:
- insight_id
- source: object containing research_id and a source type/reference
- topic
- observation
- evidence: array
- relevance
- content_implications: array
- confidence: number from 0 to 1

Preserve the distinction between observation and evidence. Do not present an
inference as a verified fact. Use only supplied Research records and their
research_id values. Do not invent sources, competitors, evidence, or URLs.
Keep the output useful for later ContentIdea generation."""
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def generate_research_insights(
        self,
        *,
        account: Mapping[str, Any],
        research: Sequence[Mapping[str, Any]],
    ) -> Sequence[Mapping[str, Any]]:
        result = self.llm.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=(
                "ACCOUNT:\n"
                f"{dict(account)}\n\n"
                "RESEARCH:\n"
                f"{[dict(item) for item in research]}"
            ),
        )

        if isinstance(result, Mapping) and "research_insights" in result:
            insights = result["research_insights"]
        else:
            insights = result

        if isinstance(insights, (str, bytes, Mapping)) or not isinstance(
            insights, Sequence
        ):
            raise DomainValidationError(
                "LLMResearchInsightProvider must receive a sequence of insight objects"
            )

        return insights
