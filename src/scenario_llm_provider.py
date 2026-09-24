from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.domain_validation import DomainValidationError
from src.llm_provider import LLMProvider


class LLMScenarioProvider:
    """ScenarioProvider adapter backed by a generic structured LLM provider."""

    SYSTEM_PROMPT = """You are a lead video strategist for short-form video in sales psychology and personal transformation.

Turn the provided ContentConcept into one or more production-ready Scenario objects.

Return ONLY a JSON array of Scenario objects. Do not return markdown or commentary.

Each object must follow the current Scenario v1 contract:
- title: short English title
- hook: concise English hook
- caption: short English caption
- visual: object with type, generation_required, prompt_en
- text_overlay: object with text, position, animation
- audio: object with tts and music
- subtitles: object with enabled
- duration_seconds: positive number within the supplied ProductionProfile bounds
- assembly: object with transitions (boolean) and animation (string)

Use JSON primitive types exactly: booleans must be true/false, not arrays or strings. In particular, assembly.transitions, audio.tts, audio.music, subtitles.enabled, and visual.generation_required are booleans; assembly.animation, visual.type, and text_overlay.position/animation are strings.

Respect the supplied Account language, ContentConcept, and ProductionProfile exactly.
Do not invent account_id, concept_id, or production_profile values."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def generate_scenarios(
        self,
        *,
        account: Mapping[str, Any],
        concept: Mapping[str, Any],
        production_profile: Mapping[str, Any],
    ) -> Sequence[Mapping[str, Any]]:
        user_prompt = (
            "ACCOUNT:\n"
            f"{dict(account)}\n\n"
            "CONTENT CONCEPT:\n"
            f"{dict(concept)}\n\n"
            "PRODUCTION PROFILE:\n"
            f"{dict(production_profile)}"
        )

        result = self.llm.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        if isinstance(result, Mapping) and "scenarios" in result:
            scenarios = result["scenarios"]
        else:
            scenarios = result

        if isinstance(scenarios, (str, bytes, Mapping)) or not isinstance(
            scenarios, Sequence
        ):
            raise DomainValidationError(
                "LLMScenarioProvider must receive a sequence of scenario objects"
            )

        return scenarios
