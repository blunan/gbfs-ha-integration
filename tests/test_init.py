"""Tests for removing GBFS station devices."""

from __future__ import annotations

from custom_components.gbfs.const import CONF_STATIONS, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component


async def test_remove_device(
    hass: HomeAssistant,
    hass_ws_client,
    mock_feeds,
    config_entry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """A station's device can be deleted once the station is unselected."""
    assert await async_setup_component(hass, "config", {})
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, f"{config_entry.entry_id}_1"), config_entry.entry_id
    )
    assert device is not None
    client = await hass_ws_client(hass)

    # Station 1 is selected: its device would be recreated on reload
    response = await client.remove_device(device.id)
    assert not response["success"]
    assert device_registry.async_get(device.id) is not None

    # Once unselected, its entities become unavailable...
    hass.config_entries.async_update_entry(config_entry, options={CONF_STATIONS: ["2"]})
    await hass.async_block_till_done()
    entity_id = "sensor.station_alpha_bikes_available"
    assert hass.states.get(entity_id).state == "unavailable"

    # ...until the device is deleted, removing its entities
    response = await client.remove_device(device.id)
    assert response["success"]
    await hass.async_block_till_done()
    assert device_registry.async_get(device.id) is None
    assert entity_registry.async_get(entity_id) is None
    assert hass.states.get(entity_id) is None

    # Station 2 remains selected and active
    assert hass.states.get("sensor.station_beta_bikes_available").state == "0"
