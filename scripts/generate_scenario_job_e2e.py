from __future__ import annotations

import argparse
from pathlib import Path

from src.odirouter_llm_provider import ODIRouterLLMProvider
from src.scenario_generator import ScenarioGenerator
from src.scenario_job_orchestrator import ScenarioJobOrchestrator
from src.scenario_llm_provider import LLMScenarioProvider


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a real Scenario v2 and create its execution Job."
    )
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument(
        "--scenario-output",
        default="data/scenarios/scenario_generated_job_e2e.json",
    )
    parser.add_argument("--jobs-root", default="data/jobs")
    args = parser.parse_args()

    account_path = ROOT / "data/accounts/sales_psychology_001/account.json"
    idea_path = ROOT / "data/ideas/content_idea_001.json"
    concept_path = ROOT / "data/ideas/content_concept_001.json"
    profile_path = ROOT / "data/production_profiles/simple.json"

    llm = ODIRouterLLMProvider(model=args.model, timeout=90)
    provider = LLMScenarioProvider(llm)
    generator = ScenarioGenerator(provider)
    orchestrator = ScenarioJobOrchestrator(generator)

    job_dir = orchestrator.generate_scenario_and_create_job(
        content_idea_path=idea_path,
        content_concept_path=concept_path,
        production_profile_path=profile_path,
        scenario_output_path=ROOT / args.scenario_output,
        jobs_root=ROOT / args.jobs_root,
        accounts_root=ROOT / "data/accounts",
    )

    print("SCENARIO + JOB E2E: OK")
    print(f"MODEL: {args.model}")
    print(f"SCENARIO: {ROOT / args.scenario_output}")
    print(f"JOB: {job_dir}")


if __name__ == "__main__":
    main()
