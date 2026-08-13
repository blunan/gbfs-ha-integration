"""Tests for sensor and binary_sensor entities."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .conftest import FEED_BASE, load_json_fixture


async def _setup(hass: HomeAssistant, config_entry) -> None:
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_sensor_values(hass: HomeAssistant, mock_feeds, config_entry) -> None:
    """Sensors expose values from station_status.json."""
    await _setup(hass, config_entry)

    assert hass.states.get("sensor.station_alpha_bikes_available").state == "9"
    assert hass.states.get("sensor.station_alpha_docks_available").state == "30"
    assert hass.states.get("sensor.station_alpha_bikes_disabled").state == "2"
    assert hass.states.get("sensor.station_alpha_docks_disabled").state == "1"
    # 9 / (9 + 30) * 100 = 23.1
    assert hass.states.get("sensor.station_alpha_occupancy").state == "23.1"
    assert (
        hass.states.get("sensor.station_alpha_last_reported").state
        == dt_util.utc_from_timestamp(1786131115).isoformat()
    )

    # Station out of service: 0 bikes and 0 docks → occupancy unknown
    assert hass.states.get("sensor.station_beta_bikes_available").state == "0"
    assert hass.states.get("sensor.station_beta_occupancy").state == "unknown"

    # Station 3 was not selected: its entities are not created
    assert hass.states.get("sensor.station_gamma_bikes_available") is None


async def test_bikes_sensor_exposes_location(
    hass: HomeAssistant, mock_feeds, config_entry
) -> None:
    """The bikes sensor carries lat/lon from station_information for the map card."""
    await _setup(hass, config_entry)

    bikes = hass.states.get("sensor.station_alpha_bikes_available")
    assert bikes.attributes["latitude"] == 19.416795
    assert bikes.attributes["longitude"] == -99.192508

    # Only one entity per station carries coordinates (one marker per station)
    docks = hass.states.get("sensor.station_alpha_docks_available")
    assert "latitude" not in docks.attributes


async def test_ebikes_sensor_not_created_without_feed_support(
    hass: HomeAssistant, mock_feeds, config_entry
) -> None:
    """Ecobici-style feed does not publish e-bikes: entity does not exist."""
    await _setup(hass, config_entry)
    assert hass.states.get("sensor.station_alpha_e_bikes_available") is None


async def test_ebikes_sensor_created_when_feed_publishes_it(
    hass: HomeAssistant, mock_feeds, config_entry
) -> None:
    """With num_ebikes_available in the feed, the entity is created."""
    mock_feeds.clear_requests()
    mock_feeds.get(
        "https://gbfs.example.com/gbfs/gbfs.json",
        json=load_json_fixture("gbfs.json"),
    )
    mock_feeds.get(
        f"{FEED_BASE}/station_information.json",
        json=load_json_fixture("station_information.json"),
    )
    mock_feeds.get(
        f"{FEED_BASE}/station_status.json",
        json=load_json_fixture("station_status_ebikes.json"),
    )

    await _setup(hass, config_entry)
    assert hass.states.get("sensor.station_alpha_e_bikes_available").state == "4"

    # This fixture does not publish num_bikes_disabled/num_docks_disabled:
    # conditional sensors are not created
    assert hass.states.get("sensor.station_alpha_bikes_disabled") is None
    assert hass.states.get("sensor.station_alpha_docks_disabled") is None


async def test_binary_sensors(hass: HomeAssistant, mock_feeds, config_entry) -> None:
    """is_renting and is_returning are exposed as binary sensors."""
    await _setup(hass, config_entry)

    assert hass.states.get("binary_sensor.station_alpha_renting").state == "on"
    assert hass.states.get("binary_sensor.station_alpha_returning").state == "on"
    assert hass.states.get("binary_sensor.station_beta_renting").state == "off"
    assert hass.states.get("binary_sensor.station_beta_returning").state == "on"
