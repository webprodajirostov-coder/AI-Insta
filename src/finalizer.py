import sys
from pathlib import Path

from src.assembly_renderer import render_assembly
from src.output_validator import validate_output
from src.update_job_stage import update_stage


def finalize(job_dir):
    job_dir = Path(job_dir)

    print()
    print("===== FINALIZE OUTPUT =====")

    try:
        print()
        print("[1/3] RENDER")
        render_assembly(job_dir)

        print()
        print("[2/3] VALIDATE")
        validate_output(job_dir)

        print()
        print("[3/3] UPDATE JOB STAGE")
        update_stage(
            str(job_dir),
            "output",
            "completed",
        )

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
