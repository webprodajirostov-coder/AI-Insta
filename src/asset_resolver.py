import json
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_visual_asset(job_dir, asset_id="visual_001"):
    job_dir = Path(job_dir)

    job = load_json(job_dir / "job.json")
    asset_path = job_dir / "media" / "visual" / f"{asset_id}.json"

    if not asset_path.exists():
        raise FileNotFoundError(f"VisualAsset not found: {asset_path}")

    asset = load_json(asset_path)

    if asset.get("job_id") != job.get("job_id"):
        raise ValueError(
            f"Job mismatch: asset={asset.get('job_id')} "
            f"current={job.get('job_id')}"
        )

    if asset.get("status") != "ready":
        raise RuntimeError(
            f"Visual asset is not ready: status={asset.get('status')}"
        )

    if not asset.get("path"):
        raise RuntimeError("Visual asset has no physical path")

    physical_path = Path(asset["path"])

    if not physical_path.is_absolute():
        physical_path = Path.cwd() / physical_path

    physical_path = physical_path.resolve()
    job_root = job_dir.resolve()

    try:
        physical_path.relative_to(job_root)
    except ValueError:
        raise ValueError(
            f"Visual asset path escapes job directory: {physical_path}"
        )

    if not physical_path.exists():
        raise FileNotFoundError(
            f"Visual file does not exist: {physical_path}"
        )

    return physical_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python src/asset_resolver.py <job_dir>")
        raise SystemExit(1)

    try:
        path = resolve_visual_asset(sys.argv[1])
        print(f"VISUAL RESOLVED: {path}")
    except Exception as e:
        print(f"VISUAL RESOLVE FAILED: {e}")
        raise SystemExit(1)
