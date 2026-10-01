from __future__ import annotations

import argparse
from pathlib import Path

from src.content_concept_generator import ContentConceptGenerator
from src.content_creation_orchestrator import ContentCreationOrchestrator
from src.content_idea_generator import ContentIdeaGenerator
from src.llm_content_concept_provider import LLMContentConceptProvider
from src.llm_content_idea_provider import LLMContentIdeaProvider
from src.llm_research_insight_provider import LLMResearchInsightProvider
from src.odirouter_llm_provider import ODIRouterLLMProvider
from src.research_insight_generator import ResearchInsightGenerator
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
        help="Optional raw Research JSON path. May be supplied multiple times.",
    )
    parser.add_argument(
        "--research-insight",
        action="append",
        default=[],
        help="Optional persisted ResearchInsight JSON path. May be supplied multiple times.",
    )
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--jobs-root", default="data/jobs")
    parser.add_argument("--no-run", action="store_true")

    args = parser.parse_args()

    account_dir = ROOT / "data" / "accounts" / args.account
    account_path = account_dir / "account.json"
    knowledge_path = account_dir / "knowledge.json"
    llm = ODIRouterLLMProvider(model=args.model)

    orchestrator = ContentCreationOrchestrator(
        idea_generator=ContentIdeaGenerator(LLMContentIdeaProvider(llm)),
        concept_generator=ContentConceptGenerator(
            LLMContentConceptProvider(llm)
        ),
        scenario_generator=ScenarioGenerator(LLMScenarioProvider(llm)),
        research_insight_generator=ResearchInsightGenerator(
            LLMResearchInsightProvider(llm)
        ),
    )

    raw_research_paths = [ROOT / path for path in args.research]
    research_paths = [ROOT / path for path in args.research_insight]

    result = orchestrator.create(
        account_path=account_path,
        knowledge_path=knowledge_path,
        research_paths=research_paths,
        raw_research_paths=raw_research_paths,
        jobs_root=ROOT / args.jobs_root,
        accounts_root=ROOT / "data" / "accounts",
        run=not args.no_run,
    )

    print("CONTENT CREATION:", result.status.upper())
    print("JOB:", result.job_dir)
    if result.output_path:
        print("OUTPUT:", result.output_path)
    if result.error:
        print("ERROR:", result.error)


if __name__ == "__main__":
    main()
