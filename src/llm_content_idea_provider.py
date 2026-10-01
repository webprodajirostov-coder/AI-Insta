from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.domain_validation import DomainValidationError
from src.llm_provider import LLMProvider


class LLMContentIdeaProvider:
    """ContentIdeaProvider adapter backed by a generic structured LLM."""

    SYSTEM_PROMPT = """You are a content strategist for an account-aware short-form content system.

Generate exactly one ContentIdea object from the supplied Account, Knowledge, and optional ResearchInsight objects.

Return ONLY a JSON array containing exactly one ContentIdea object. Do not return markdown or commentary.

Each ContentIdea must contain:
- idea_id
- account_id
- status
- source: object with type and source_ids
- topic
- content_pillar
- funnel_stage
- angle
- audience_problem
- audience_desire
- hook_direction
- why_now
- knowledge_refs: ids that exist in the supplied Knowledge
- research_refs: ids that exist in the supplied ResearchInsight list, or [] when no research is supplied
- production: object with profile

Keep ContentIdea at the strategy/idea level. Do NOT include:
hook, cta, caption, voiceover, visual, audio, scenario, or scenes.

Use only the supplied account_id, knowledge ids, research ids, and account content pillars.
The production profile must be compatible with the account's baseline production format.
Do not invent research references.
Do not turn research observations into established facts; preserve them as content inputs."""
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def generate_content_ideas(
        self,
        *,
        account: Mapping[str, Any],
        knowledge: Mapping[str, Any],
        research_insights: Sequence[Mapping[str, Any]],
    ) -> Sequence[Mapping[str, Any]]:
        valid_knowledge_ref_ids = [
            item["id"]
            for key in (
                "core_concepts",
                "audience_insights",
                "psychological_mechanisms",
                "content_pillars",
            )
            for item in knowledge.get(key, [])
            if isinstance(item, Mapping) and item.get("id")
        ]

        user_prompt = (
            "ACCOUNT:\n"
            f"{dict(account)}\n\n"
            "VALID KNOWLEDGE_REF IDS (use only these in knowledge_refs):\n"
            f"{valid_knowledge_ref_ids}\n\n"
            "KNOWLEDGE:\n"
            f"{dict(knowledge)}\n\n"
            "RESEARCH INSIGHTS:\n"
            f"{[dict(item) for item in research_insights]}\n\n"
            "IMPORTANT: ids from hooks, content_patterns, messaging, or other "
            "Knowledge sections are not valid knowledge_refs. Use only the "
            "explicit VALID KNOWLEDGE_REF IDS list."
        )

        result = self.llm.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        if isinstance(result, Mapping) and "ideas" in result:
            ideas = result["ideas"]
        else:
            ideas = result

        if isinstance(ideas, (str, bytes, Mapping)) or not isinstance(
            ideas, Sequence
        ):
            raise DomainValidationError(
                "LLMContentIdeaProvider must receive a sequence of idea objects"
            )

        return ideas
