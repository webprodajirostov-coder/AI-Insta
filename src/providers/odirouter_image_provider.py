import os
from pathlib import Path

import requests
from dotenv import load_dotenv


class ODIRouterImageProvider:
    BASE_URL = "https://api.odirouter.ai/model"
    MODEL = "kling-v3-image"

    def __init__(self, api_key=None):
        load_dotenv(Path(".env").resolve())

        self.api_key = api_key or os.getenv("ODIROUTER_API_KEY")

        if not self.api_key:
            raise RuntimeError("ODIROUTER_API_KEY is not configured")

    def submit(
        self,
        prompt,
        resolution="1k",
        aspect_ratio="9:16",
        negative_prompt="",
        n=1,
    ):
        url = f"{self.BASE_URL}/v1/queue/{self.MODEL}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "resolution": resolution,
            "n": n,
            "aspect_ratio": aspect_ratio,
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=90,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("request_id"):
            raise RuntimeError(
                f"OdiRouter returned no request_id: {data}"
            )

        return data

    def get_status(self, status_url):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        response = requests.get(
            status_url,
            headers=headers,
            timeout=60,
        )

        response.raise_for_status()

        return response.json()

    def download_file(self, file_url, output_path):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        response = requests.get(
            file_url,
            headers=headers,
            timeout=120,
        )

        response.raise_for_status()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)

        return output_path

    def get_result(self, response_url):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        response = requests.get(
            response_url,
            headers=headers,
            timeout=60,
        )

        response.raise_for_status()

        return response.json()
