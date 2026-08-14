"""Base GBFS entity: groups entities of a station in one device."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GbfsCoordinator


class GbfsEntity(CoordinatorEntity[GbfsCoordinator]):
    """Base for all entities of a GBFS station."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GbfsCoordinator,
        station_id: str,
        description: EntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._station_id = station_id
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{station_id}_{description.key}"
        )
        info = coordinator.station_info.get(station_id, {})
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.config_entry.entry_id}_{station_id}")},
            name=info.get("name", f"Station {station_id}"),
            manufacturer="GBFS",
            model="Bike share station",
        )

    @property
    def available(self) -> bool:
        """The entity is available if the station appears in the latest poll."""
        return super().available and self._station_id in self.coordinator.data

    @property
    def station_status(self) -> dict[str, Any]:
        """Current status of the station in station_status.json."""
        return self.coordinator.data.get(self._station_id, {})
