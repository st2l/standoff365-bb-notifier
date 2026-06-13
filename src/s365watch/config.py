"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

API_BASE_URL = "https://api.standoff365.com/api"
SITE_ORIGIN = "https://bugbounty.standoff365.com"
DEFAULT_POLL_INTERVAL = 600
DEFAULT_STATE_PATH = "state/seen.json"


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class Config:
    """All settings needed to run the watcher.

    Attributes:
        bot_token: Telegram bot token from @BotFather.
        chat_id: Target chat/channel id (e.g. ``-1001234567890`` or ``@channel``).
        poll_interval: Seconds between polls in loop mode.
        state_path: Path to the JSON file tracking already-seen program ids.
        request_timeout: Per-request timeout in seconds.
        notify_existing_on_first_run: If false, the first run only records the
            current programs as a baseline without sending notifications.
    """

    bot_token: str
    chat_id: str
    poll_interval: int = DEFAULT_POLL_INTERVAL
    state_path: str = DEFAULT_STATE_PATH
    request_timeout: float = 30.0
    notify_existing_on_first_run: bool = False

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Config:
        """Build configuration from the process environment.

        Args:
            env: Mapping to read from; defaults to ``os.environ``.

        Returns:
            A validated Config.

        Raises:
            ConfigError: If a required variable is missing or a numeric
                variable cannot be parsed.
        """
        source = os.environ if env is None else env
        bot_token = source.get("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = source.get("TELEGRAM_CHAT_ID", "").strip()
        if not bot_token:
            raise ConfigError("TELEGRAM_BOT_TOKEN is required")
        if not chat_id:
            raise ConfigError("TELEGRAM_CHAT_ID is required")
        return cls(
            bot_token=bot_token,
            chat_id=chat_id,
            poll_interval=_int_env(source, "POLL_INTERVAL", DEFAULT_POLL_INTERVAL),
            state_path=source.get("STATE_PATH", DEFAULT_STATE_PATH).strip() or DEFAULT_STATE_PATH,
            request_timeout=_float_env(source, "REQUEST_TIMEOUT", 30.0),
            notify_existing_on_first_run=_bool_env(
                source, "NOTIFY_EXISTING_ON_FIRST_RUN", default=False
            ),
        )


def _int_env(env: Mapping[str, str], key: str, default: int) -> int:
    raw = env.get(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{key} must be an integer, got {raw!r}") from exc


def _float_env(env: Mapping[str, str], key: str, default: float) -> float:
    raw = env.get(key, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{key} must be a number, got {raw!r}") from exc


def _bool_env(env: Mapping[str, str], key: str, *, default: bool) -> bool:
    raw = env.get(key, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}
