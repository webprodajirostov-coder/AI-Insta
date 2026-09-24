import json
from pathlib import Path

from src.asset_resolver import resolve_visual_asset
from src.audio_resolver import resolve_audio_asset


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_asset_id(job_dir, asset_type):
    job_dir = Path(job_dir)
    assets_dir = job_dir / "media"

    matches = []

    for path in assets_dir.glob("*/*.json"):
        asset = load_json(path)

        if (
            asset.get("entity") in {"VisualAsset", "AudioAsset"}
            and asset.get("type") == asset_type
            and asset.get("status") == "ready"
        ):
            matches.append(asset.get("asset_id"))

    matches = [asset_id for asset_id in matches if asset_id]

    if not matches:
        raise FileNotFoundError(
            f"No ready asset found for type={asset_type}"
        )

    if len(matches) > 1:
        raise ValueError(
            f"Multiple ready assets found for type={asset_type}: {matches}"
        )

    return matches[0]


def build_assembly_plan(job_dir):
    job_dir = Path(job_dir)

    job = load_json(job_dir / "job.json")
    scenario = load_json(job_dir / "content" / "scenario.json")

    if scenario.get("schema_version") != 2:
        raise ValueError("Assembly requires Scenario v2")

    profile_name = scenario["production_profile"]
    profile_path = Path("data/production_profiles") / f"{profile_name}.json"
    profile = load_json(profile_path)

    scenes = scenario["scenes"]
    if len(scenes) != 1:
        raise ValueError(
            "Current Simple Renderer vertical slice requires exactly one scene"
        )

    scene = scenes[0]
    visual = scene["visual"]

    music_asset_path = None
    if profile["audio"]["music"]:
        music_asset_id = find_asset_id(job_dir, "music")
        music_asset_path = str(
            resolve_audio_asset(job_dir, music_asset_id)
        )

    visual_asset_id = find_asset_id(job_dir, visual["type"])
    visual_asset_path = resolve_visual_asset(job_dir, visual_asset_id)

    overlay = scene["text_overlay"]
    overlay_text = overlay["text"] if overlay is not None else None

    plan = {
        "schema_version": 1,
        "entity": "AssemblyPlan",
        "job_id": job["job_id"],
        "scenario_id": scenario["scenario_id"],
        "production_profile": profile["profile_id"],
        "language": scenario["language"],
        "inputs": {
            "visual": {
                "type": visual["type"],
                "generation_required": visual["generation_required"],
                "prompt_en": visual.get("prompt_en"),
                "asset_id": visual_asset_id,
                "asset_path": str(visual_asset_path),
            },
            "audio": {
                "tts": {
                    "enabled": profile["audio"]["tts"],
                    "asset_path": None,
                },
                "music": {
                    "enabled": profile["audio"]["music"],
                    "asset_path": music_asset_path,
                },
            },
            "text": {
                "hook": scenario["hook"],
                "overlay": overlay_text,
                "caption": scenario["caption"],
            },
        },
        "settings": {
            "duration_seconds": scenario["duration_seconds"],
            "transitions": scenario["assembly"]["transitions"],
            "animation": scenario["assembly"]["animation"],
            "hook_overlay": profile["text"]["hook_overlay"],
            "subtitles": profile["text"]["subtitles"],
            "dynamic_subtitles": profile["text"]["dynamic_subtitles"],
            "tts": profile["audio"]["tts"],
            "music": profile["audio"]["music"],
        },
        "output": {
            "format": "mp4",
            "path": str(job_dir / "output" / "final.mp4"),
        },
    }

    assembly_dir = job_dir / "assembly"
    assembly_dir.mkdir(parents=True, exist_ok=True)

    assembly_path = assembly_dir / "assembly_plan.json"
    with open(assembly_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    return plan


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python src/assembly.py <job_dir>")
        raise SystemExit(1)

    plan = build_assembly_plan(sys.argv[1])
    print(json.dumps(plan, ensure_ascii=False, indent=2))
