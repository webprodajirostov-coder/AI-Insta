from __future__ import annotations

import argparse
from pathlib import Path

from src.content_concept_generator import ContentConceptGenerator
from src.content_creation_orchestrator import ContentCreationOrchestrator
from src.content_idea_generator import ContentIdeaGenerator
from src.llm_content_concept_provider import LLMContentConceptProvider
from src.llm_content_idea_provider import LLMContentIdeaProvider
from src.odirouter_llm_provider import ODIRouterLLMProvider
from src.scenario_generator import ScenarioGenerator
from src.scenario_llm_provider import LLMScenarioProvider


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Content Intelligence and create a production Job."
    )
    parser.add_argument(
        "--account",
        default="sales_psychology_001",
        help="Account id under data/accounts.",
    )
    parser.add_argument(
        "--research",
        action="append",
        default=[],
        help="Optional ResearchInsight JSON path. May be supplied multiple times.",
    )
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--jobs-root", default="data/jobs")
    parser.add_argument("--no-run", action="store_true")

    args = parser.parse_args()

    account_dir = ROOT / "data" / "accounts" / args.account
    account_path = account_dir / "account.json"
    knowledge_path = account_dir / "knowledge.json"
    profile_name = None

    account = __import__("json").loads(
        account_path.read_text(encoding="utf-8")
    )
    profile_name = account["production_defaults"]["baseline_format"]
    profile_path = ROOT / "data" / "production_profiles" / f"{profile_name}.json"

    llm = ODIRouterLLMProvider(model=args.model)

    orchestrator = ContentCreationOrchestrator(
        idea_generator=ContentIdeaGenerator(LLMContentIdeaProvider(llm)),
        concept_generator=ContentConceptGenerator(
            LLMContentConceptProvider(llm)
        ),
        scenario_generator=ScenarioGenerator(LLMScenarioProvider(llm)),
    )

    research_paths = [ROOT / path for path in args.research]

    job_dir = orchestrator.create(
        account_path=account_path,
        knowledge_path=knowledge_path,
        production_profile_path=profile_path,
        research_paths=research_paths,
        jobs_root=ROOT / args.jobs_root,
        accounts_root=ROOT / "data" / "accounts",
        run=not args.no_run,
    )

    print("CONTENT CREATION: OK")
    print("JOB:", job_dir)


if __name__ == "__main__":
    main()
