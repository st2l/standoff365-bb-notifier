"""Persistent record of program ids already seen and notified."""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class StateStore:
    """Tracks which program ids have been observed, backed by a JSON file.

    The file holds a single ``{"seen_ids": [...]}`` object. Writes are atomic
    (temp file + rename) so an interrupted run cannot corrupt the state.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._seen: set[int] = set()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def is_empty(self) -> bool:
        """True when no ids have been recorded (e.g. very first run)."""
        return not self._seen

    def load(self) -> None:
        """Load seen ids from disk, tolerating a missing file."""
        if not self._path.exists():
            logger.info("no state file at %s; starting fresh", self._path)
            self._seen = set()
            return
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        self._seen = {int(i) for i in raw.get("seen_ids", [])}
        logger.info("loaded %d seen ids from %s", len(self._seen), self._path)

    def diff(self, ids: set[int]) -> set[int]:
        """Return ids in ``ids`` that have not been seen before."""
        return ids - self._seen

    def mark_seen(self, ids: set[int]) -> None:
        """Add ids to the seen set (call before :meth:`save`)."""
        self._seen |= ids

    def save(self) -> None:
        """Atomically persist the current seen set to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"seen_ids": sorted(self._seen)}
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self._path.parent,
            prefix=f".{self._path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            tmp_path = Path(handle.name)
        tmp_path.replace(self._path)
        logger.debug("saved %d seen ids to %s", len(self._seen), self._path)
