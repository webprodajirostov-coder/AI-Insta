import sys
import json
from pathlib import Path

from src.assembly_renderer import render_assembly
from src.output_validator import validate_output


def finalize(job_dir):
    job_dir = Path(job_dir)

    print()
    print("===== FINALIZE OUTPUT =====")

    try:
        with open(job_dir / "job.json", "r", encoding="utf-8") as f:
            job = json.load(f)

        if job["pipeline"].get("output") == "completed":
            print()
            print("[1/3] RENDER: SKIPPED (OUTPUT ALREADY COMPLETED)")
        else:
            print()
            print("[1/3] RENDER")
            render_assembly(job_dir)

        print()
        print("[2/3] VALIDATE")
        validate_output(job_dir)

        print()
        print("[3/3] COMPLETE JOB")
        from src.job_pipeline import complete_job_after_output_validation

        complete_job_after_output_validation(job_dir)

        print()
        print("===== FINALIZE RESULT =====")
        print("OUTPUT FINALIZED: OK")
        print("============================")

        return True

    except Exception as e:
        print()
        print("===== FINALIZE RESULT =====")
        print(f"OUTPUT FINALIZE FAILED: {e}")
        print("============================")

        try:
            update_stage(
                str(job_dir),
                "output",
                "failed",
            )
        except Exception as stage_error:
            print(
                f"JOB STAGE UPDATE FAILED: {stage_error}"
            )

        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python src/finalizer.py <job_dir>"
        )
        raise SystemExit(1)

    success = finalize(sys.argv[1])

    raise SystemExit(0 if success else 1)
