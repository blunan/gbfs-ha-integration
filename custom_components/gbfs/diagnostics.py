"""Diagnostics for the GBFS integration."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import GbfsConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: GbfsConfigEntry
) -> dict[str, Any]:
    """Diagnostics of the config entry: feed state and coordinator data."""
    coordinator = entry.runtime_data
    return {
        "entry": {
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "update_interval_seconds": (
            coordinator.update_interval.total_seconds()
            if coordinator.update_interval
            else None
        ),
        "last_update_success": coordinator.last_update_success,
        "published_fields": sorted(coordinator.published_fields),
        "station_info": coordinator.station_info,
        "station_status": coordinator.data,
    }
