"""Application-level orchestration for a production Job.

This module coordinates stage execution and Job lifecycle transitions.
Stage implementations and lifecycle helpers remain in their dedicated
modules; this class only decides what runs next.
"""

from pathlib import Path

from src.job_pipeline import (
    JOB_STATUSES,
    load_job,
    materialize_preproduction_stages,
    resolve_visual_stage,
    run_audio_stage,
    run_visual_stage,
    update_job_state,
    validate_completed_job,
    validate_job,
)
from src.update_job_stage import update_stage


class PipelineOrchestrator:
    """Coordinate the full production pipeline for one isolated Job."""

    def __init__(self, job_dir):
        self.job_dir = Path(job_dir)

    def run(self):
        job = load_job(self.job_dir)
        validate_job(job)

        if job.get("status") == "failed":
            self._print_terminal("failed")
            return False

        if job.get("status") == "completed":
            validate_completed_job(self.job_dir, job)
            self._print_completed(job)
            return True

        print("===== FULL PIPELINE =====")
        print("JOB:", job["job_id"])

        active_stage = None

        try:
            materialize_preproduction_stages(self.job_dir)

            active_stage = "audio"
            self._run_audio()

            active_stage = "visual"
            if not self._run_visual():
                return False

            active_stage = "assembly"
            self._run_assembly()

            active_stage = "output"
            if not self._run_output():
                return False

            job = load_job(self.job_dir)
            validate_completed_job(self.job_dir, job)

            print("JOB STATUS: completed")
            print("========================")
            return True

        except Exception as error:
            if active_stage:
                self._fail_stage(active_stage)

            update_job_state(
                self.job_dir,
                status="failed",
                error=error,
            )
            print("JOB STATUS: failed")
            print("ERROR:", error)
            print("========================")
            return False

    def _run_audio(self):
        job = load_job(self.job_dir)

        if job["pipeline"]["audio"] == "completed":
            print("AUDIO: already completed")
            return

        result = run_audio_stage(self.job_dir)

        if result == "completed":
            update_stage(self.job_dir, "audio", "completed")
            print("AUDIO: completed")
            return

        if result == "skipped":
            raise RuntimeError("Audio stage cannot be skipped")

        raise RuntimeError(f"Unsupported audio stage result: {result}")

    def _run_visual(self):
        job = load_job(self.job_dir)

        if job["pipeline"]["visual"] == "failed":
            print("VISUAL: failed")
            print("ACTION: SKIP — VISUAL STAGE ALREADY FAILED")
            print("========================")
            return False

        visual_action, visual_asset_id = resolve_visual_stage(self.job_dir)

        if visual_action == "ready":
            update_stage(self.job_dir, "visual", "completed")
            print("VISUAL: completed")
            return True

        if visual_action in {"generate", "poll"}:
            result = run_visual_stage(self.job_dir)

            if result == "waiting":
                update_stage(self.job_dir, "visual", "waiting")
                update_job_state(self.job_dir, status="waiting")
                print("VISUAL: waiting")
                print("========================")
                return False

            update_stage(self.job_dir, "visual", "completed")
            print("VISUAL: completed")
            return True

        if visual_action == "failed":
            update_stage(self.job_dir, "visual", "failed")
            update_job_state(
                self.job_dir,
                status="failed",
                error=(
                    "Visual stage failed: generation is disabled "
                    "and no ready VisualAsset exists"
                ),
            )
            print("VISUAL: failed")
            print("JOB STATUS: failed")
            print("========================")
            return False

        raise RuntimeError(
            f"Unsupported visual action: {visual_action} "
            f"(asset={visual_asset_id})"
        )

    def _run_assembly(self):
        job = load_job(self.job_dir)

        if job["pipeline"]["assembly"] == "completed":
            print("ASSEMBLY: already completed")
            return

        from src.assembly import build_assembly_plan
        from src.assembly_runner import run_assembly

        print("ASSEMBLY: building plan")
        build_assembly_plan(self.job_dir)

        print("ASSEMBLY: validating inputs")
        run_assembly(self.job_dir)

        update_stage(self.job_dir, "assembly", "completed")
        print("ASSEMBLY: completed")

    def _run_output(self):
        job = load_job(self.job_dir)

        if job["pipeline"]["output"] != "completed":
            from src.finalizer import finalize

            print("OUTPUT: rendering + validation")

            if not finalize(self.job_dir):
                update_job_state(
                    self.job_dir,
                    status="failed",
                    error="Output finalization failed",
                )
                print("OUTPUT: failed")
                return False

            print("OUTPUT: completed")
            return True

        print("OUTPUT: already completed")
        return True

    def _fail_stage(self, stage):
        job = load_job(self.job_dir)

        if job["pipeline"].get(stage) == "failed":
            return

        update_stage(self.job_dir, stage, "failed")

    @staticmethod
    def _print_terminal(status):
        print("===== FULL PIPELINE =====")
        print("JOB STATUS:", status)
        print("ACTION: SKIP — JOB ALREADY FAILED")
        print("========================")

    @staticmethod
    def _print_completed(job):
        print("===== FULL PIPELINE =====")
        print("JOB:", job["job_id"])
        print("JOB STATUS: completed")
        print("ACTION: SKIP — JOB ALREADY COMPLETED")
        print("OUTPUT:", job["artifacts"]["output"])
        print("========================")
