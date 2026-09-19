import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_visual_asset(job_dir, asset_id=None):
    asset_dir = Path(job_dir) / "media" / "visual"

    candidates = []

    for asset_path in asset_dir.glob("*.json"):
        asset = load_json(asset_path)

        if asset.get("entity") != "VisualAsset":
            continue

        if asset_id and asset.get("asset_id") != asset_id:
            continue

        candidates.append((asset_path, asset))

    if not candidates:
        raise FileNotFoundError(
            f"No VisualAsset found in: {asset_dir}"
        )

    if len(candidates) > 1:
        raise ValueError(
            "Multiple matching VisualAssets found: "
            f"{[item[1].get('asset_id') for item in candidates]}"
        )

    return candidates[0]


def poll_visual(job_dir, asset_id=None):
    job_dir = Path(job_dir)

    load_dotenv(Path(".env").resolve())

    api_key = os.getenv("ODIROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("ODIROUTER_API_KEY is not configured")

    asset_path, asset = find_visual_asset(job_dir, asset_id)

    status = asset.get("status")

    if status == "ready":
        print("VISUAL POLLER: SKIPPED")
        print("REASON: asset is already ready")
        print("ASSET:", asset["asset_id"])
        return True

    if status not in {"generating", "pending"}:
        raise RuntimeError(
            f"VisualAsset cannot be polled: status={status}"
        )

    provider_job = asset.get("provider_job")

    if not provider_job:
        raise ValueError(
            f"VisualAsset {asset['asset_id']} has no provider_job"
        )

    status_url = provider_job.get("status_url")
    response_url = provider_job.get("response_url")

    if not status_url or not response_url:
        raise ValueError(
            f"VisualAsset {asset['asset_id']} has incomplete provider_job"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    status_response = requests.get(
        status_url,
        headers=headers,
        timeout=60,
    )
    status_response.raise_for_status()

    status_data = status_response.json()
    provider_status = str(
        status_data.get("status", "")
    ).lower()

    print("STATUS:", provider_status)

    if provider_status != "completed":
        if provider_status in {"failed", "cancelled"}:
            asset["status"] = "failed"
            save_json(asset_path, asset)

            raise RuntimeError(
                f"OdiRouter task failed: {provider_status}"
            )

        asset["status"] = "generating"
        save_json(asset_path, asset)

        print("VISUAL: STILL PROCESSING")
        return False

    response = requests.get(
        response_url,
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()

    result = response.json()

    content = result["output"][0]["content"][0]

    if content.get("type") != "image":
        raise ValueError(
            "OdiRouter response does not contain an image"
        )

    image_url = content["url"]

    image_response = requests.get(
        image_url,
        headers=headers,
        timeout=120,
    )
    image_response.raise_for_status()

    output_path = (
        job_dir
        / "media"
        / "visual"
        / f"{asset['asset_id']}.png"
    )

    output_path.write_bytes(image_response.content)

    asset["status"] = "ready"
    asset["path"] = str(output_path.resolve())

    asset.setdefault("metadata", {})
    asset["metadata"]["provider_job_id"] = content.get("jobId")
    asset["metadata"]["completed"] = True

    save_json(asset_path, asset)

    print("VISUAL: READY")
    print("ASSET:", asset["asset_id"])
    print("FILE:", output_path)
    print("SIZE:", output_path.stat().st_size, "bytes")

    return True
