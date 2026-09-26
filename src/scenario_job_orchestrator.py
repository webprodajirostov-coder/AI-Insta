from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from src.job_service import create_job
from src.scenario_generator import ScenarioGenerator


class ScenarioJobOrchestrator:
    """Connect Scenario v2 generation with the execution Job service."""

    def __init__(
        self,
        scenario_generator: ScenarioGenerator,
        *,
        job_creator: Callable[..., Path] = create_job,
    ):
        self.scenario_generator = scenario_generator
        self.job_creator = job_creator

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"JSON object expected: {path}")
        return value

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

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

        idea = self._load_json(content_idea_path)
        concept = self._load_json(content_concept_path)
        profile = self._load_json(production_profile_path)

        account_id = idea["account_id"]
        account_path = Path(accounts_root) / account_id / "account.json"
        if not account_path.is_file():
            raise FileNotFoundError(f"Account not found: {account_path}")

        account = self._load_json(account_path)

        result = self.scenario_generator.generate(
            account=account,
            concept=concept,
            production_profile=profile,
        )

        if len(result.scenarios) != 1:
            raise ValueError(
                "Scenario job orchestration requires exactly one generated Scenario"
            )

        scenario = result.scenarios[0]
        self._write_json(scenario_output_path, scenario)

        return self.job_creator(
            content_idea_path=content_idea_path,
            content_concept_path=content_concept_path,
            scenario_path=scenario_output_path,
            production_profile_path=production_profile_path,
            jobs_root=jobs_root,
            accounts_root=accounts_root,
        )
