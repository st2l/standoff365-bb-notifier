"""Tests for the watch loop and diff logic."""

from __future__ import annotations

from pathlib import Path

from s365watch.models import Program
from s365watch.monitor import Monitor
from s365watch.state import StateStore
from s365watch.telegram import TelegramError
from tests.conftest import make_program_payload


class FakeClient:
    def __init__(self, programs: list[Program]) -> None:
        self._programs = programs

    def set_programs(self, programs: list[Program]) -> None:
        self._programs = programs

    def fetch_published_programs(self) -> list[Program]:
        return list(self._programs)


class FakeNotifier:
    def __init__(self, *, fail_on: set[str] | None = None) -> None:
        self.sent: list[str] = []
        self._fail_on = fail_on or set()

    def send_message(self, text: str) -> None:
        for slug in self._fail_on:
            if slug in text:
                raise TelegramError(f"boom on {slug}")
        self.sent.append(text)


def _program(id_: int, slug: str) -> Program:
    return Program.from_api(make_program_payload(id=id_, slug=slug, name=slug))


def _monitor(
    client: FakeClient,
    notifier: FakeNotifier,
    store: StateStore,
    *,
    notify_first_run: bool = False,
) -> Monitor:
    return Monitor(client, notifier, store, notify_first_run=notify_first_run)  # type: ignore[arg-type]


def test_baseline_run_records_without_notifying(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "seen.json")
    store.load()
    client = FakeClient([_program(1, "a"), _program(2, "b")])
    notifier = FakeNotifier()
    monitor = _monitor(client, notifier, store)

    notified = monitor.run_once()

    assert notified == []
    assert notifier.sent == []
    assert store.diff({1, 2}) == set()


def test_baseline_run_notifies_when_opted_in(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "seen.json")
    store.load()
    client = FakeClient([_program(1, "a")])
    notifier = FakeNotifier()
    monitor = _monitor(client, notifier, store, notify_first_run=True)

    notified = monitor.run_once()

    assert len(notified) == 1
    assert len(notifier.sent) == 1


def test_new_program_triggers_notification(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "seen.json")
    store.load()
    client = FakeClient([_program(1, "a")])
    notifier = FakeNotifier()
    monitor = _monitor(client, notifier, store)
    monitor.run_once()  # baseline

    client.set_programs([_program(1, "a"), _program(2, "newco")])
    notified = monitor.run_once()

    assert [p.slug for p in notified] == ["newco"]
    assert len(notifier.sent) == 1
    assert "newco" in notifier.sent[0]


def test_no_new_programs_sends_nothing(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "seen.json")
    store.load()
    client = FakeClient([_program(1, "a")])
    notifier = FakeNotifier()
    monitor = _monitor(client, notifier, store)
    monitor.run_once()

    notified = monitor.run_once()

    assert notified == []
    assert notifier.sent == []


def test_failed_send_is_not_marked_seen(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "seen.json")
    store.load()
    client = FakeClient([_program(1, "a")])
    notifier = FakeNotifier(fail_on={"newco"})
    monitor = _monitor(client, notifier, store)
    monitor.run_once()  # baseline

    client.set_programs([_program(1, "a"), _program(2, "newco")])
    first = monitor.run_once()
    assert first == []
    assert store.diff({2}) == {2}

    notifier_ok = FakeNotifier()
    retry = Monitor(client, notifier_ok, store)  # type: ignore[arg-type]
    notified = retry.run_once()
    assert [p.slug for p in notified] == ["newco"]


def test_state_persists_across_monitor_instances(tmp_path: Path) -> None:
    path = tmp_path / "seen.json"
    store = StateStore(path)
    store.load()
    client = FakeClient([_program(1, "a")])
    _monitor(client, FakeNotifier(), store).run_once()

    reloaded = StateStore(path)
    reloaded.load()
    notifier = FakeNotifier()
    client.set_programs([_program(1, "a"), _program(9, "fresh")])
    notified = Monitor(client, notifier, reloaded).run_once()  # type: ignore[arg-type]
    assert [p.slug for p in notified] == ["fresh"]
