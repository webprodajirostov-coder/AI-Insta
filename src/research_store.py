from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.domain_validation import (
    DomainValidationError,
    validate_research_insight,
)


def load_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Research file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise DomainValidationError(
            f"Research file must contain a JSON object: {path}"
        )

    return data


def load_research_record(
    path: str | Path,
    *,
    account_id: str | None = None,
) -> dict[str, Any]:
    record = load_json(path)

    research_id = record.get("research_id")
    if not research_id:
        raise DomainValidationError(
            "ResearchRecord is missing required field: research_id"
        )

    actual_account_id = record.get("account_id")
    if not actual_account_id:
        raise DomainValidationError(
            f"ResearchRecord {research_id} is missing required field: account_id"
        )

    if account_id is not None and actual_account_id != account_id:
        raise DomainValidationError(
            f"ResearchRecord {research_id} belongs to account "
            f"{actual_account_id!r}, expected {account_id!r}"
        )

    for field in ("status", "source", "raw_material", "analysis"):
        if field not in record:
            raise DomainValidationError(
                f"ResearchRecord {research_id} is missing required field: {field}"
            )

    if not isinstance(record["source"], Mapping):
        raise DomainValidationError(
            f"ResearchRecord {research_id} source must be an object"
        )

    if not isinstance(record["analysis"], Mapping):
        raise DomainValidationError(
            f"ResearchRecord {research_id} analysis must be an object"
        )

    return record


def load_research_insight(
    path: str | Path,
    *,
    account_id: str | None = None,
) -> dict[str, Any]:
    insight = load_json(path)
    validate_research_insight(insight, account_id=account_id)
    return insight


def load_research_directory(
    directory: str | Path,
    *,
    account_id: str | None = None,
) -> dict[str, dict[str, Any]]:
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"Research directory not found: {directory}")

    records: dict[str, dict[str, Any]] = {}

    for path in sorted(directory.glob("*.json")):
        data = load_json(path)

        if data.get("entity") == "ResearchRecord":
            record = load_research_record(path, account_id=account_id)
            records[record["research_id"]] = record
        elif data.get("entity") == "ResearchInsight":
            insight = load_research_insight(path, account_id=account_id)
            records[insight["insight_id"]] = insight

    return records
