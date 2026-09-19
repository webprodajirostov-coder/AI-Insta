import json
import subprocess
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def probe_video(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries",
            "format=duration,size",
            "-show_entries",
            "stream=codec_type,codec_name,width,height,r_frame_rate",
            "-of", "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(result.stdout)


def validate_output(job_dir):
    job_dir = Path(job_dir)

    job = load_json(job_dir / "job.json")
    plan = load_json(job_dir / "assembly" / "assembly_plan.json")

    output_path = Path(plan["output"]["path"])

    if not output_path.exists():
        raise FileNotFoundError(
            f"Output file does not exist: {output_path}"
        )

    data = probe_video(output_path)

    streams = data.get("streams", [])
    video = next(
        (s for s in streams if s.get("codec_type") == "video"),
        None,
    )
    audio = next(
        (s for s in streams if s.get("codec_type") == "audio"),
        None,
    )

    if video is None:
        raise ValueError("Output has no video stream")

    if video.get("codec_name") != "h264":
        raise ValueError(
            f"Invalid video codec: {video.get('codec_name')}"
        )

    if video.get("width") != 1080 or video.get("height") != 1920:
        raise ValueError(
            f"Invalid resolution: "
            f"{video.get('width')}x{video.get('height')}"
        )

    expected_duration = float(
        plan["settings"]["duration_seconds"]
    )

    actual_duration = float(
        data["format"]["duration"]
    )

    if abs(actual_duration - expected_duration) > 0.1:
        raise ValueError(
            f"Invalid duration: "
            f"expected={expected_duration}, "
            f"actual={actual_duration}"
        )

    music_enabled = plan["settings"].get("music", False)

    if music_enabled and audio is None:
        raise ValueError(
            "Music is enabled but output has no audio stream"
        )

    if music_enabled and audio.get("codec_name") != "aac":
        raise ValueError(
            f"Invalid audio codec: "
            f"{audio.get('codec_name')}"
        )

    print("OUTPUT VALID: OK")
    print(f"FILE:       {output_path}")
    print(f"SIZE:       {data['format'].get('size')} bytes")
    print(f"VIDEO:      {video.get('codec_name')}")
    print(
        f"RESOLUTION: "
        f"{video.get('width')}x{video.get('height')}"
    )
    print(f"DURATION:   {actual_duration}s")
    print(
        f"AUDIO:      "
        f"{audio.get('codec_name') if audio else 'none'}"
    )

    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python src/output_validator.py <job_dir>"
        )
        raise SystemExit(1)

    try:
        validate_output(sys.argv[1])
    except Exception as e:
        print(f"OUTPUT INVALID: {e}")
        raise SystemExit(1)
