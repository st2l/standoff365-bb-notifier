"""Format programs into Telegram-ready HTML messages."""

from __future__ import annotations

from html import escape

from s365watch.models import Program, RewardRange

_MAX_DESCRIPTION = 300
_CURRENCY_SYMBOLS = {"rub": "₽", "usd": "$", "eur": "€"}


def format_program_message(program: Program) -> str:
    """Render a new-program notification as Telegram HTML.

    Args:
        program: The newly published program.

    Returns:
        An HTML string suitable for ``parse_mode=HTML``.
    """
    lines = [
        "🆕 <b>Новая программа на Standoff 365 Bug Bounty</b>",
        "",
        f"<b>{escape(program.name)}</b>",
    ]
    if program.short_description:
        lines.append(escape(_truncate(program.short_description)))
    reward = _format_rewards(program.rewards)
    if reward:
        lines.append("")
        lines.append(f"💰 Награды: {reward}")
    if program.visibility == "with_confirmation":
        lines.append("🔒 Доступ по подтверждению")
    lines.append("")
    lines.append(f'🔗 <a href="{escape(program.url)}">{escape(program.url)}</a>')
    return "\n".join(lines)


def _truncate(text: str, limit: int = _MAX_DESCRIPTION) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "…"


def _format_rewards(rewards: tuple[RewardRange, ...]) -> str:
    parts: list[str] = []
    for reward in rewards:
        if reward.max_amount <= 0:
            continue
        symbol = _CURRENCY_SYMBOLS.get(reward.currency.lower(), reward.currency.upper())
        low = _format_amount(reward.min_amount)
        high = _format_amount(reward.max_amount)
        span = high if reward.min_amount <= 0 else f"{low}–{high}"
        parts.append(f"{span} {symbol}")
    return ", ".join(parts)


def _format_amount(amount: float) -> str:
    return f"{round(amount):,}".replace(",", " ")
