from __future__ import annotations

import json
import os
from typing import Any, Callable, Mapping

import requests
from dotenv import load_dotenv

from src.llm_provider import LLMProvider


ODIROUTER_URL = "https://api.odirouter.ai/v1/chat/completions"


class ODIRouterLLMProvider:
    """Concrete LLMProvider for ODIRouter's OpenAI-compatible chat API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        base_url: str = ODIROUTER_URL,
        timeout: int = 90,
        post: Callable[..., Any] | None = None,
    ):
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("ODIROUTER_API_KEY")

        if not api_key:
            raise ValueError("ODIROUTER_API_KEY is required")

        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self._post = post or requests.post

    @staticmethod
    def _parse_json_content(raw_content: str) -> Any:
        content = raw_content.strip()

        if content.startswith("```"):
            lines = content.splitlines()

            if len(lines) == 1 and "\\n" in content:
                lines = content.split("\\n")

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines).strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("ODIRouter returned invalid JSON") from exc
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Mapping[str, Any] | None = None,
    ) -> Any:
        effective_user_prompt = user_prompt

        if response_schema is not None:
            effective_user_prompt += (
                "\n\nRESPONSE SCHEMA:\n"
                + json.dumps(response_schema, ensure_ascii=False, indent=2)
                + "\nReturn valid JSON matching this schema."
            )

        response = self._post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": effective_user_prompt},
                ],
                "temperature": 0.7,
            },
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"ODIRouter returned HTTP {response.status_code}: "
                f"{getattr(response, 'text', '')}"
            )

        try:
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError("Invalid ODIRouter chat completion response") from exc

        if not isinstance(raw_content, str):
            raise RuntimeError("ODIRouter message content must be a string")

        return self._parse_json_content(raw_content)

