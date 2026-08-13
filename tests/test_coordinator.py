"""Tests of the coordinator and GBFS feed auto-discovery."""

from __future__ import annotations

from datetime import timedelta

import aiohttp
import pytest

from custom_components.gbfs.const import InvalidFeed
from custom_components.gbfs.coordinator import resolve_feeds
from homeassistant.core import HomeAssistant

from .conftest import FEED_BASE, load_json_fixture


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


async def test_coordinator_setup(hass: HomeAssistant, mock_feeds, config_entry) -> None:
    """First refresh discovers feeds, loads names, and polls status."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = config_entry.runtime_data
    assert set(coordinator.data) == {"1", "2", "3"}
    assert coordinator.data["1"]["num_bikes_available"] == 9
    assert coordinator.station_info["1"]["name"] == "Station Alpha"
    assert "num_ebikes_available" not in coordinator.published_fields
    assert "num_bikes_disabled" in coordinator.published_fields
    # Feed ttl (10s) is less than default interval: stays at 60s
    assert coordinator.update_interval == timedelta(seconds=60)


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
