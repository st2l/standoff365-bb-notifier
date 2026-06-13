"""Shared test fixtures."""

from __future__ import annotations

from typing import Any

import pytest

from s365watch.models import Program


def make_program_payload(**overrides: Any) -> dict[str, Any]:
    """Build a realistic ``items[]`` API entry, overridable per test."""
    payload: dict[str, Any] = {
        "id": 391,
        "slug": "bcs-bank",
        "name": "БКС Банк",
        "status": "published",
        "visibility": "public",
        "shortDescription": "БКС Банк работает на рынке с 1989 года.",
        "publishedAt": "2025-07-11T07:20:31.914250Z",
        "statistics": {"rewards": {"rub": {"min": 0, "max": 250000, "totalBounties": 1320000.0}}},
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def program() -> Program:
    return Program.from_api(make_program_payload())
