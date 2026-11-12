"""GBFS integration: monitors bike-share stations."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_STATIONS, DOMAIN
from .coordinator import GbfsConfigEntry, GbfsCoordinator
from .entity import station_identifier

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: GbfsConfigEntry) -> bool:
    """Set up a GBFS feed from a config entry."""
    coordinator = GbfsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: GbfsConfigEntry) -> None:
    """Reload the entry when selected stations change (options flow)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GbfsConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: GbfsConfigEntry, device_entry: dr.AnyDeviceEntry
) -> bool:
    """Allow deleting the device of a station that is no longer selected.

    Selected station devices cannot be removed because reload would recreate
    them. Unselect the station in options first.
    """
    selected = {
        station_identifier(entry.entry_id, station_id)
        for station_id in entry.options.get(CONF_STATIONS, [])
    }
    return not any(
        domain == DOMAIN and identifier in selected
        for domain, identifier in device_entry.identifiers
    )
