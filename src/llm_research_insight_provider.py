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
- source: object containing research_id, material_refs, and a source type/reference
- topic
- observation
- evidence: array
- relevance
- content_implications: array
- confidence: number from 0 to 1

For every ResearchInsight:
- source.research_id MUST identify the supplied Research record that supports the insight.
- source.material_refs MUST be a non-empty array of exact material.id values from that Research record.
- Base every observation and evidence item only on the referenced material records.
- Account context may inform relevance and content implications, but it must not be used as a source of facts.
- Do not add material ids, facts, sources, competitors, evidence, or URLs that are not present in the supplied Research.
- Preserve the distinction between observation and evidence. Do not present an inference as a verified fact.
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
                f"{[dict(item) for item in research]}\n\n"
                "IMPORTANT: source.material_refs must contain only exact material.id "
                "values from the referenced Research record. Do not invent or infer material ids."
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
