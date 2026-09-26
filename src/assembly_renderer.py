import json
from pathlib import Path

from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
)


TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


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


def overlay_position(position):
    positions = {
        "top": ("center", 180),
        "center": ("center", "center"),
        "bottom": ("center", 1600),
    }
    return positions.get(position, ("center", "center"))


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

    if plan.get("schema_version") != 2:
        raise ValueError("Renderer requires AssemblyPlan v2")

    scenes = plan.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("AssemblyPlan has no scenes")

    if len(scenes) != 1:
        raise ValueError(
            "Simple Renderer currently supports exactly one scene"
        )

    scene = scenes[0]

    visual_path = ensure_path_inside_job(
        job_dir,
        scene["visual"].get("asset_path"),
        "Visual asset",
    )
    if visual_path is None or not visual_path.exists():
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
        plan["output"].get("path"),
        "Output",
    )
    if output_path is None:
        raise ValueError("AssemblyPlan output path is required")

    duration = scene["duration_seconds"]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"RENDER SCENE: {scene['scene_id']}")
    print(f"RENDER VISUAL: {visual_path}")
    print(f"RENDER MUSIC:  {music_path}")
    print(f"RENDER OUTPUT: {output_path}")
    print(f"DURATION:      {duration}s")

    video = (
        ImageClip(str(visual_path))
        .with_duration(duration)
        .resized(height=TARGET_HEIGHT)
    )

    video = video.cropped(
        x_center=video.w / 2,
        y_center=video.h / 2,
        width=TARGET_WIDTH,
        height=TARGET_HEIGHT,
    )

    layers = [video]

    overlay = scene.get("text_overlay")
    hook_overlay_enabled = plan["settings"].get("hook_overlay", False)

    if hook_overlay_enabled and overlay and overlay.get("text"):
        text_clip = (
            TextClip(
                text=overlay["text"],
                font_size=64,
                color="white",
                method="caption",
                size=(int(TARGET_WIDTH * 0.86), None),
            )
            .with_duration(duration)
            .with_position(overlay_position(overlay.get("position")))
        )
        layers.append(text_clip)

    if music_path:
        audio = AudioFileClip(str(music_path)).subclipped(0, duration)
        video = video.with_audio(audio)
        layers[0] = video

    final = CompositeVideoClip(
        layers,
        size=(TARGET_WIDTH, TARGET_HEIGHT),
    )

    final.write_videofile(
        str(output_path),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        logger="bar",
    )

    final.close()
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
