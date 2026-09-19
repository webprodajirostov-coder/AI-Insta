import json
from pathlib import Path

from moviepy import ImageClip, AudioFileClip


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_assembly(job_dir):
    job_dir = Path(job_dir)

    plan_path = job_dir / "assembly" / "assembly_plan.json"

    if not plan_path.exists():
        raise FileNotFoundError(
            f"AssemblyPlan not found: {plan_path}"
        )

    plan = load_json(plan_path)

    if plan.get("entity") != "AssemblyPlan":
        raise ValueError("Invalid AssemblyPlan entity")

    visual_path = Path(
        plan["inputs"]["visual"]["asset_path"]
    )

    music_path = plan["inputs"]["audio"]["music"].get(
        "asset_path"
    )

    if not visual_path.exists():
        raise FileNotFoundError(
            f"Visual asset does not exist: {visual_path}"
        )

    if music_path and not Path(music_path).exists():
        raise FileNotFoundError(
            f"Music asset does not exist: {music_path}"
        )

    duration = plan["settings"]["duration_seconds"]

    output_path = Path(plan["output"]["path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"RENDER VISUAL: {visual_path}")
    print(f"RENDER MUSIC:  {music_path}")
    print(f"RENDER OUTPUT: {output_path}")
    print(f"DURATION:      {duration}s")

    video = (
        ImageClip(str(visual_path))
        .with_duration(duration)
        .resized(height=1920)
    )

    video = video.cropped(
        x_center=video.w / 2,
        y_center=video.h / 2,
        width=1080,
        height=1920,
    )

    if music_path:
        audio = AudioFileClip(
            str(music_path)
        ).subclipped(0, duration)

        video = video.with_audio(audio)

    video.write_videofile(
        str(output_path),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        logger="bar",
    )

    video.close()

    print(f"RENDER COMPLETE: {output_path}")

    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python src/assembly_renderer.py <job_dir>"
        )
        raise SystemExit(1)

    try:
        render_assembly(sys.argv[1])
    except Exception as e:
        print(f"RENDER FAILED: {e}")
        raise SystemExit(1)
