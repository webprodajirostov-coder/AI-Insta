from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from src.job_service import create_job
from src.scenario_generator import ScenarioGenerator
from src.scenario_orchestrator import ScenarioOrchestrator


class ScenarioJobOrchestrator:
    """Connect Scenario v2 orchestration with the execution Job service."""

    def __init__(
        self,
        scenario_generator: ScenarioGenerator,
        *,
        job_creator: Callable[..., Path] = create_job,
    ):
        self.scenario_orchestrator = ScenarioOrchestrator(scenario_generator)
        self.job_creator = job_creator

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"JSON object expected: {path}")
        return value

    def generate_scenario_and_create_job(
        self,
        *,
        content_idea_path: str | Path,
        content_concept_path: str | Path,
        production_profile_path: str | Path,
        scenario_output_path: str | Path,
        jobs_root: str | Path = "data/jobs",
        accounts_root: str | Path = "data/accounts",
    ) -> Path:
        content_idea_path = Path(content_idea_path)
        content_concept_path = Path(content_concept_path)
        production_profile_path = Path(production_profile_path)
        scenario_output_path = Path(scenario_output_path)

        self._load_json(content_idea_path)

        scenario_bundle_path = scenario_output_path.with_suffix(
            scenario_output_path.suffix + ".bundle"
        )

        self.scenario_orchestrator.generate(
            content_concept_path=content_concept_path,
            production_profile_path=production_profile_path,
            output_path=scenario_bundle_path,
            accounts_root=accounts_root,
        )

        payload = self._load_json(scenario_bundle_path)
        scenarios = payload.get("scenarios", [])

        if len(scenarios) != 1:
            scenario_bundle_path.unlink(missing_ok=True)
            raise ValueError(
                "Scenario job orchestration requires exactly one generated Scenario"
            )

        scenario = scenarios[0]
        scenario_output_path.parent.mkdir(parents=True, exist_ok=True)
        scenario_output_path.write_text(
            json.dumps(scenario, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        scenario_bundle_path.unlink(missing_ok=True)

        return self.job_creator(
            content_idea_path=content_idea_path,
            content_concept_path=content_concept_path,
            scenario_path=scenario_output_path,
            production_profile_path=production_profile_path,
            jobs_root=jobs_root,
            accounts_root=accounts_root,
        )
