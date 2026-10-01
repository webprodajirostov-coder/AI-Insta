import json
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_path_inside_job(job_dir, path, label):
    if not path:
        return None

    physical_path = Path(path)

    if not physical_path.is_absolute():
        physical_path = Path.cwd() / physical_path

    physical_path = physical_path.resolve()
    job_root = Path(job_dir).resolve()

    try:
        physical_path.relative_to(job_root)
    except ValueError:
        raise ValueError(
            f"{label} path escapes job directory: {physical_path}"
        )

    return physical_path


def run_assembly(job_dir):
    job_dir = Path(job_dir)

    plan_path = job_dir / "assembly" / "assembly_plan.json"

    if not plan_path.exists():
        raise FileNotFoundError(
            f"AssemblyPlan not found: {plan_path}"
        )

    plan = load_json(plan_path)

    if plan.get("entity") != "AssemblyPlan":
        raise ValueError("Invalid AssemblyPlan entity")

    if plan.get("schema_version") != 2:
        raise ValueError("Assembly requires AssemblyPlan v2")

    if plan.get("job_id") != load_json(job_dir / "job.json").get("job_id"):
        raise ValueError("AssemblyPlan job_id mismatch")

    scenes = plan.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("AssemblyPlan has no scenes")

    for scene in scenes:
        visual_path = ensure_path_inside_job(
            job_dir,
            scene["visual"].get("asset_path"),
            f"Visual asset for scene {scene['scene_id']}",
        )

        if visual_path and not visual_path.exists():
            raise FileNotFoundError(
                f"Visual asset does not exist: {visual_path}"
            )

    music_path = ensure_path_inside_job(
        job_dir,
        plan["inputs"]["audio"]["music"].get("asset_path"),
        "Music asset",
    )

    if music_path and not music_path.exists():
        raise FileNotFoundError(
            f"Music asset does not exist: {music_path}"
        )

    output_path = ensure_path_inside_job(
        job_dir,
        plan["output"]["path"],
        "Output",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("ASSEMBLY INPUTS: OK")
    for scene in scenes:
        print(
            f"SCENE {scene['order']}: "
            f"{scene['scene_id']} -> {scene['visual'].get('asset_path')}"
        )
    print(f"MUSIC:  {music_path}")
    print(f"OUTPUT: {output_path}")

    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python src/assembly_runner.py <job_dir>")
        raise SystemExit(1)

    try:
        run_assembly(sys.argv[1])
    except Exception as e:
        print(f"ASSEMBLY FAILED: {e}")
        raise SystemExit(1)
