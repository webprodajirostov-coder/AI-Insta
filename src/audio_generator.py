import json
from pathlib import Path
from datetime import datetime


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_audio(job_dir, audio_type="tts", provider="mock"):
    job_dir = Path(job_dir)

    job = load_json(job_dir / "job.json")
    scenario = load_json(job_dir / "content" / "scenario.json")

    profile_name = scenario["production_profile"]
    profile_path = Path("data/production_profiles") / f"{profile_name}.json"
    profile = load_json(profile_path)
    audio = profile["audio"]

    if audio_type == "tts":
        enabled = audio["tts"]
        text = scenario.get("voiceover") or scenario.get("caption", "")
        voice = None
    elif audio_type == "music":
        enabled = audio["music"]
        text = None
        voice = None
    else:
        raise ValueError(f"Unknown audio type: {audio_type}")

    if not enabled:
        print(f"AUDIO GENERATION: SKIPPED ({audio_type})")
        return None

    asset_dir = job_dir / "media" / "audio"
    asset_dir.mkdir(parents=True, exist_ok=True)

    asset_id = f"{audio_type}_001"

    asset = {
        "schema_version": 1,
        "entity": "AudioAsset",
        "asset_id": asset_id,
        "job_id": job["job_id"],
        "type": audio_type,
        "status": "pending",
        "source": {
            "provider": provider,
            "text": text,
            "voice": voice
        },
        "path": None,
        "metadata": {
            "language": scenario["language"],
            "created_at": datetime.now().isoformat(timespec="seconds")
        }
    }

    asset_path = asset_dir / f"{asset_id}.json"

    with open(asset_path, "w", encoding="utf-8") as f:
        json.dump(asset, f, ensure_ascii=False, indent=2)

    return asset_path


def generate_mock_music(job_dir, duration_seconds=8):
    job_dir = Path(job_dir)

    job = load_json(job_dir / "job.json")
    scenario = load_json(job_dir / "content" / "scenario.json")

    profile_name = scenario["production_profile"]
    profile_path = Path("data/production_profiles") / f"{profile_name}.json"
    profile = load_json(profile_path)

    if not profile["audio"]["music"]:
        print("AUDIO GENERATION: SKIPPED (music disabled)")
        return None

    asset_dir = job_dir / "media" / "audio"
    asset_dir.mkdir(parents=True, exist_ok=True)

    existing_assets = []

    for asset_json in sorted(asset_dir.glob("*.json")):
        try:
            asset = load_json(asset_json)
        except Exception:
            continue

        if asset.get("entity") == "AudioAsset" and asset.get("type") == "music":
            existing_assets.append((asset_json, asset))

    active = [
        item
        for item in existing_assets
        if item[1].get("status") in {"pending", "generating", "ready"}
    ]

    if len(active) > 1:
        raise ValueError(
            "Multiple active AudioAssets found: "
            f"{[item[1].get('asset_id') for item in active]}"
        )

    failed = [
        item
        for item in existing_assets
        if item[1].get("status") == "failed"
    ]

    if len(failed) > 1:
        raise ValueError(
            "Multiple failed AudioAssets found: "
            f"{[item[1].get('asset_id') for item in failed]}"
        )

    if active:
        asset_json_path, existing_asset = active[0]
        asset_id = existing_asset["asset_id"]

        if existing_asset.get("status") == "ready":
            print("AUDIO GENERATION: SKIP")
            print("REASON: existing asset is already ready")
            return asset_json_path

        if existing_asset.get("status") in {"pending", "generating"}:
            print("AUDIO GENERATION: SKIP")
            print(
                "REASON: existing asset is already",
                existing_asset.get("status"),
            )
            return asset_json_path
    elif failed:
        asset_json_path, existing_asset = failed[0]
        asset_id = existing_asset["asset_id"]
        print("AUDIO GENERATION: RETRY")
        print("REASON: existing asset is failed")
    else:
        asset_id = f"music_{len(existing_assets) + 1:03d}"
        asset_json_path = asset_dir / f"{asset_id}.json"

    audio_path = asset_dir / f"{asset_id}.mp3"

    import subprocess

    command = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=220:sample_rate=44100",
        "-t", str(duration_seconds),
        "-af", "volume=0.04",
        "-codec:a", "libmp3lame",
        "-b:a", "128k",
        str(audio_path),
    ]

    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    asset = {
        "schema_version": 1,
        "entity": "AudioAsset",
        "asset_id": asset_id,
        "job_id": job["job_id"],
        "type": "music",
        "status": "ready",
        "source": {
            "provider": "mock",
            "text": None,
            "voice": None,
        },
        "path": str(audio_path),
        "metadata": {
            "language": scenario["language"],
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    with open(asset_json_path, "w", encoding="utf-8") as f:
        json.dump(asset, f, ensure_ascii=False, indent=2)

    print("AUDIO: mock music generated")
    print("FILE:", audio_path)

    return asset_json_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print(
            "Usage: python src/audio_generator.py "
            "<job_dir> <tts|music>"
        )
        raise SystemExit(1)

    result = generate_audio(sys.argv[1], sys.argv[2])

    if result:
        print(f"AUDIO ASSET: {result}")
