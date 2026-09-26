from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Sequence

from src.content_concept_generator import ContentConceptGenerator
from src.content_concept_orchestrator import ContentConceptOrchestrator
from src.content_idea_generator import ContentIdeaGenerator
from src.content_idea_orchestrator import ContentIdeaOrchestrator
from src.job_pipeline import run_pipeline
from src.scenario_job_orchestrator import ScenarioJobOrchestrator
from src.scenario_generator import ScenarioGenerator
from src.scenario_llm_provider import LLMScenarioProvider


class ContentCreationOrchestrator:
    """Connect Content Intelligence generation with Scenario, Job and Pipeline."""

    def __init__(
        self,
        *,
        idea_generator: ContentIdeaGenerator,
        concept_generator: ContentConceptGenerator,
        scenario_generator: ScenarioGenerator,
        pipeline_runner: Callable[[Path], bool] = run_pipeline,
    ):
        self.idea_orchestrator = ContentIdeaOrchestrator(idea_generator)
        self.concept_orchestrator = ContentConceptOrchestrator(concept_generator)
        self.scenario_job_orchestrator = ScenarioJobOrchestrator(
            scenario_generator
        )
        self.pipeline_runner = pipeline_runner

    @staticmethod
    def _load_json(path: str | Path) -> dict[str, Any]:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"JSON object expected: {path}")
        return value

    def create(
        self,
        *,
        account_path: str | Path,
        knowledge_path: str | Path,
        production_profile_path: str | Path,
        research_paths: Sequence[str | Path] = (),
        jobs_root: str | Path = "data/jobs",
        accounts_root: str | Path = "data/accounts",
        run: bool = True,
    ) -> Path:
        with TemporaryDirectory(prefix="ai_insta_content_") as tmp:
            workspace = Path(tmp)
            ideas_path = workspace / "ideas.json"
            concepts_path = workspace / "concepts.json"
            idea_path = workspace / "content_idea.json"
            concept_path = workspace / "content_concept.json"
            scenario_path = workspace / "scenario.json"

            self.idea_orchestrator.generate(
                account_path=account_path,
                knowledge_path=knowledge_path,
                research_paths=research_paths,
                output_path=ideas_path,
            )
            ideas = self._load_json(ideas_path).get("ideas", [])
            if len(ideas) != 1:
                raise ValueError(
                    "Content creation requires exactly one generated ContentIdea"
                )
            idea_path.write_text(
                json.dumps(ideas[0], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            self.concept_orchestrator.generate(
                account_path=account_path,
                knowledge_path=knowledge_path,
                idea_path=idea_path,
                research_paths=research_paths,
                output_path=concepts_path,
            )
            concepts = self._load_json(concepts_path).get("concepts", [])
            if len(concepts) != 1:
                raise ValueError(
                    "Content creation requires exactly one generated ContentConcept"
                )
            concept_path.write_text(
                json.dumps(concepts[0], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            job_dir = self.scenario_job_orchestrator.generate_scenario_and_create_job(
                content_idea_path=idea_path,
                content_concept_path=concept_path,
                production_profile_path=production_profile_path,
                scenario_output_path=scenario_path,
                jobs_root=jobs_root,
                accounts_root=accounts_root,
            )

        if run:
            self.pipeline_runner(job_dir)

        return job_dir
