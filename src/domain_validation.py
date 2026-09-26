from __future__ import annotations

from typing import Any, Mapping


class DomainValidationError(ValueError):
    """Raised when domain entities violate a cross-entity contract."""


def _require(entity: Mapping[str, Any], field: str, label: str) -> Any:
    value = entity.get(field)
    if value in (None, ""):
        raise DomainValidationError(f"{label} is missing required field: {field}")
    return value


def validate_account(account: Mapping[str, Any]) -> None:
    _require(account, "account_id", "Account")
    _require(account, "version", "Account")
    _require(account, "status", "Account")
    _require(account, "identity", "Account")
    _require(account, "audience", "Account")
    _require(account, "content_strategy", "Account")
    _require(account, "production_defaults", "Account")


def validate_knowledge(
    knowledge: Mapping[str, Any],
    *,
    account_id: str | None = None,
) -> None:
    knowledge_id = _require(knowledge, "knowledge_id", "Knowledge")
    if account_id is not None:
        actual_account_id = _require(knowledge, "account_id", "Knowledge")
        if actual_account_id != account_id:
            raise DomainValidationError(
                f"Knowledge {knowledge_id} belongs to account "
                f"{actual_account_id!r}, expected {account_id!r}"
            )


def validate_research_insight(
    insight: Mapping[str, Any],
    *,
    account_id: str | None = None,
) -> None:
    insight_id = _require(insight, "insight_id", "ResearchInsight")
    actual_account_id = _require(insight, "account_id", "ResearchInsight")

    if account_id is not None and actual_account_id != account_id:
        raise DomainValidationError(
            f"ResearchInsight {insight_id} belongs to account "
            f"{actual_account_id!r}, expected {account_id!r}"
        )

    _require(insight, "status", "ResearchInsight")
    _require(insight, "source", "ResearchInsight")
    _require(insight, "topic", "ResearchInsight")
    _require(insight, "observation", "ResearchInsight")
    _require(insight, "evidence", "ResearchInsight")
    _require(insight, "relevance", "ResearchInsight")
    _require(insight, "content_implications", "ResearchInsight")

    evidence = insight["evidence"]
    if not isinstance(evidence, list):
        raise DomainValidationError(
            f"ResearchInsight {insight_id} evidence must be a list"
        )

    implications = insight["content_implications"]
    if not isinstance(implications, list):
        raise DomainValidationError(
            f"ResearchInsight {insight_id} content_implications must be a list"
        )

    confidence = insight.get("confidence")
    if confidence is not None and (
        not isinstance(confidence, (int, float)) or isinstance(confidence, bool)
        or not 0 <= confidence <= 1
    ):
        raise DomainValidationError(
            f"ResearchInsight {insight_id} confidence must be between 0 and 1"
        )


def validate_content_idea(
    idea: Mapping[str, Any],
    *,
    account_id: str | None = None,
) -> None:
    idea_id = _require(idea, "idea_id", "ContentIdea")
    actual_account_id = _require(idea, "account_id", "ContentIdea")

    if account_id is not None and actual_account_id != account_id:
        raise DomainValidationError(
            f"ContentIdea {idea_id} belongs to account "
            f"{actual_account_id!r}, expected {account_id!r}"
        )

    for field in (
        "status",
        "source",
        "topic",
        "content_pillar",
        "funnel_stage",
        "angle",
        "audience_problem",
        "audience_desire",
        "hook_direction",
        "why_now",
        "knowledge_refs",
        "research_refs",
        "production",
    ):
        _require(idea, field, "ContentIdea")

    source = idea["source"]
    if not isinstance(source, Mapping):
        raise DomainValidationError(
            f"ContentIdea {idea_id} source must be an object"
        )

    source_ids = _require(source, "source_ids", f"ContentIdea {idea_id}.source")
    if not isinstance(source_ids, list):
        raise DomainValidationError(
            f"ContentIdea {idea_id} source.source_ids must be a list"
        )

    for field in ("knowledge_refs", "research_refs"):
        refs = idea[field]
        if not isinstance(refs, list):
            raise DomainValidationError(
                f"ContentIdea {idea_id} {field} must be a list"
            )

    priority = idea.get("priority")
    if priority is not None and (
        not isinstance(priority, (int, float)) or isinstance(priority, bool)
        or priority < 0
    ):
        raise DomainValidationError(
            f"ContentIdea {idea_id} priority must be a non-negative number"
        )

    production = idea["production"]
    if not isinstance(production, Mapping):
        raise DomainValidationError(
            f"ContentIdea {idea_id} production must be an object"
        )

    _require(production, "profile", "ContentIdea.production")


def validate_content_concept(
    concept: Mapping[str, Any],
    *,
    account_id: str | None = None,
    idea_id: str | None = None,
) -> None:
    concept_id = _require(concept, "concept_id", "ContentConcept")
    actual_account_id = _require(concept, "account_id", "ContentConcept")
    actual_idea_id = _require(concept, "idea_id", "ContentConcept")

    if account_id is not None and actual_account_id != account_id:
        raise DomainValidationError(
            f"ContentConcept {concept_id} belongs to account "
            f"{actual_account_id!r}, expected {account_id!r}"
        )

    if idea_id is not None and actual_idea_id != idea_id:
        raise DomainValidationError(
            f"ContentConcept {concept_id} belongs to idea "
            f"{actual_idea_id!r}, expected {idea_id!r}"
        )

    for field in (
        "status",
        "core_message",
        "problem",
        "reframe",
        "psychological_mechanism",
        "key_points",
        "hook",
        "emotional_direction",
        "audience_takeaway",
        "cta",
        "knowledge_refs",
        "research_refs",
        "production_profile",
    ):
        _require(concept, field, "ContentConcept")

    key_points = concept["key_points"]
    if not isinstance(key_points, list):
        raise DomainValidationError(
            f"ContentConcept {concept_id} key_points must be a list"
        )

    cta = concept["cta"]
    if not isinstance(cta, Mapping):
        raise DomainValidationError(
            f"ContentConcept {concept_id} cta must be an object"
        )
    _require(cta, "type", f"ContentConcept {concept_id}.cta")
    if "text" not in cta:
        raise DomainValidationError(
            f"ContentConcept {concept_id}.cta is missing required field: text"
        )

    for field in ("knowledge_refs", "research_refs"):
        refs = concept[field]
        if not isinstance(refs, list):
            raise DomainValidationError(
                f"ContentConcept {concept_id} {field} must be a list"
            )


def validate_scenario(
    scenario: Mapping[str, Any],
    *,
    account_id: str | None = None,
    concept_id: str | None = None,
    production_profile: Mapping[str, Any] | None = None,
) -> None:
    scenario_id = _require(scenario, "scenario_id", "Scenario")
    actual_account_id = _require(scenario, "account_id", "Scenario")
    actual_concept_id = _require(scenario, "concept_id", "Scenario")

    if account_id is not None and actual_account_id != account_id:
        raise DomainValidationError(
            f"Scenario {scenario_id} belongs to account "
            f"{actual_account_id!r}, expected {account_id!r}"
        )

    if concept_id is not None and actual_concept_id != concept_id:
        raise DomainValidationError(
            f"Scenario {scenario_id} belongs to concept "
            f"{actual_concept_id!r}, expected {concept_id!r}"
        )

    scenario_profile_id = _require(
        scenario, "production_profile", "Scenario"
    )

    if production_profile is None:
        return

    validate_production_profile(production_profile)
    profile_id = production_profile["profile_id"]
    if scenario_profile_id != profile_id:
        raise DomainValidationError(
            f"Scenario {scenario_id} uses ProductionProfile "
            f"{scenario_profile_id!r}, expected {profile_id!r}"
        )

    duration = _require(scenario, "duration_seconds", f"Scenario {scenario_id}")
    if (
        not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or duration <= 0
    ):
        raise DomainValidationError(
            f"Scenario {scenario_id} duration_seconds must be a positive number"
        )

    duration_bounds = production_profile["duration_seconds"]
    if duration < duration_bounds["min"] or duration > duration_bounds["max"]:
        raise DomainValidationError(
            f"Scenario {scenario_id} duration_seconds {duration} is outside "
            f"ProductionProfile {profile_id} range "
            f"{duration_bounds['min']}–{duration_bounds['max']}"
        )

    visual = _require(scenario, "visual", f"Scenario {scenario_id}")
    if not isinstance(visual, Mapping):
        raise DomainValidationError(
            f"Scenario {scenario_id} visual must be an object"
        )

    visual_type = _require(visual, "type", f"Scenario {scenario_id}.visual")
    if visual_type not in production_profile["visual"]["types"]:
        raise DomainValidationError(
            f"Scenario {scenario_id} visual type {visual_type!r} is not supported "
            f"by ProductionProfile {profile_id}"
        )

    generation_required = visual.get("generation_required")
    profile_generation_required = production_profile["visual"].get(
        "generation_required"
    )
    if profile_generation_required is True and generation_required is not True:
        raise DomainValidationError(
            f"Scenario {scenario_id} must require visual generation for "
            f"ProductionProfile {profile_id}"
        )

    audio = _require(scenario, "audio", f"Scenario {scenario_id}")
    if not isinstance(audio, Mapping):
        raise DomainValidationError(
            f"Scenario {scenario_id} audio must be an object"
        )

    profile_audio = production_profile["audio"]
    for field in ("tts", "music"):
        if field in profile_audio and audio.get(field) != profile_audio[field]:
            raise DomainValidationError(
                f"Scenario {scenario_id} audio.{field}={audio.get(field)!r} "
                f"does not match ProductionProfile {profile_id} "
                f"requirement {profile_audio[field]!r}"
            )

    subtitles = _require(scenario, "subtitles", f"Scenario {scenario_id}")
    if not isinstance(subtitles, Mapping):
        raise DomainValidationError(
            f"Scenario {scenario_id} subtitles must be an object"
        )

    profile_text = production_profile["text"]
    if profile_text.get("subtitles") is True and subtitles.get("enabled") is not True:
        raise DomainValidationError(
            f"Scenario {scenario_id} must enable subtitles for "
            f"ProductionProfile {profile_id}"
        )

    assembly = _require(scenario, "assembly", f"Scenario {scenario_id}")
    if not isinstance(assembly, Mapping):
        raise DomainValidationError(
            f"Scenario {scenario_id} assembly must be an object"
        )

    profile_editing = production_profile["editing"]
    if (
        "transitions" in profile_editing
        and assembly.get("transitions") != profile_editing["transitions"]
    ):
        raise DomainValidationError(
            f"Scenario {scenario_id} assembly.transitions={assembly.get('transitions')!r} "
            f"does not match ProductionProfile {profile_id}"
        )

    if (
        "animation" in profile_editing
        and assembly.get("animation") != profile_editing["animation"]
    ):
        raise DomainValidationError(
            f"Scenario {scenario_id} assembly.animation={assembly.get('animation')!r} "
            f"does not match ProductionProfile {profile_id}"
        )



def validate_scenario_v2(
    scenario: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    account_id: str | None = None,
    concept_id: str | None = None,
) -> None:
    """Validate the Scenario v2 structural contract against its profile."""

    scenario_id = _require(scenario, "scenario_id", "Scenario")
    actual_account_id = _require(scenario, "account_id", "Scenario")
    actual_concept_id = _require(scenario, "concept_id", "Scenario")
    scenario_profile_id = _require(
        scenario, "production_profile", "Scenario"
    )

    if account_id is not None and actual_account_id != account_id:
        raise DomainValidationError(
            f"Scenario {scenario_id} belongs to account "
            f"{actual_account_id!r}, expected {account_id!r}"
        )

    if concept_id is not None and actual_concept_id != concept_id:
        raise DomainValidationError(
            f"Scenario {scenario_id} belongs to concept "
            f"{actual_concept_id!r}, expected {concept_id!r}"
        )

    if scenario_profile_id != profile["profile_id"]:
        raise DomainValidationError(
            f"Scenario {scenario_id} uses ProductionProfile "
            f"{scenario_profile_id!r}, expected {profile['profile_id']!r}"
        )


    if scenario.get("schema_version") != 2:
        raise DomainValidationError(
            f"Scenario {scenario_id} must use schema_version=2"
        )

    for field in (
        "status",
        "language",
        "title",
        "hook",
        "caption",
        "duration_seconds",
        "scenes",
        "assembly",
    ):
        _require(scenario, field, "Scenario")

    duration = scenario["duration_seconds"]
    if not isinstance(duration, (int, float)) or isinstance(duration, bool):
        raise DomainValidationError(
            f"Scenario {scenario_id} duration_seconds must be numeric"
        )

    profile_duration = profile["duration_seconds"]
    minimum = profile_duration["min"]
    maximum = profile_duration["max"]

    if not minimum <= duration <= maximum:
        raise DomainValidationError(
            f"Scenario {scenario_id} duration_seconds={duration} is outside "
            f"ProductionProfile {profile['profile_id']} bounds "
            f"{minimum}..{maximum}"
        )

    scenes = scenario["scenes"]
    if not isinstance(scenes, list) or not scenes:
        raise DomainValidationError(
            f"Scenario {scenario_id} scenes must be a non-empty list"
        )

    orders: list[int] = []

    for index, scene in enumerate(scenes, start=1):
        label = f"Scenario {scenario_id} Scene[{index}]"

        if not isinstance(scene, Mapping):
            raise DomainValidationError(f"{label} must be an object")

        for field in (
            "scene_id",
            "order",
            "duration_seconds",
            "voiceover_text",
            "visual",
            "text_overlay",
            "subtitles",
        ):
            if field not in scene:
                raise DomainValidationError(
                    f"{label} is missing required field: {field}"
                )

        order = scene["order"]
        if not isinstance(order, int) or isinstance(order, bool) or order < 1:
            raise DomainValidationError(
                f"{label}.order must be a positive integer"
            )
        orders.append(order)

        scene_duration = scene["duration_seconds"]
        if (
            not isinstance(scene_duration, (int, float))
            or isinstance(scene_duration, bool)
            or scene_duration <= 0
        ):
            raise DomainValidationError(
                f"{label}.duration_seconds must be a positive number"
            )

        voiceover_text = scene["voiceover_text"]
        if not isinstance(voiceover_text, str):
            raise DomainValidationError(
                f"{label}.voiceover_text must be a string"
            )

        visual = scene["visual"]
        if not isinstance(visual, Mapping):
            raise DomainValidationError(f"{label}.visual must be an object")

        for field in ("type", "generation_required"):
            if field not in visual:
                raise DomainValidationError(
                    f"{label}.visual is missing required field: {field}"
                )

        visual_type = visual["type"]
        if visual_type not in profile["visual"]["types"]:
            raise DomainValidationError(
                f"{label}.visual.type={visual_type!r} is not allowed by "
                f"ProductionProfile {profile['profile_id']}"
            )

        if not isinstance(visual["generation_required"], bool):
            raise DomainValidationError(
                f"{label}.visual.generation_required must be boolean"
            )

        prompt = visual.get("prompt_en")
        if prompt is not None and not isinstance(prompt, str):
            raise DomainValidationError(
                f"{label}.visual.prompt_en must be a string or null"
            )

        text_overlay = scene["text_overlay"]
        if text_overlay is not None:
            if not isinstance(text_overlay, Mapping):
                raise DomainValidationError(
                    f"{label}.text_overlay must be an object or null"
                )

            for field in ("text", "position", "animation"):
                if field not in text_overlay:
                    raise DomainValidationError(
                        f"{label}.text_overlay is missing required field: {field}"
                    )

        subtitles = scene["subtitles"]
        if not profile["text"]["subtitles"] and subtitles is not None:
            raise DomainValidationError(
                f"{label}.subtitles must be null because "
                f"ProductionProfile {profile['profile_id']} disables subtitles"
            )

        if profile["audio"]["tts"] and not voiceover_text.strip():
            raise DomainValidationError(
                f"{label}.voiceover_text is required because "
                f"ProductionProfile {profile['profile_id']} requires TTS"
            )

    if sorted(orders) != list(range(1, len(scenes) + 1)):
        raise DomainValidationError(
            f"Scenario {scenario_id} scene orders must be unique and contiguous "
            f"starting at 1"
        )

    total_scene_duration = sum(scene["duration_seconds"] for scene in scenes)
    if total_scene_duration != duration:
        raise DomainValidationError(
            f"Scenario {scenario_id} duration_seconds={duration} does not "
            f"match sum(Scene.duration_seconds)={total_scene_duration}"
        )

    assembly = scenario["assembly"]
    if not isinstance(assembly, Mapping):
        raise DomainValidationError(
            f"Scenario {scenario_id} assembly must be an object"
        )

    for field in ("transitions", "animation"):
        if field not in assembly:
            raise DomainValidationError(
                f"Scenario {scenario_id} assembly is missing required field: {field}"
            )

    if assembly["transitions"] != profile["editing"]["transitions"]:
        raise DomainValidationError(
            f"Scenario {scenario_id} assembly.transitions does not match "
            f"ProductionProfile {profile['profile_id']}"
        )

    if assembly["animation"] != profile["editing"]["animation"]:
        raise DomainValidationError(
            f"Scenario {scenario_id} assembly.animation does not match "
            f"ProductionProfile {profile['profile_id']}"
        )

def validate_production_profile(profile: Mapping[str, Any]) -> None:
    profile_id = _require(profile, "profile_id", "ProductionProfile")
    _require(profile, "status", "ProductionProfile")
    visual = _require(profile, "visual", "ProductionProfile")
    _require(profile, "audio", "ProductionProfile")
    _require(profile, "text", "ProductionProfile")
    _require(profile, "editing", "ProductionProfile")
    _require(profile, "duration_seconds", "ProductionProfile")

    count = _require(visual, "count", f"ProductionProfile.visual ({profile_id})")
    if not isinstance(count, int) or count < 1:
        raise DomainValidationError(
            f"ProductionProfile {profile_id} visual.count must be a positive integer"
        )

    types = _require(visual, "types", f"ProductionProfile.visual ({profile_id})")
    if not isinstance(types, list) or not types:
        raise DomainValidationError(
            f"ProductionProfile {profile_id} visual.types must be a non-empty list"
        )

    duration = profile["duration_seconds"]
    if not isinstance(duration, Mapping):
        raise DomainValidationError(
            f"ProductionProfile {profile_id} duration_seconds must be an object"
        )

    minimum = _require(
        duration,
        "min",
        f"ProductionProfile.duration_seconds ({profile_id})",
    )
    maximum = _require(
        duration,
        "max",
        f"ProductionProfile.duration_seconds ({profile_id})",
    )

    if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
        raise DomainValidationError(
            f"ProductionProfile {profile_id} duration bounds must be numeric"
        )

    if minimum > maximum:
        raise DomainValidationError(
            f"ProductionProfile {profile_id} duration min cannot exceed max"
        )


def validate_knowledge_refs(
    entity: Mapping[str, Any],
    knowledge: Mapping[str, Any],
    *,
    label: str,
) -> None:
    refs = entity.get("knowledge_refs", [])
    if not isinstance(refs, list):
        raise DomainValidationError(f"{label}.knowledge_refs must be a list")

    known_ids: set[str] = set()
    for key in (
        "core_concepts",
        "audience_insights",
        "psychological_mechanisms",
        "content_pillars",
    ):
        for item in knowledge.get(key, []):
            if isinstance(item, Mapping) and item.get("id"):
                known_ids.add(item["id"])

    missing = [ref for ref in refs if ref not in known_ids]
    if missing:
        raise DomainValidationError(
            f"{label} references unknown Knowledge ids: {missing}"
        )


def validate_research_refs(
    entity: Mapping[str, Any],
    research_insights: Mapping[str, Mapping[str, Any]] | list[Mapping[str, Any]],
    *,
    label: str,
) -> None:
    refs = entity.get("research_refs", [])
    if not isinstance(refs, list):
        raise DomainValidationError(f"{label}.research_refs must be a list")

    if isinstance(research_insights, Mapping):
        known = research_insights
    else:
        known = {
            insight.get("insight_id"): insight
            for insight in research_insights
            if isinstance(insight, Mapping) and insight.get("insight_id")
        }

    missing = [ref for ref in refs if ref not in known]
    if missing:
        raise DomainValidationError(
            f"{label} references unknown ResearchInsight ids: {missing}"
        )


def validate_content_chain(
    *,
    account: Mapping[str, Any],
    knowledge: Mapping[str, Any],
    idea: Mapping[str, Any],
    concept: Mapping[str, Any],
    scenario: Mapping[str, Any],
    profile: Mapping[str, Any],
    research_insights: Mapping[str, Mapping[str, Any]]
    | list[Mapping[str, Any]]
    | None = None,
) -> None:
    account_id = _require(account, "account_id", "Account")
    idea_id = _require(idea, "idea_id", "ContentIdea")
    concept_id = _require(concept, "concept_id", "ContentConcept")
    profile_id = _require(profile, "profile_id", "ProductionProfile")

    validate_account(account)
    validate_knowledge(knowledge, account_id=account_id)
    validate_content_idea(idea, account_id=account_id)
    validate_content_concept(
        concept,
        account_id=account_id,
        idea_id=idea_id,
    )
    validate_production_profile(profile)

    schema_version = scenario.get("schema_version")
    if schema_version == 2:
        validate_scenario_v2(
            scenario,
            profile,
            account_id=account_id,
            concept_id=concept_id,
        )
    elif schema_version is None or schema_version == 1:
        validate_scenario(
            scenario,
            account_id=account_id,
            concept_id=concept_id,
            production_profile=profile,
        )
    else:
        raise DomainValidationError(
            f"Scenario {scenario.get('scenario_id', '<unknown>')} uses "
            f"unsupported schema_version={schema_version!r}"
        )

    idea_profile = idea["production"]["profile"]
    concept_profile = concept["production_profile"]
    scenario_profile = scenario["production_profile"]

    if not (
        idea_profile == concept_profile == scenario_profile == profile_id
    ):
        raise DomainValidationError(
            "ProductionProfile mismatch across ContentIdea, "
            "ContentConcept, Scenario and ProductionProfile: "
            f"{idea_profile!r}, {concept_profile!r}, "
            f"{scenario_profile!r}, {profile_id!r}"
        )

    content_pillars = account.get("content_strategy", {}).get("pillars", [])
    idea_pillar = idea.get("content_pillar")
    if idea_pillar and content_pillars and idea_pillar not in content_pillars:
        raise DomainValidationError(
            f"ContentIdea {idea_id} uses unknown account content pillar: "
            f"{idea_pillar!r}"
        )

    validate_knowledge_refs(idea, knowledge, label="ContentIdea")
    validate_knowledge_refs(concept, knowledge, label="ContentConcept")

    if research_insights is None:
        if idea.get("research_refs") or concept.get("research_refs"):
            raise DomainValidationError(
                "ResearchInsight references are present but research_insights "
                "were not provided for validation"
            )
    else:
        for insight in (
            research_insights.values()
            if isinstance(research_insights, Mapping)
            else research_insights
        ):
            validate_research_insight(insight, account_id=account_id)

        validate_research_refs(
            idea, research_insights, label="ContentIdea"
        )
        validate_research_refs(
            concept, research_insights, label="ContentConcept"
        )
