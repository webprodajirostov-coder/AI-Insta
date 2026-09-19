import json
from pathlib import Path
from datetime import datetime

STAGE_STATUSES = {"skipped", "waiting", "completed", "failed"}


def update_stage(job_dir, stage, status):
    job_dir = Path(job_dir)
    job_path = job_dir / "job.json"

    with open(job_path, "r", encoding="utf-8") as f:
        job = json.load(f)

    if stage not in job["pipeline"]:
        raise ValueError(f"Unknown pipeline stage: {stage}")

    if status not in STAGE_STATUSES:
        raise ValueError(f"Invalid pipeline stage status: {status}")

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
