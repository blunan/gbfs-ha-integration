"""Base GBFS entity: groups entities of a station in one device."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GbfsCoordinator, StationStatus

# Status of a station missing from the latest poll: every value unknown
NO_STATUS = StationStatus()


def station_identifier(entry_id: str, station_id: str) -> str:
    """Device identifier of a station, scoped to its entry: systems reuse IDs."""
    return f"{entry_id}_{station_id}"


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
        identifier = station_identifier(coordinator.config_entry.entry_id, station_id)
        self._attr_unique_id = f"{identifier}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=coordinator.station_name(station_id) or f"Station {station_id}",
            manufacturer="GBFS",
            model="Bike share station",
        )

    @property
    def available(self) -> bool:
        """The entity is available if the station appears in the latest poll."""
        return super().available and self._station_id in self.coordinator.data

    @property
    def station_status(self) -> StationStatus:
        """Current status of the station in station_status.json."""
        return self.coordinator.data.get(self._station_id, NO_STATUS)
