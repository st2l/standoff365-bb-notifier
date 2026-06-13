"""Core watch logic: detect newly published programs and notify."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterable

from s365watch.client import Standoff365Client
from s365watch.models import Program
from s365watch.notifier import format_program_message
from s365watch.state import StateStore
from s365watch.telegram import TelegramError, TelegramNotifier

logger = logging.getLogger(__name__)


class Monitor:
    """Polls Standoff 365, diffs against state, and notifies on new programs."""

    def __init__(
        self,
        client: Standoff365Client,
        notifier: TelegramNotifier,
        store: StateStore,
        *,
        notify_first_run: bool = False,
    ) -> None:
        self._client = client
        self._notifier = notifier
        self._store = store
        self._notify_first_run = notify_first_run

    def run_once(self) -> list[Program]:
        """Run a single poll cycle.

        Returns:
            Programs that were newly detected and notified this cycle. On the
            baseline (first) run the list is empty even though state is
            populated, unless ``notify_first_run`` is set.

        Raises:
            httpx.HTTPError: If the platform fetch fails.
        """
        programs = self._client.fetch_published_programs()
        by_id = {p.id: p for p in programs}
        new_ids = self._store.diff(set(by_id))

        if not new_ids:
            logger.info("no new programs (%d published total)", len(by_id))
            self._store.mark_seen(set(by_id))
            self._store.save()
            return []

        if self._store.is_empty and not self._notify_first_run:
            logger.info("baseline run: recording %d programs without notifying", len(new_ids))
            self._store.mark_seen(set(by_id))
            self._store.save()
            return []

        notified = self._notify(by_id[i] for i in new_ids)
        self._store.mark_seen({p.id for p in notified})
        self._store.save()
        return notified

    def _notify(self, programs: Iterable[Program]) -> list[Program]:
        ordered = sorted(programs, key=lambda p: (p.published_at or "", p.id))
        notified: list[Program] = []
        for program in ordered:
            try:
                self._notifier.send_message(format_program_message(program))
            except TelegramError:
                logger.exception("failed to notify program %s; will retry", program.slug)
                break
            notified.append(program)
        logger.info("notified %d new programs", len(notified))
        return notified


def run_loop(
    monitor: Monitor, interval: int, sleep: Callable[[float], object] = time.sleep
) -> None:
    """Run :meth:`Monitor.run_once` forever, sleeping ``interval`` seconds.

    Transient fetch errors are logged and retried on the next cycle rather than
    crashing the daemon.

    Args:
        monitor: Configured Monitor.
        interval: Seconds to sleep between cycles.
        sleep: Sleep function (injectable for tests).
    """
    logger.info("starting watch loop, interval=%ds", interval)
    while True:
        try:
            monitor.run_once()
        except Exception:
            logger.exception("poll cycle failed; retrying after interval")
        sleep(interval)
