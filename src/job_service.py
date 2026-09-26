"""Execution Job service: validates content inputs and creates an isolated Job directory."""

import json
import shutil
from datetime import datetime
from pathlib import Path

from src.domain_validation import validate_content_chain


PIPELINE_STAGES = [
    "research",
    "analysis",
    "concept",
    "scenario",
    "audio",
    "visual",
    "assembly",
    "output",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_job(
    content_idea_path,
    content_concept_path,
    scenario_path,
    production_profile_path,
    jobs_root="data/jobs",
    accounts_root="data/accounts",
):
    content_idea_path = Path(content_idea_path)
    content_concept_path = Path(content_concept_path)
    scenario_path = Path(scenario_path)
    production_profile_path = Path(production_profile_path)
    jobs_root = Path(jobs_root)
    accounts_root = Path(accounts_root)

    idea = load_json(content_idea_path)
    concept = load_json(content_concept_path)
    scenario = load_json(scenario_path)
    profile = load_json(production_profile_path)

    account_id = idea["account_id"]
    account_path = accounts_root / account_id / "account.json"
    knowledge_path = accounts_root / account_id / "knowledge.json"

    if not account_path.exists():
        raise FileNotFoundError(f"Account not found: {account_path}")

    if not knowledge_path.exists():
        raise FileNotFoundError(f"Knowledge not found: {knowledge_path}")

    account = load_json(account_path)
    knowledge = load_json(knowledge_path)

    validate_content_chain(
        account=account,
        knowledge=knowledge,
        idea=idea,
        concept=concept,
        scenario=scenario,
        profile=profile,
    )

    idea_id = idea["idea_id"]
    concept_id = concept["concept_id"]
    scenario_id = scenario["scenario_id"]
    profile_id = profile["profile_id"]

    now = datetime.now().replace(microsecond=0)
    job_id = now.strftime("%Y%m%d_%H%M%S")

    job_dir = jobs_root / job_id

    if job_dir.exists():
        raise FileExistsError(f"Job already exists: {job_dir}")

    directories = [
        job_dir / "input",
        job_dir / "content",
        job_dir / "media" / "audio",
        job_dir / "media" / "visual",
        job_dir / "media" / "subtitles",
        job_dir / "assembly",
        job_dir / "output",
        job_dir / "research",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=False)

    shutil.copy2(
        content_idea_path,
        job_dir / "input" / "content_idea.json",
    )

    shutil.copy2(
        content_concept_path,
        job_dir / "content" / "content_concept.json",
    )

    shutil.copy2(
        scenario_path,
        job_dir / "content" / "scenario.json",
    )

    pipeline = {
        stage: "pending"
        for stage in PIPELINE_STAGES
    }

    job = {
        "job_id": job_id,
        "account_id": account_id,
        "status": "created",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "language": scenario.get("language", "en"),
        "input": {
            "type": "content_idea",
            "idea_id": idea_id,
        },
        "content": {
            "concept_id": concept_id,
            "scenario_id": scenario_id,
        },
        "production": {
            "profile": profile_id,
        },
        "pipeline": pipeline,
        "artifacts": {
            "scenario": str(job_dir / "content" / "scenario.json"),
            "output": None,
        },
        "error": None,
    }

    with open(job_dir / "job.json", "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)

    return job_dir


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 5:
        print(
            "Usage: python -m src.job_creator "
            "<content_idea.json> "
            "<content_concept.json> "
            "<scenario.json> "
            "<production_profile.json>"
        )
        raise SystemExit(1)

    job_dir = create_job(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4],
    )

    print(f"JOB CREATED: {job_dir}")
