"""Tests for the Standoff 365 API client."""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from s365watch.client import Standoff365Client
from tests.conftest import make_program_payload


def _response_body(*items: dict) -> dict:
    return {"items": list(items), "page": 1, "total": 1, "totalEntries": len(items)}


def test_fetch_programs_parses_items(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        json=_response_body(
            make_program_payload(id=1, slug="a"),
            make_program_payload(id=2, slug="b"),
        )
    )
    with Standoff365Client.create() as client:
        programs = client.fetch_programs()
    assert [p.id for p in programs] == [1, 2]


def test_fetch_published_filters_non_published(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        json=_response_body(
            make_program_payload(id=1, slug="a", status="published"),
            make_program_payload(id=2, slug="b", status="archived"),
            make_program_payload(id=3, slug="c", status="finished"),
        )
    )
    with Standoff365Client.create() as client:
        programs = client.fetch_published_programs()
    assert [p.id for p in programs] == [1]


def test_sends_browser_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=_response_body())
    with Standoff365Client.create() as client:
        client.fetch_programs()
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["Origin"] == "https://bugbounty.standoff365.com"
    assert request.headers["Referer"] == "https://bugbounty.standoff365.com/"


def test_raises_on_server_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=503)
    with Standoff365Client.create() as client, pytest.raises(httpx.HTTPStatusError):
        client.fetch_programs()


def test_raises_on_malformed_payload(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json={"unexpected": True})
    with Standoff365Client.create() as client, pytest.raises(ValueError):
        client.fetch_programs()
