"""Minimal Telegram Bot API client for sending notifications."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_API_TEMPLATE = "https://api.telegram.org/bot{token}"


class TelegramError(RuntimeError):
    """Raised when the Telegram API rejects a request."""


class TelegramNotifier:
    """Sends HTML messages to a single chat via the Telegram Bot API."""

    def __init__(self, token: str, chat_id: str, client: httpx.Client) -> None:
        self._chat_id = chat_id
        self._base_url = _API_TEMPLATE.format(token=token)
        self._client = client

    @classmethod
    def create(cls, token: str, chat_id: str, timeout: float = 30.0) -> TelegramNotifier:
        """Construct a notifier with its own httpx session."""
        return cls(token, chat_id, httpx.Client(timeout=timeout))

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> TelegramNotifier:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def send_message(self, text: str) -> None:
        """Send one HTML message.

        Args:
            text: Message body with ``parse_mode=HTML`` markup.

        Raises:
            TelegramError: If the API responds with ``ok: false`` or a non-2xx
                status.
        """
        response = self._client.post(
            f"{self._base_url}/sendMessage",
            json={
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
        )
        self._raise_for_telegram(response)
        logger.info("sent message to chat %s", self._chat_id)

    @staticmethod
    def _raise_for_telegram(response: httpx.Response) -> None:
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.is_success and body.get("ok"):
            return
        description = body.get("description", response.text)
        raise TelegramError(f"Telegram API error (HTTP {response.status_code}): {description}")
