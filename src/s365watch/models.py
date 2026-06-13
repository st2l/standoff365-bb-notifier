"""Domain models for Standoff 365 bug bounty programs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PROGRAM_URL_TEMPLATE = "https://bugbounty.standoff365.com/programs/{slug}"


@dataclass(frozen=True, slots=True)
class RewardRange:
    """Min/max bounty for a single currency."""

    currency: str
    min_amount: float
    max_amount: float


@dataclass(frozen=True, slots=True)
class Program:
    """A bug bounty program as returned by the Standoff 365 UI API.

    Only the fields used for change detection and notification are kept; the
    raw API payload carries many more that are irrelevant here.
    """

    id: int
    slug: str
    name: str
    status: str
    visibility: str
    short_description: str
    published_at: str | None
    rewards: tuple[RewardRange, ...]

    @property
    def url(self) -> str:
        """Public program page on bugbounty.standoff365.com."""
        return PROGRAM_URL_TEMPLATE.format(slug=self.slug)

    @property
    def is_published(self) -> bool:
        """Whether the program is publicly visible on the platform."""
        return self.status == "published"

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> Program:
        """Build a Program from a single ``items[]`` entry of the UI API.

        Args:
            payload: One program object from ``/bug-bounty/ui/program``.

        Returns:
            Parsed Program. Missing optional fields fall back to safe defaults.

        Raises:
            KeyError: If a required identifier field is absent.
        """
        return cls(
            id=int(payload["id"]),
            slug=str(payload["slug"]),
            name=str(payload.get("name") or payload["slug"]),
            status=str(payload.get("status") or "unknown"),
            visibility=str(payload.get("visibility") or "unknown"),
            short_description=str(payload.get("shortDescription") or "").strip(),
            published_at=_optional_str(payload.get("publishedAt")),
            rewards=_parse_rewards(payload.get("statistics")),
        )


def _optional_str(value: Any) -> str | None:
    return str(value) if value else None


def _parse_rewards(statistics: Any) -> tuple[RewardRange, ...]:
    """Extract per-currency reward ranges from the ``statistics`` block."""
    if not isinstance(statistics, dict):
        return ()
    rewards = statistics.get("rewards")
    if not isinstance(rewards, dict):
        return ()
    ranges: list[RewardRange] = []
    for currency, data in rewards.items():
        if not isinstance(data, dict):
            continue
        ranges.append(
            RewardRange(
                currency=str(currency),
                min_amount=float(data.get("min") or 0),
                max_amount=float(data.get("max") or 0),
            )
        )
    return tuple(ranges)
