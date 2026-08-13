"""Shared fixtures for GBFS tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbfs.const import CONF_STATIONS, CONF_URL, DOMAIN

FIXTURES_DIR = Path(__file__).parent / "fixtures"

GBFS_URL = "https://gbfs.example.com/gbfs/gbfs.json"
FEED_BASE = "https://gbfs.example.com/gbfs/en"


def load_json_fixture(name: str) -> dict[str, Any]:
    """Loads a JSON fixture from tests/fixtures."""
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allows loading custom_components in tests."""
    return


@pytest.fixture
def mock_feeds(aioclient_mock):
    """Mocks the four GBFS feeds with fixture data."""
    aioclient_mock.get(GBFS_URL, json=load_json_fixture("gbfs.json"))
    aioclient_mock.get(
        f"{FEED_BASE}/system_information.json",
        json=load_json_fixture("system_information.json"),
    )
    aioclient_mock.get(
        f"{FEED_BASE}/station_information.json",
        json=load_json_fixture("station_information.json"),
    )
    aioclient_mock.get(
        f"{FEED_BASE}/station_status.json",
        json=load_json_fixture("station_status.json"),
    )
    return aioclient_mock


@pytest.fixture
def config_entry(hass) -> MockConfigEntry:
    """Config entry with stations 1 and 2 selected."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Example Bikes",
        data={CONF_URL: GBFS_URL},
        options={CONF_STATIONS: ["1", "2"]},
        unique_id=GBFS_URL.rstrip("/"),
    )
    entry.add_to_hass(hass)
    return entry
