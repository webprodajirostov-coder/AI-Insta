import json
from pathlib import Path
from datetime import datetime

STAGE_ALLOWED_STATUSES = {
    "research": {"completed", "skipped", "failed"},
    "analysis": {"completed", "skipped", "failed"},
    "concept": {"completed", "failed"},
    "scenario": {"completed", "failed"},
    "audio": {"completed", "failed"},
    "visual": {"completed", "waiting", "failed"},
    "assembly": {"completed", "failed"},
    "output": {"completed", "failed"},
}

STAGE_TRANSITIONS = {
    "research": {
        "pending": {"completed", "skipped", "failed"},
    },
    "analysis": {
        "pending": {"completed", "skipped", "failed"},
    },
    "concept": {
        "pending": {"completed", "failed"},
    },
    "scenario": {
        "pending": {"completed", "failed"},
    },
    "audio": {
        "pending": {"completed", "failed"},
    },
    "visual": {
        "pending": {"completed", "waiting", "failed"},
        "waiting": {"completed", "failed"},
    },
    "assembly": {
        "pending": {"completed", "failed"},
    },
    "output": {
        "pending": {"failed"},
    },
}


def update_stage(job_dir, stage, status):
    job_dir = Path(job_dir)
    job_path = job_dir / "job.json"

    with open(job_path, "r", encoding="utf-8") as f:
        job = json.load(f)

    if stage not in job["pipeline"]:
        raise ValueError(f"Unknown pipeline stage: {stage}")

    if stage not in STAGE_ALLOWED_STATUSES:
        raise ValueError(f"Unsupported pipeline stage: {stage}")

    if status not in STAGE_ALLOWED_STATUSES[stage]:
        raise ValueError(
            f"Invalid status for pipeline stage {stage}: {status}"
        )

    if stage == "output" and status == "completed":
        raise ValueError(
            "Output completion is reserved for final job completion"
        )

    current_status = job["pipeline"][stage]

    if current_status not in {"pending", "completed", "waiting", "failed"}:
        raise ValueError(
            f"Invalid current status for pipeline stage "
            f"{stage}: {current_status}"
        )

    if current_status == status:
        raise ValueError(
            f"Pipeline stage {stage} is already {status}"
        )

    allowed_next = STAGE_TRANSITIONS.get(stage, {}).get(
        current_status,
        set(),
    )

    if status not in allowed_next:
        raise ValueError(
            f"Invalid pipeline transition for {stage}: "
            f"{current_status} -> {status}"
        )

    job["pipeline"][stage] = status
    job["updated_at"] = datetime.now().isoformat(timespec="seconds")

    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)

    return job


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print(
            "Usage: python src/update_job_stage.py "
            "<job_dir> <stage> <status>"
        )
        raise SystemExit(1)

    job = update_stage(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3]
    )

    print(
        f"JOB STAGE UPDATED: "
        f"{sys.argv[2]}={sys.argv[3]}"
    )
