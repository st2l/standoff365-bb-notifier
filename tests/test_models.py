"""Tests for program parsing."""

from __future__ import annotations

from s365watch.models import Program
from tests.conftest import make_program_payload


def test_from_api_parses_core_fields() -> None:
    program = Program.from_api(make_program_payload())
    assert program.id == 391
    assert program.slug == "bcs-bank"
    assert program.name == "БКС Банк"
    assert program.is_published
    assert program.url == "https://bugbounty.standoff365.com/programs/bcs-bank"


def test_from_api_parses_reward_range() -> None:
    program = Program.from_api(make_program_payload())
    assert len(program.rewards) == 1
    reward = program.rewards[0]
    assert reward.currency == "rub"
    assert reward.min_amount == 0
    assert reward.max_amount == 250000


def test_from_api_handles_missing_optional_fields() -> None:
    program = Program.from_api({"id": 7, "slug": "acme", "status": "published"})
    assert program.name == "acme"
    assert program.short_description == ""
    assert program.published_at is None
    assert program.rewards == ()


def test_from_api_handles_missing_statistics_block() -> None:
    program = Program.from_api(make_program_payload(statistics=None))
    assert program.rewards == ()


def test_non_published_status_is_not_published() -> None:
    program = Program.from_api(make_program_payload(status="archived"))
    assert not program.is_published
