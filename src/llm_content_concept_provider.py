from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.domain_validation import DomainValidationError
from src.llm_provider import LLMProvider


class LLMContentConceptProvider:
    """ContentConceptProvider adapter backed by a generic structured LLM."""

    SYSTEM_PROMPT = """You are a creative strategist for an account-aware short-form content system.

Turn the supplied ContentIdea into one or more production-ready ContentConcept objects.

Return ONLY a JSON array of ContentConcept objects. Do not return markdown or commentary.

Each ContentConcept must contain:
- concept_id
- core_message
- problem
- reframe
- psychological_mechanism
- key_points: array
- hook
- emotional_direction
- audience_takeaway
- cta: object with type and text
- knowledge_refs
- research_refs
- production_profile

Keep ContentConcept above the media-production layer. Do NOT include:
caption, voiceover, visual, audio, scenario, or scenes.

Preserve the ContentIdea account_id and idea_id.
Preserve its knowledge_refs, research_refs, and production profile unless there is a clear validation-safe reason not to.
Use only references supplied by the input.
Do not invent research evidence or present a research observation as established fact."""
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def generate_content_concepts(
        self,
        *,
        account: Mapping[str, Any],
        knowledge: Mapping[str, Any],
        idea: Mapping[str, Any],
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
            "CONTENT IDEA:\n"
            f"{dict(idea)}\n\n"
            "RESEARCH INSIGHTS:\n"
            f"{[dict(item) for item in research_insights]}\n\n"
            "IMPORTANT: ids from hooks, content_patterns, messaging, or other "
            "Knowledge sections are not valid knowledge_refs. Preserve the "
            "ContentIdea knowledge_refs and use only the explicit VALID "
            "KNOWLEDGE_REF IDS list."
        )

        result = self.llm.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        if isinstance(result, Mapping) and "concepts" in result:
            concepts = result["concepts"]
        else:
            concepts = result

        if isinstance(concepts, (str, bytes, Mapping)) or not isinstance(
            concepts, Sequence
        ):
            raise DomainValidationError(
                "LLMContentConceptProvider must receive a sequence of concept objects"
            )

        return concepts
