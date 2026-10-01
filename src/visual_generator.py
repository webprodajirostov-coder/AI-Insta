import json
from datetime import datetime
from pathlib import Path

from src.providers.odirouter_image_provider import ODIRouterImageProvider


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_visual_assets(asset_dir):
    assets = []

    for path in asset_dir.glob("*.json"):
        asset = load_json(path)

        if asset.get("entity") == "VisualAsset":
            assets.append((path, asset))

    return assets


def generate_visual(
    job_dir,
    provider="odirouter",
    resolution="1k",
    aspect_ratio="9:16",
):
    job_dir = Path(job_dir)

    job = load_json(job_dir / "job.json")
    scenario = load_json(job_dir / "content" / "scenario.json")

    if scenario.get("schema_version") != 2:
        raise ValueError("Visual generation requires Scenario v2")

    scenes = scenario["scenes"]
    if len(scenes) != 1:
        raise ValueError(
            "Current Simple Renderer vertical slice requires exactly one scene"
        )

    visual = scenes[0]["visual"]

    if not visual["generation_required"]:
        print("VISUAL GENERATION: SKIPPED")
        return None

    asset_dir = job_dir / "media" / "visual"
    asset_dir.mkdir(parents=True, exist_ok=True)

    assets = find_visual_assets(asset_dir)

    # Existing assets are authoritative.
    if assets:
        ready = [
            item
            for item in assets
            if item[1].get("status") == "ready"
        ]

        if len(ready) == 1:
            path, asset = ready[0]
            print("VISUAL GENERATION: SKIPPED")
            print("REASON: ready asset already exists")
            print("ASSET:", path)
            return path

        if len(ready) > 1:
            raise ValueError(
                "Multiple ready VisualAssets found: "
                f"{[item[1].get('asset_id') for item in ready]}"
            )

        active = [
            item
            for item in assets
            if item[1].get("status") in {"pending", "generating"}
        ]

        if len(active) == 1:
            path, asset = active[0]
            print("VISUAL GENERATION: SKIPPED")
            print(
                "REASON: existing asset is already",
                asset.get("status"),
            )
            print("ASSET:", path)
            return path

        if len(active) > 1:
            raise ValueError(
                "Multiple active VisualAssets found: "
                f"{[item[1].get('asset_id') for item in active]}"
            )

        failed = [
            item
            for item in assets
            if item[1].get("status") == "failed"
        ]

        if len(failed) > 1:
            raise ValueError(
                "Multiple failed VisualAssets found: "
                f"{[item[1].get('asset_id') for item in failed]}"
            )

        if failed:
            asset_path, existing_asset = failed[0]
            asset_id = existing_asset["asset_id"]
            print("VISUAL GENERATION: RETRY")
            print("REASON: existing asset is failed")
        else:
            raise ValueError(
                "VisualAssets exist, but none has a supported status"
            )

    else:
        asset_id = f"visual_{len(assets) + 1:03d}"
        asset_path = asset_dir / f"{asset_id}.json"
        existing_asset = None

    asset = {
        "schema_version": 1,
        "entity": "VisualAsset",
        "asset_id": asset_id,
        "job_id": job["job_id"],
        "type": visual["type"],
        "status": "pending",
        "source": {
            "provider": provider,
            "prompt": visual.get("prompt_en"),
        },
        "path": None,
        "metadata": {
            "language": scenario["language"],
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
        "provider_job": None,
    }

    if provider == "odirouter":
        image_provider = ODIRouterImageProvider()

        result = image_provider.submit(
            prompt=visual.get("prompt_en"),
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            n=1,
        )

        asset["status"] = "generating"

        asset["provider_job"] = {
            "provider": "odirouter",
            "model": image_provider.MODEL,
            "request_id": result["request_id"],
            "status_url": result["status_url"],
            "response_url": result["response_url"],
        }

    elif provider == "mock":
        asset["status"] = "ready"

    else:
        raise ValueError(f"Unsupported visual provider: {provider}")

    save_json(asset_path, asset)

    print("VISUAL ASSET:", asset_path)
    print("ASSET ID:", asset["asset_id"])
    print("STATUS:", asset["status"])

    if asset["provider_job"]:
        print("PROVIDER:", asset["provider_job"]["provider"])
        print("MODEL:", asset["provider_job"]["model"])
        print("REQUEST ID:", asset["provider_job"]["request_id"])

    return asset_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python src/visual_generator.py <job_dir>")
        raise SystemExit(1)

    try:
        generate_visual(sys.argv[1])
    except Exception as e:
        print(f"VISUAL GENERATION FAILED: {e}")
        raise SystemExit(1)
