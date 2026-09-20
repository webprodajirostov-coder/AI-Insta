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

    audio = scenario.get("audio", {})

    if audio_type == "tts":
        enabled = audio.get("tts", False)
        text = scenario.get("voiceover") or scenario.get("caption", "")
        voice = None
    elif audio_type == "music":
        enabled = audio.get("music", False)
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

    if not scenario.get("audio", {}).get("music", False):
        print("AUDIO GENERATION: SKIPPED (music disabled)")
        return None

    asset_dir = job_dir / "media" / "audio"
    asset_dir.mkdir(parents=True, exist_ok=True)

    asset_id = "music_001"
    audio_path = asset_dir / f"{asset_id}.mp3"
    asset_json_path = asset_dir / f"{asset_id}.json"

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
