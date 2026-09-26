from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.scenario_generator import ScenarioGenerator


class ScenarioOrchestrator:
    """Load ContentConcept inputs and persist generated Scenario v2 objects."""

    def __init__(self, generator: ScenarioGenerator):
        self.generator = generator

    @staticmethod
    def _load_json(path: str | Path) -> dict[str, Any]:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")

        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"JSON object expected: {path}")
        return value

    @staticmethod
    def _write_json(path: str | Path, value: dict[str, Any]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def generate(
        self,
        *,
        content_concept_path: str | Path,
        production_profile_path: str | Path,
        output_path: str | Path,
        accounts_root: str | Path = "data/accounts",
    ) -> Path:
        concept = self._load_json(content_concept_path)
        profile = self._load_json(production_profile_path)

        account_id = concept["account_id"]
        account_path = Path(accounts_root) / account_id / "account.json"
        if not account_path.is_file():
            raise FileNotFoundError(f"Account not found: {account_path}")

        account = self._load_json(account_path)

        result = self.generator.generate(
            account=account,
            concept=concept,
            production_profile=profile,
        )

        if not result.scenarios:
            raise ValueError(
                "Scenario orchestration requires at least one generated Scenario"
            )

        output = Path(output_path)
        self._write_json(output, result.to_dict())
        return output
