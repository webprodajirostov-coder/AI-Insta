from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Infrastructure contract for structured text generation."""

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Mapping[str, Any] | None = None,
    ) -> Any:
        ...
