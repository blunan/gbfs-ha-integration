"""Sensors per station: bikes, e-bikes (if feed publishes them), docks, occupancy, and last report."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    PERCENTAGE,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .const import CONF_STATIONS
from .coordinator import GbfsConfigEntry, GbfsCoordinator
from .entity import GbfsEntity


@dataclass(frozen=True, kw_only=True)
class GbfsSensorEntityDescription(SensorEntityDescription):
    """Description of a GBFS sensor."""

    value_fn: Callable[[dict[str, Any]], StateType | datetime]
    exists_fn: Callable[[GbfsCoordinator], bool] = lambda _: True
    # Only one entity per station carries lat/lon so the map card
    # shows a single marker per station
    has_location: bool = False


def _occupancy(status: dict[str, Any]) -> float | None:
    bikes = status.get("num_bikes_available")
    docks = status.get("num_docks_available")
    if bikes is None or docks is None or bikes + docks == 0:
        return None
    return round(bikes / (bikes + docks) * 100, 1)


def _last_reported(status: dict[str, Any]) -> datetime | None:
    if (timestamp := status.get("last_reported")) is None:
        return None
    return dt_util.utc_from_timestamp(timestamp)


SENSORS: tuple[GbfsSensorEntityDescription, ...] = (
    GbfsSensorEntityDescription(
        key="bikes_available",
        translation_key="bikes_available",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda status: status.get("num_bikes_available"),
        has_location=True,
    ),
    GbfsSensorEntityDescription(
        key="ebikes_available",
        translation_key="ebikes_available",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda status: status.get("num_ebikes_available"),
        # Only if feed publishes e-bikes (varies by operator's GBFS version)
        exists_fn=lambda coordinator: (
            "num_ebikes_available" in coordinator.published_fields
        ),
    ),
    GbfsSensorEntityDescription(
        key="bikes_disabled",
        translation_key="bikes_disabled",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda status: status.get("num_bikes_disabled"),
        # Optional field in GBFS spec
        exists_fn=lambda coordinator: (
            "num_bikes_disabled" in coordinator.published_fields
        ),
    ),
    GbfsSensorEntityDescription(
        key="docks_available",
        translation_key="docks_available",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda status: status.get("num_docks_available"),
    ),
    GbfsSensorEntityDescription(
        key="docks_disabled",
        translation_key="docks_disabled",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda status: status.get("num_docks_disabled"),
        # Optional field in GBFS spec
        exists_fn=lambda coordinator: (
            "num_docks_disabled" in coordinator.published_fields
        ),
    ),
    GbfsSensorEntityDescription(
        key="occupancy",
        translation_key="occupancy",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_occupancy,
    ),
    GbfsSensorEntityDescription(
        key="last_reported",
        translation_key="last_reported",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_last_reported,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GbfsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Creates sensors for the selected stations."""
    coordinator = entry.runtime_data
    async_add_entities(
        GbfsSensor(coordinator, station_id, description)
        for station_id in entry.options.get(CONF_STATIONS, [])
        for description in SENSORS
        if description.exists_fn(coordinator)
    )


class GbfsSensor(GbfsEntity, SensorEntity):
    """Sensor for a GBFS station."""

    entity_description: GbfsSensorEntityDescription

    @property
    def native_value(self) -> StateType | datetime:
        return self.entity_description.value_fn(self.station_status)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Lat/lon from station_information; allow showing the station on the map."""
        if not self.entity_description.has_location:
            return None
        info = self.coordinator.station_info.get(self._station_id, {})
        lat, lon = info.get("lat"), info.get("lon")
        if lat is None or lon is None:
            return None
        return {ATTR_LATITUDE: lat, ATTR_LONGITUDE: lon}
