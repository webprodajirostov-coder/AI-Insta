from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.domain_validation import DomainValidationError
from src.llm_provider import LLMProvider


class LLMScenarioProvider:
    """ScenarioProvider adapter backed by a generic structured LLM provider."""

    SYSTEM_PROMPT = """You are a lead video strategist for short-form video in sales psychology and personal transformation.

Turn the provided ContentConcept into one or more production-ready Scenario v2 objects.

Return ONLY a JSON array of Scenario objects. Do not return markdown or commentary.

Each object must follow the Scenario v2 contract:
- schema_version: 2
- entity: "Scenario"
- title: short title
- hook: concise hook
- caption: short caption
- duration_seconds: positive number within the supplied ProductionProfile bounds
- scenes: non-empty array of Scene objects
- assembly: object with transitions (boolean) and animation (string)

Each Scene must contain:
- scene_id: unique string within the Scenario
- order: positive integer, contiguous starting at 1
- duration_seconds: positive number
- voiceover_text: string; provide non-empty text when the ProductionProfile requires TTS
- visual: object with type, generation_required, and prompt_en
- For generated scenarios intended for downstream execution, set visual.generation_required=true so the execution pipeline knows the Scene requires a generated visual.
- text_overlay: object with text, position, animation, or null
- subtitles: object with actual subtitle data, or null when subtitles are disabled by the ProductionProfile

The sum of Scene.duration_seconds MUST equal Scenario.duration_seconds.
Use only visual types allowed by the supplied ProductionProfile.
Match the ProductionProfile editing constraints exactly in assembly.transitions and assembly.animation.
Do not add a Scenario-level audio object: audio requirements are defined by the ProductionProfile and voiceover_text belongs to each Scene.

Use JSON primitive types exactly: booleans must be true/false, not arrays or strings.
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