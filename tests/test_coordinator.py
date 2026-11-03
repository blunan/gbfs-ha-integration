"""Tests of the coordinator and GBFS feed auto-discovery."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
import pytest

from custom_components.gbfs.const import InvalidFeed
from custom_components.gbfs.coordinator import (
    StationStatus,
    localized_text,
    parse_timestamp,
    resolve_feeds,
)
from homeassistant.core import HomeAssistant

from .conftest import FEED_BASE, load_json_fixture

NAMES = [
    {"text": "Station Alpha", "language": "en"},
    {"text": "Estación Alfa", "language": "es"},
]


def test_resolve_feeds_by_language() -> None:
    """GBFS 1.x/2.x: selects the requested language block."""
    discovery = load_json_fixture("gbfs.json")

    feeds = resolve_feeds(discovery, "es")
    assert feeds["station_status"].startswith("https://gbfs.example.com/gbfs/es/")

    feeds = resolve_feeds(discovery, "en-US")
    assert feeds["station_status"].startswith("https://gbfs.example.com/gbfs/en/")

    # Language not published: falls back to first available
    feeds = resolve_feeds(discovery, "fr")
    assert "station_status" in feeds


def test_resolve_feeds_v3() -> None:
    """GBFS 3.0: flat data.feeds, no languages."""
    feeds = resolve_feeds(load_json_fixture("gbfs_v3.json"), "es")
    assert feeds["station_status"] == (
        "https://gbfs.example.com/gbfs/3.0/station_status.json"
    )


def test_resolve_feeds_invalid() -> None:
    """Invalid structures raise InvalidFeed."""
    with pytest.raises(InvalidFeed):
        resolve_feeds({"hello": "world"})
    with pytest.raises(InvalidFeed):
        resolve_feeds({"data": {"en": {"feeds": []}}})
    # Missing station_status
    with pytest.raises(InvalidFeed):
        resolve_feeds(
            {
                "data": {
                    "feeds": [
                        {"name": "station_information", "url": "https://x/si.json"}
                    ]
                }
            }
        )


@pytest.mark.parametrize(
    ("value", "language", "expected"),
    [
        # GBFS 1.x/2.x: plain text, whatever the language
        ("Station Alpha", "es", "Station Alpha"),
        # GBFS 3.0: the translation matching the primary language subtag
        (NAMES, "es", "Estación Alfa"),
        (NAMES, "es-MX", "Estación Alfa"),
        (NAMES, "en", "Station Alpha"),
        # No matching translation, or no language: the first one
        (NAMES, "fr", "Station Alpha"),
        (NAMES, None, "Station Alpha"),
        # Nothing usable
        ([], "en", None),
        ([{"language": "en"}], "en", None),
        (None, "en", None),
        (42, "en", None),
    ],
)
def test_localized_text(value: Any, language: str | None, expected: str | None) -> None:
    """Plain GBFS strings and 3.0 translations resolve to one text."""
    assert localized_text(value, language) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # GBFS 1.x/2.x: POSIX seconds
        (1786131115, datetime(2026, 8, 7, 19, 31, 55, tzinfo=UTC)),
        # GBFS 3.0: RFC 3339, with Z or an offset, and optional fractions
        ("2026-08-04T10:11:55Z", datetime(2026, 8, 4, 10, 11, 55, tzinfo=UTC)),
        ("2026-08-04T12:11:40+02:00", datetime(2026, 8, 4, 10, 11, 40, tzinfo=UTC)),
        ("2026-11-03T19:57:09.338Z", datetime(2026, 11, 3, 19, 57, 9, 338000, UTC)),
        # Without an offset the time is ambiguous; garbage is ignored
        ("2026-08-04T10:11:55", None),
        ("yesterday", None),
        (None, None),
    ],
)
def test_parse_timestamp(value: Any, expected: datetime | None) -> None:
    """Timestamps of every GBFS version become aware datetimes."""
    assert parse_timestamp(value) == expected


def test_station_status_same_across_versions() -> None:
    """A GBFS 2.x station and its 3.0 equivalent read the same."""
    v2 = {
        "station_id": "1",
        "num_bikes_available": 9,
        "num_bikes_disabled": 2,
        "num_docks_available": 30,
        "num_docks_disabled": 1,
        "is_renting": 1,
        "is_returning": 0,
        "last_reported": 1786131115,
    }
    v3 = {
        "station_id": "1",
        "num_vehicles_available": 9,
        "num_vehicles_disabled": 2,
        "num_docks_available": 30,
        "num_docks_disabled": 1,
        "is_renting": True,
        "is_returning": False,
        "last_reported": "2026-08-07T19:31:55Z",
    }
    expected = StationStatus(
        bikes_available=9,
        bikes_disabled=2,
        docks_available=30,
        docks_disabled=1,
        is_renting=True,
        is_returning=False,
        last_reported=datetime(2026, 8, 7, 19, 31, 55, tzinfo=UTC),
    )
    assert StationStatus.from_feed(v2) == expected
    assert StationStatus.from_feed(v3) == expected


async def test_coordinator_setup(hass: HomeAssistant, mock_feeds, config_entry) -> None:
    """First refresh discovers feeds, loads names, and polls status."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = config_entry.runtime_data
    assert set(coordinator.data) == {"1", "2", "3"}
    assert coordinator.data["1"].bikes_available == 9
    assert coordinator.raw_status["1"]["num_bikes_available"] == 9
    assert coordinator.station_name("1") == "Station Alpha"
    assert "num_ebikes_available" not in coordinator.published_fields
    assert "num_bikes_disabled" in coordinator.published_fields
    # Feed ttl (10s) is less than default interval: stays at 60s
    assert coordinator.update_interval == timedelta(seconds=60)


async def test_coordinator_setup_v3(
    hass: HomeAssistant, mock_feeds_v3, config_entry_v3
) -> None:
    """GBFS 3.0: translated names and renamed fields."""
    assert await hass.config_entries.async_setup(config_entry_v3.entry_id)
    await hass.async_block_till_done()

    coordinator = config_entry_v3.runtime_data
    assert coordinator.data["1"].bikes_available == 9
    assert coordinator.station_name("1") == "Station Alpha"
    # Only published in Spanish: falls back to it
    assert coordinator.station_name("3") == "Estación Gamma"


async def test_coordinator_respects_larger_ttl(
    hass: HomeAssistant, mock_feeds, config_entry
) -> None:
    """If feed ttl is greater than 60s, the interval respects it."""
    status = load_json_fixture("station_status.json")
    status["ttl"] = 300
    mock_feeds.clear_requests()
    mock_feeds.get(
        "https://gbfs.example.com/gbfs/gbfs.json",
        json=load_json_fixture("gbfs.json"),
    )
    mock_feeds.get(
        f"{FEED_BASE}/station_information.json",
        json=load_json_fixture("station_information.json"),
    )
    mock_feeds.get(f"{FEED_BASE}/station_status.json", json=status)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = config_entry.runtime_data
    assert coordinator.update_interval == timedelta(seconds=300)


async def test_coordinator_update_failed(
    hass: HomeAssistant, mock_feeds, config_entry
) -> None:
    """A network error in the poll marks the update as failed."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = config_entry.runtime_data
    assert coordinator.last_update_success is True

    mock_feeds.clear_requests()
    mock_feeds.get(f"{FEED_BASE}/station_status.json", exc=aiohttp.ClientError("boom"))
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
