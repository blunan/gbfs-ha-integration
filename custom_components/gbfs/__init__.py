"""GBFS integration: monitors bike-share stations."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import GbfsConfigEntry, GbfsCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: GbfsConfigEntry) -> bool:
    """Sets up a GBFS feed from a config entry."""
    coordinator = GbfsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: GbfsConfigEntry) -> None:
    """Reloads the entry when selected stations change (options flow)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GbfsConfigEntry) -> bool:
    """Unloads a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
