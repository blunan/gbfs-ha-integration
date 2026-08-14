"""Tests for config entry diagnostics."""

from __future__ import annotations

from custom_components.gbfs.const import CONF_STATIONS, CONF_URL
from custom_components.gbfs.diagnostics import async_get_config_entry_diagnostics
from homeassistant.core import HomeAssistant

from .conftest import GBFS_URL


async def test_diagnostics(hass: HomeAssistant, mock_feeds, config_entry) -> None:
    """Diagnostics expose the entry config and the coordinator state."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)

    assert diagnostics["entry"] == {
        "data": {CONF_URL: GBFS_URL},
        "options": {CONF_STATIONS: ["1", "2"]},
    }
    assert diagnostics["update_interval_seconds"] == 60
    assert diagnostics["last_update_success"] is True
    assert "num_bikes_disabled" in diagnostics["published_fields"]
    assert diagnostics["station_info"]["1"]["name"] == "Station Alpha"
    assert diagnostics["station_status"]["1"]["num_bikes_available"] == 9
