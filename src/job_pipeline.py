import json
from pathlib import Path


JOB_STATUSES = {"created", "waiting", "completed", "failed"}

JOB_STATUS_TRANSITIONS = {
    "created": {"waiting", "failed"},
    "waiting": {"completed", "failed"},
    "completed": set(),
    "failed": {"waiting", "completed"},
}

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


def load_job(job_dir):
    job_dir = Path(job_dir)
    job_path = job_dir / "job.json"

    if not job_path.exists():
        raise FileNotFoundError(f"Job not found: {job_path}")

    with open(job_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_job(job):
    if not job.get("job_id"):
        raise ValueError("Job has no job_id")

    if not job.get("account_id"):
        raise ValueError("Job has no account_id")

    status = job.get("status")
    if status not in JOB_STATUSES:
        raise ValueError(f"Job has invalid status: {status}")

    pipeline = job.get("pipeline")
    if not isinstance(pipeline, dict):
        raise ValueError("Job has no valid pipeline")

    missing = [stage for stage in PIPELINE_STAGES if stage not in pipeline]
    if missing:
        raise ValueError(f"Job is missing pipeline stages: {missing}")

    return True


def inspect_pipeline(job_dir):
    job = load_job(job_dir)
    validate_job(job)

    print("JOB PIPELINE: VALID")
    print("JOB ID:", job["job_id"])

    for stage in PIPELINE_STAGES:
        print(f"  {stage}: {job['pipeline'][stage]}")

    return job


def resolve_visual_stage(job_dir):
    job_dir = Path(job_dir)

    assets_dir = job_dir / "media" / "visual"
    candidates = []

    for asset_path in assets_dir.glob("*.json"):
        with open(asset_path, "r", encoding="utf-8") as f:
            asset = json.load(f)

        if asset.get("entity") == "VisualAsset":
            candidates.append((asset_path, asset))

    if not candidates:
        print("VISUAL STAGE: NO ASSET")
        print("ACTION: GENERATE")
        return "generate", None

    if len(candidates) > 1:
        ready = [
            item for item in candidates
            if item[1].get("status") == "ready"
        ]

        if len(ready) == 1:
            candidates = ready
        elif len(ready) > 1:
            raise ValueError(
                f"Multiple ready VisualAssets found: "
                f"{[item[1].get('asset_id') for item in ready]}"
            )

    asset_path, asset = candidates[0]
    status = asset.get("status")

    if status == "ready":
        from src.asset_resolver import resolve_visual_asset

        image_path = resolve_visual_asset(job_dir, asset["asset_id"])

        print("VISUAL STAGE: READY")
        print("ACTION: SKIP GENERATION")
        print("FILE:", image_path)
        return "ready", asset["asset_id"]

    if status == "generating":
        print("VISUAL STAGE: GENERATING")
        print("ACTION: POLL")
        return "poll", asset["asset_id"]

    if status == "pending":
        print("VISUAL STAGE: PENDING")
        print("ACTION: GENERATE")
        return "generate", asset["asset_id"]

    if status == "failed":
        print("VISUAL STAGE: FAILED")
        print("ACTION: STOP")
        return "failed", asset["asset_id"]

    raise ValueError(f"Unknown VisualAsset status: {status}")


def run_visual_stage(job_dir):
    job_dir = Path(job_dir)
    action, asset_id = resolve_visual_stage(job_dir)

    if action == "ready":
        return "completed"

    if action == "poll":
        from src.visual_poller import poll_visual

        ready = poll_visual(job_dir, asset_id=asset_id)
        return "completed" if ready else "waiting"

    if action == "generate":
        from src.visual_generator import generate_visual

        generate_visual(job_dir, provider="odirouter")
        return "waiting"

    if action == "failed":
        raise RuntimeError("VisualAsset is in failed state")

    raise RuntimeError(f"Unsupported visual action: {action}")


def run_audio_stage(job_dir):
    job_dir = Path(job_dir)

    job = load_job(job_dir)
    scenario = load_json(job_dir / "content" / "scenario.json")
    audio_config = scenario.get("audio", {})

    music_enabled = audio_config.get("music", False)
    tts_enabled = audio_config.get("tts", False)

    if not music_enabled and not tts_enabled:
        print("AUDIO STAGE: nothing enabled")
        return "skipped"

    from src.audio_resolver import resolve_audio_asset

    assets_dir = job_dir / "media" / "audio"
    candidates = []

    for asset_path in assets_dir.glob("*.json"):
        with open(asset_path, "r", encoding="utf-8") as f:
            asset = json.load(f)

        if asset.get("entity") == "AudioAsset":
            candidates.append((asset_path, asset))

    ready = [
        item for item in candidates
        if item[1].get("status") == "ready"
    ]

    if len(ready) > 1:
        raise ValueError(
            f"Multiple ready AudioAssets found: "
            f"{[item[1].get('asset_id') for item in ready]}"
        )

    if len(ready) == 1:
        asset_id = ready[0][1]["asset_id"]
        audio_path = resolve_audio_asset(job_dir, asset_id)

        print("AUDIO STAGE: READY")
        print("ACTION: SKIP GENERATION")
        print("FILE:", audio_path)

        return "completed"

    if music_enabled:
        from src.audio_generator import generate_mock_music

        print("AUDIO STAGE: NO READY MUSIC")
        print("ACTION: GENERATE MOCK MUSIC")

        generate_mock_music(
            job_dir,
            duration_seconds=scenario.get("duration_seconds", 8),
        )

        ready = [
            item
            for item in assets_dir.glob("*.json")
            if load_json(item).get("entity") == "AudioAsset"
            and load_json(item).get("status") == "ready"
        ]

        if len(ready) != 1:
            raise RuntimeError("Audio generation did not produce one ready AudioAsset")

        asset_id = load_json(ready[0])["asset_id"]
        audio_path = resolve_audio_asset(job_dir, asset_id)

        print("AUDIO STAGE: COMPLETED")
        print("FILE:", audio_path)

        return "completed"

    if tts_enabled:
        raise RuntimeError(
            "TTS is enabled, but no TTS audio provider is implemented"
        )

    return "skipped"


def run_ready_pipeline(job_dir):
    job_dir = Path(job_dir)
    job = load_job(job_dir)
    validate_job(job)

    print("===== READY PIPELINE =====")

    # AUDIO
    if job["pipeline"]["audio"] == "completed":
        print("AUDIO: already completed")
    else:
        from src.audio_resolver import resolve_audio_asset

        assets_dir = job_dir / "media" / "audio"
        candidates = []

        for asset_path in assets_dir.glob("*.json"):
            with open(asset_path, "r", encoding="utf-8") as f:
                asset = json.load(f)

            if asset.get("entity") == "AudioAsset":
                candidates.append((asset_path, asset))

        if not candidates:
            raise FileNotFoundError(
                f"No AudioAsset found in: {assets_dir}"
            )

        ready = [
            item for item in candidates
            if item[1].get("status") == "ready"
        ]

        if len(ready) == 1:
            audio_asset = ready[0][1]
        elif len(ready) > 1:
            raise ValueError(
                f"Multiple ready AudioAssets found: "
                f"{[item[1].get('asset_id') for item in ready]}"
            )
        else:
            raise RuntimeError("No ready AudioAsset found")

        resolve_audio_asset(job_dir, audio_asset["asset_id"])
        from src.update_job_stage import update_stage
        update_stage(job_dir, "audio", "completed")
        print("AUDIO: completed")

    # VISUAL
    visual_result = run_visual_stage(job_dir)

    if visual_result == "waiting":
        print("VISUAL: waiting for provider")
        return False

    from src.update_job_stage import update_stage
    update_stage(job_dir, "visual", "completed")
    print("VISUAL: completed")

    # ASSEMBLY
    job = load_job(job_dir)

    if job["pipeline"]["assembly"] == "completed":
        print("ASSEMBLY: already completed")
    else:
        from src.assembly import build_assembly_plan
        from src.assembly_runner import run_assembly

        build_assembly_plan(job_dir)
        run_assembly(job_dir)
        update_stage(job_dir, "assembly", "completed")
        print("ASSEMBLY: completed")

    # OUTPUT
    job = load_job(job_dir)

    if job["pipeline"]["output"] == "completed":
        print("OUTPUT: already completed")
    else:
        from src.finalizer import finalize

        if not finalize(job_dir):
            return False

        print("OUTPUT: completed")

    print("=========================")
    return True

def dry_run_pipeline(job_dir):
    job_dir = Path(job_dir)

    job = load_job(job_dir)
    validate_job(job)

    print("===== PIPELINE DRY RUN =====")
    print("JOB:", job["job_id"])

    # AUDIO STAGE
    scenario = load_json(job_dir / "content" / "scenario.json")
    music_enabled = scenario.get("audio", {}).get("music", False)

    if music_enabled:
        try:
            audio_path = resolve_audio_asset(job_dir)
            print(f"AUDIO: ready -> {audio_path}")
        except Exception:
            print("AUDIO: no ready music asset")
            generate_mock_music(job_dir)
            audio_path = resolve_audio_asset(job_dir)
            print(f"AUDIO: ready -> {audio_path}")
    else:
        print("AUDIO: music disabled")

    visual_action, visual_asset_id = resolve_visual_stage(job_dir)

    if visual_action == "ready":
        print("VISUAL: ready")
        print("ACTION: SKIP GENERATION")

    elif visual_action == "pending":
        print("VISUAL: pending")
        print("ACTION: WOULD GENERATE")
        print("PROVIDER: odirouter")
        print("MODEL: kling-v3-image")

    elif visual_action == "poll":
        print("VISUAL: generating")
        print("ACTION: WOULD POLL")

    elif visual_action == "failed":
        print("VISUAL: failed")
        print("ACTION: STOP")

    print("DRY RUN: NO PROVIDER REQUEST SENT")
    print("============================")
    return True

def run_pipeline(job_dir):
    job_dir = Path(job_dir)

    job = load_job(job_dir)
    validate_job(job)

    # Idempotency guard:
    # a completed job must not rewrite its state or rerun any stage.
    if job.get("status") == "completed":
        output_path = job.get("artifacts", {}).get("output")

        if output_path and Path(output_path).exists():
            print("===== FULL PIPELINE =====")
            print("JOB:", job["job_id"])
            print("JOB STATUS: completed")
            print("ACTION: SKIP — JOB ALREADY COMPLETED")
            print("OUTPUT:", output_path)
            print("========================")
            return True

    print("===== FULL PIPELINE =====")
    print("JOB:", job["job_id"])

    from src.update_job_stage import update_stage

    try:
        # =========================
        # AUDIO
        # =========================
        job = load_job(job_dir)

        if job["pipeline"]["audio"] == "completed":
            print("AUDIO: already completed")
        else:
            audio_result = run_audio_stage(job_dir)

            if audio_result == "completed":
                update_stage(job_dir, "audio", "completed")
                print("AUDIO: completed")

            elif audio_result == "skipped":
                update_stage(job_dir, "audio", "skipped")
                print("AUDIO: skipped")

        # =========================
        # VISUAL
        # =========================
        visual_action, visual_asset_id = resolve_visual_stage(job_dir)

        if visual_action == "ready":
            update_stage(job_dir, "visual", "completed")
            print("VISUAL: completed")

        elif visual_action in {"generate", "poll"}:
            result = run_visual_stage(job_dir)

            if result == "waiting":
                update_stage(job_dir, "visual", "waiting")
                update_job_state(job_dir, status="waiting")
                print("VISUAL: waiting")
                print("========================")
                return False

            update_stage(job_dir, "visual", "completed")
            print("VISUAL: completed")

        elif visual_action == "failed":
            update_stage(job_dir, "visual", "failed")
            raise RuntimeError("Visual stage failed")

        # =========================
        # ASSEMBLY
        # =========================
        job = load_job(job_dir)

        if job["pipeline"]["assembly"] != "completed":
            from src.assembly import build_assembly_plan
            from src.assembly_runner import run_assembly

            print("ASSEMBLY: building plan")
            build_assembly_plan(job_dir)

            print("ASSEMBLY: validating inputs")
            run_assembly(job_dir)

            update_stage(job_dir, "assembly", "completed")
            print("ASSEMBLY: completed")
        else:
            print("ASSEMBLY: already completed")

        # =========================
        # OUTPUT
        # =========================
        job = load_job(job_dir)

        if job["pipeline"]["output"] != "completed":
            from src.finalizer import finalize

            print("OUTPUT: rendering + validation")

            if not finalize(job_dir):
                update_job_state(
                    job_dir,
                    status="failed",
                    error="Output finalization failed",
                )
                print("OUTPUT: failed")
                return False

            print("OUTPUT: completed")
        else:
            print("OUTPUT: already completed")

        # =========================
        # COMPLETED
        # =========================
        output_path = (
            job_dir / "output" / "final.mp4"
        )

        update_job_state(
            job_dir,
            status="completed",
            output_path=output_path,
        )

        print("JOB STATUS: completed")
        print("========================")
        return True

    except Exception as e:
        update_job_state(
            job_dir,
            status="failed",
            error=e,
        )
        print("JOB STATUS: failed")
        print("ERROR:", e)
        print("========================")
        return False

def update_job_state(job_dir, status=None, output_path=None, error=None):
    job_dir = Path(job_dir)
    job_path = job_dir / "job.json"

    job = load_job(job_dir)

    if status is not None:
        if status not in JOB_STATUSES:
            raise ValueError(f"Invalid job status: {status}")

        current_status = job.get("status")
        if status != current_status and status not in JOB_STATUS_TRANSITIONS.get(current_status, set()):
            raise ValueError(
                f"Invalid job status transition: {current_status} -> {status}"
            )

        job["status"] = status

    if output_path is not None:
        job.setdefault("artifacts", {})
        job["artifacts"]["output"] = str(Path(output_path).resolve())

    if error is not None:
        job["error"] = str(error)
    else:
        job["error"] = None

    from datetime import datetime

    job["updated_at"] = datetime.now().isoformat(timespec="seconds")

    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)

    return job

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m src.job_pipeline <job_dir>")
        raise SystemExit(1)

    job_dir = sys.argv[1]

    try:
        result = run_pipeline(job_dir)
    except Exception as e:
        print("PIPELINE ERROR:", e)
        raise SystemExit(1)

    raise SystemExit(0 if result else 1)
