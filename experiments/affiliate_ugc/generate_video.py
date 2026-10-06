import argparse
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.odirouter.ai"
DEFAULT_MODEL = "viduq3-pro-img2video"


def api_headers():
    key = os.getenv("ODIROUTER_API_KEY")
    if not key:
        raise RuntimeError("ODIROUTER_API_KEY is not configured")
    return {"Authorization": f"Bearer {key}"}


def upload_image(path: Path) -> str:
    with path.open("rb") as f:
        r = requests.post(
            f"{BASE_URL}/v1/files",
            headers=api_headers(),
            files={"file": (path.name, f, "application/octet-stream")},
            timeout=120,
        )
    r.raise_for_status()
    data = r.json()
    url = data.get("url")
    if not url:
        raise RuntimeError(f"Upload response has no url: {data}")
    return url


def submit(image_url: str, prompt: str, model: str, duration: int,
           resolution: str, aspect_ratio: str) -> dict:
    if model == "kling-v3-i2v":
        payload = {
            "image": image_url,
            "prompt": prompt,
            "duration": duration,
            "sound": False,
        }
    elif model == "seedance-2-0-fast":
        payload = {
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                    "role": "first_frame",
                },
            ],
            "resolution": resolution,
            "ratio": aspect_ratio,
            "duration": duration,
        }
    else:
        payload = {
            "images": [image_url],
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
        }
    r = requests.post(
        f"{BASE_URL}/model/v1/queue/{model}",
        headers={**api_headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("request_id"):
        raise RuntimeError(f"OdiRouter returned no request_id: {data}")
    return data


def poll(job: dict, interval: int) -> dict:
    status_url = job["status_url"]
    response_url = job["response_url"]

    while True:
        r = requests.get(status_url, headers=api_headers(), timeout=60)
        r.raise_for_status()
        data = r.json()
        status = str(data.get("status", "")).lower()
        print("STATUS:", status)

        if status == "completed":
            r = requests.get(response_url, headers=api_headers(), timeout=60)
            r.raise_for_status()
            return r.json()

        if status in {"failed", "cancelled", "canceled", "error"}:
            raise RuntimeError(f"OdiRouter task failed: {data}")

        time.sleep(interval)


def extract_video_url(result: dict) -> str:
    for item in result.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "video" and content.get("url"):
                return content["url"]
    raise RuntimeError(f"No video found in OdiRouter response: {result}")


def download(url: str, output: Path) -> None:
    r = requests.get(url, headers=api_headers(), timeout=180)
    r.raise_for_status()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(r.content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default=os.getenv("ODIROUTER_VIDEO_MODEL", DEFAULT_MODEL))
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--resolution", default="720p")
    parser.add_argument("--aspect-ratio", default="9:16")
    parser.add_argument("--poll-seconds", type=int, default=5)
    args = parser.parse_args()

    load_dotenv(Path(".env").resolve())

    if not args.image.exists():
        raise FileNotFoundError(args.image)
    prompt = args.prompt_file.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError("Prompt file is empty")

    print("MODEL:", args.model)
    print("IMAGE:", args.image)
    print("Uploading reference image...")
    image_url = upload_image(args.image)

    print("Submitting video...")
    job = submit(
        image_url=image_url,
        prompt=prompt,
        model=args.model,
        duration=args.duration,
        resolution=args.resolution,
        aspect_ratio=args.aspect_ratio,
    )
    print("REQUEST ID:", job["request_id"])

    result = poll(job, args.poll_seconds)
    video_url = extract_video_url(result)

    print("Downloading video...")
    download(video_url, args.output)
    print("VIDEO:", args.output.resolve())
    print("SIZE:", args.output.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
