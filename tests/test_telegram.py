"""Tests for the Telegram notifier."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from s365watch.telegram import TelegramError, TelegramNotifier


def test_send_message_posts_to_chat(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json={"ok": True, "result": {"message_id": 1}})
    with TelegramNotifier.create("token123", "-1001") as notifier:
        notifier.send_message("<b>hi</b>")
    request = httpx_mock.get_request()
    assert request is not None
    assert request.url.path == "/bottoken123/sendMessage"
    body = request.read().decode()
    assert '"chat_id":"-1001"' in body
    assert '"parse_mode":"HTML"' in body


def test_send_raises_on_api_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=400, json={"ok": False, "description": "chat not found"})
    with (
        TelegramNotifier.create("token", "-1") as notifier,
        pytest.raises(TelegramError, match="chat not found"),
    ):
        notifier.send_message("hi")


def test_send_raises_when_ok_false_on_200(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, json={"ok": False, "description": "nope"})
    with (
        TelegramNotifier.create("token", "-1") as notifier,
        pytest.raises(TelegramError, match="nope"),
    ):
        notifier.send_message("hi")
