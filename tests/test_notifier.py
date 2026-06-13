"""Tests for message formatting."""

from __future__ import annotations

from s365watch.models import Program
from s365watch.notifier import format_program_message
from tests.conftest import make_program_payload


def test_message_contains_name_and_url() -> None:
    program = Program.from_api(make_program_payload())
    message = format_program_message(program)
    assert "БКС Банк" in message
    assert "https://bugbounty.standoff365.com/programs/bcs-bank" in message
    assert "Новая программа" in message


def test_message_formats_reward_range_without_zero_min() -> None:
    program = Program.from_api(make_program_payload())
    message = format_program_message(program)
    assert "250 000 ₽" in message
    assert "0–250 000" not in message


def test_message_formats_full_reward_range() -> None:
    payload = make_program_payload(statistics={"rewards": {"rub": {"min": 5000, "max": 250000}}})
    message = format_program_message(Program.from_api(payload))
    assert "5 000–250 000 ₽" in message


def test_message_escapes_html_in_name() -> None:
    payload = make_program_payload(name="<b>evil</b> & co")
    message = format_program_message(Program.from_api(payload))
    assert "&lt;b&gt;evil&lt;/b&gt; &amp; co" in message


def test_message_marks_confirmation_required() -> None:
    payload = make_program_payload(visibility="with_confirmation")
    message = format_program_message(Program.from_api(payload))
    assert "подтверждению" in message


def test_long_description_is_truncated() -> None:
    payload = make_program_payload(shortDescription="word " * 200)
    message = format_program_message(Program.from_api(payload))
    assert "…" in message


def test_message_omits_rewards_when_absent() -> None:
    payload = make_program_payload(statistics=None)
    message = format_program_message(Program.from_api(payload))
    assert "Награды" not in message
