"""Tests for environment configuration parsing."""

from __future__ import annotations

import pytest

from s365watch.config import Config, ConfigError


def _base_env(**overrides: str) -> dict[str, str]:
    env = {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "123"}
    env.update(overrides)
    return env


def test_requires_bot_token() -> None:
    with pytest.raises(ConfigError, match="TELEGRAM_BOT_TOKEN"):
        Config.from_env({"TELEGRAM_CHAT_ID": "123"})


def test_requires_chat_id() -> None:
    with pytest.raises(ConfigError, match="TELEGRAM_CHAT_ID"):
        Config.from_env({"TELEGRAM_BOT_TOKEN": "tok"})


def test_defaults_applied() -> None:
    config = Config.from_env(_base_env())
    assert config.poll_interval == 600
    assert config.telegram_proxy is None
    assert config.notify_existing_on_first_run is False


def test_telegram_proxy_parsed() -> None:
    config = Config.from_env(_base_env(TELEGRAM_PROXY="socks5://127.0.0.1:10808"))
    assert config.telegram_proxy == "socks5://127.0.0.1:10808"


def test_blank_telegram_proxy_is_none() -> None:
    config = Config.from_env(_base_env(TELEGRAM_PROXY="  "))
    assert config.telegram_proxy is None


def test_invalid_poll_interval_rejected() -> None:
    with pytest.raises(ConfigError, match="POLL_INTERVAL"):
        Config.from_env(_base_env(POLL_INTERVAL="soon"))


def test_bool_env_truthy_values() -> None:
    config = Config.from_env(_base_env(NOTIFY_EXISTING_ON_FIRST_RUN="yes"))
    assert config.notify_existing_on_first_run is True
