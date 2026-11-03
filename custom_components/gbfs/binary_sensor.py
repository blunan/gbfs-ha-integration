"""Binary sensors per station: is_renting and is_returning."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_STATIONS
from .coordinator import GbfsConfigEntry, StationStatus
from .entity import GbfsEntity


@dataclass(frozen=True, kw_only=True)
class GbfsBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Description of a GBFS binary sensor."""

    value_fn: Callable[[StationStatus], bool | None]


BINARY_SENSORS: tuple[GbfsBinarySensorEntityDescription, ...] = (
    GbfsBinarySensorEntityDescription(
        key="is_renting",
        translation_key="is_renting",
        value_fn=lambda station: station.is_renting,
    ),
    GbfsBinarySensorEntityDescription(
        key="is_returning",
        translation_key="is_returning",
        value_fn=lambda station: station.is_returning,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GbfsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Creates binary sensors for the selected stations."""
    coordinator = entry.runtime_data
    async_add_entities(
        GbfsBinarySensor(coordinator, station_id, description)
        for station_id in entry.options.get(CONF_STATIONS, [])
        for description in BINARY_SENSORS
    )


class GbfsBinarySensor(GbfsEntity, BinarySensorEntity):
    """Binary sensor for a GBFS station."""

    entity_description: GbfsBinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.station_status)
