from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from src.content_concept_generator import ContentConceptGenerator


class ContentConceptOrchestrator:
    """Load Content Intelligence inputs and persist generated ContentConcepts."""

    def __init__(self, generator: ContentConceptGenerator):
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
        account_path: str | Path,
        knowledge_path: str | Path,
        idea_path: str | Path,
        research_paths: Sequence[str | Path] = (),
        output_path: str | Path,
    ) -> Path:
        account = self._load_json(account_path)
        knowledge = self._load_json(knowledge_path)
        idea = self._load_json(idea_path)

        research_insights: list[dict[str, Any]] = []
        for research_path in research_paths:
            research_insights.append(self._load_json(research_path))

        result = self.generator.generate(
            account=account,
            knowledge=knowledge,
            idea=idea,
            research_insights=research_insights,
        )

        if not result.concepts:
            raise ValueError(
                "Content concept orchestration requires at least one generated concept"
            )

        output = Path(output_path)
        self._write_json(
            output,
            {"concepts": [dict(concept) for concept in result.concepts]},
        )
        return output
