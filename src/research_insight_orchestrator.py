from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from src.research_insight_generator import ResearchInsightGenerator


class ResearchInsightOrchestrator:
    """Load Research records, generate ResearchInsights, and persist them."""

    def __init__(self, generator: ResearchInsightGenerator):
        self.generator = generator

    @staticmethod
    def _load_json(path: str | Path) -> dict:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"JSON object expected: {path}")
        return value

    @staticmethod
    def _write_json(path: str | Path, value: dict) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def generate(
        self,
        *,
        account_path: str | Path,
        research_paths: Sequence[str | Path],
        output_path: str | Path,
    ) -> Path:
        account = self._load_json(account_path)
        research = [self._load_json(path) for path in research_paths]

        result = self.generator.generate(
            account=account,
            research=research,
        )

        output = Path(output_path)
        self._write_json(
            output,
            {"research_insights": [dict(item) for item in result.insights]},
        )
        return output
