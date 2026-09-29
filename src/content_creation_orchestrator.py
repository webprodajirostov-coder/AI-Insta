from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Literal, Sequence

from src.content_concept_generator import ContentConceptGenerator
from src.content_concept_orchestrator import ContentConceptOrchestrator
from src.content_idea_generator import ContentIdeaGenerator
from src.content_idea_orchestrator import ContentIdeaOrchestrator
from src.job_pipeline import run_pipeline
from src.production_profile_store import ProductionProfileStore
from src.scenario_job_orchestrator import ScenarioJobOrchestrator
from src.scenario_generator import ScenarioGenerator
from src.scenario_llm_provider import LLMScenarioProvider


@dataclass(frozen=True)
class ContentCreationResult:
    """Explicit result of Content Creation and its optional production run."""

    job_dir: Path
    status: Literal["created", "waiting", "completed", "failed"]
    output_path: Path | None = None
    error: str | None = None


class ContentCreationOrchestrator:
    """Connect Content Intelligence generation with Scenario, Job and Pipeline."""

    def __init__(
        self,
        *,
        idea_generator: ContentIdeaGenerator,
        concept_generator: ContentConceptGenerator,
        scenario_generator: ScenarioGenerator,
        pipeline_runner: Callable[[Path], bool] = run_pipeline,
        production_profile_store: ProductionProfileStore | None = None,
    ):
        self.idea_orchestrator = ContentIdeaOrchestrator(idea_generator)
        self.concept_orchestrator = ContentConceptOrchestrator(concept_generator)
        self.scenario_job_orchestrator = ScenarioJobOrchestrator(
            scenario_generator
        )
        self.pipeline_runner = pipeline_runner
        self.production_profile_store = production_profile_store or ProductionProfileStore(
            "data/production_profiles"
        )

    @staticmethod
    def _load_json(path: str | Path) -> dict[str, Any]:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"JSON object expected: {path}")
        return value

    @classmethod
    def _result_from_job(cls, job_dir: str | Path) -> ContentCreationResult:
        job_dir = Path(job_dir)
        job = cls._load_json(job_dir / "job.json")
        status = job.get("status")

        if status not in {"waiting", "completed", "failed"}:
            raise ValueError(
                "Content creation pipeline returned an invalid Job status: "
                f"{status}"
            )

        output_path = None
        if status == "completed":
            output_path = Path(job["artifacts"]["output"])

        return ContentCreationResult(
            job_dir=job_dir,
            status=status,
            output_path=output_path,
            error=job.get("error"),
        )

    def create(
        self,
        *,
        account_path: str | Path,
        knowledge_path: str | Path,
        research_paths: Sequence[str | Path] = (),
        jobs_root: str | Path = "data/jobs",
        accounts_root: str | Path = "data/accounts",
        run: bool = True,
    ) -> ContentCreationResult:
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
                    "Content creation requires exactly one generated ContentIdea; "
                    f"received {len(ideas)}"
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

            concept = self._load_json(concept_path)
            account = self._load_json(account_path)
            profile = self.production_profile_store.resolve_for_account(
                account=account,
                profile_id=concept["production_profile"],
            )
            profile_path = workspace / "production_profile.json"
            profile_path.write_text(
                json.dumps(profile, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            job_dir = self.scenario_job_orchestrator.generate_scenario_and_create_job(
                content_idea_path=idea_path,
                content_concept_path=concept_path,
                production_profile_path=profile_path,
                scenario_output_path=scenario_path,
                jobs_root=jobs_root,
                accounts_root=accounts_root,
            )

        if not run:
            return ContentCreationResult(
                job_dir=job_dir,
                status="created",
            )

        self.pipeline_runner(job_dir)
        return self._result_from_job(job_dir)
