from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.odirouter_llm_provider import ODIRouterLLMProvider
from src.scenario_generator import ScenarioGenerator
from src.scenario_llm_provider import LLMScenarioProvider

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a real Scenario v2 through ODIRouter."
    )
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument(
        "--output",
        default="data/scenarios/scenario_generated_e2e.json",
    )
    args = parser.parse_args()

    account = load_json(
        ROOT / "data/accounts/sales_psychology_001/account.json"
    )
    concept = load_json(ROOT / "data/ideas/content_concept_001.json")
    profile = load_json(ROOT / "data/production_profiles/simple.json")

    llm = ODIRouterLLMProvider(model=args.model, timeout=90)
    provider = LLMScenarioProvider(llm)
    generator = ScenarioGenerator(provider)

    result = generator.generate(
        account=account,
        concept=concept,
        production_profile=profile,
    )

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("SCENARIO GENERATION: OK")
    print(f"MODEL: {args.model}")
    print(f"SCENARIOS: {len(result.scenarios)}")
    print(f"OUTPUT: {output}")
    for scenario in result.scenarios:
        print(
            f"SCENARIO: {scenario['scenario_id']} | "
            f"SCHEMA: {scenario['schema_version']} | "
            f"SCENES: {len(scenario['scenes'])} | "
            f"DURATION: {scenario['duration_seconds']}s"
        )


if __name__ == "__main__":
    main()
