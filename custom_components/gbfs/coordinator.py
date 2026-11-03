"""DataUpdateCoordinator for GBFS bike-share feeds."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FEED_STATION_INFORMATION,
    FEED_STATION_STATUS,
    FEED_VEHICLE_TYPES,
    CannotConnect,
    GbfsError,
    InvalidFeed,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

# Vehicle types (GBFS 2.1+) categorized as e-bikes
EBIKE_FORM_FACTORS = frozenset({"bicycle", "cargo_bicycle"})
EBIKE_PROPULSION_TYPES = frozenset({"electric_assist", "electric"})

type GbfsConfigEntry = ConfigEntry[GbfsCoordinator]


async def async_fetch_json(session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
    """Download and parse JSON from a feed URL."""
    try:
        async with session.get(url, timeout=REQUEST_TIMEOUT) as resp:
            resp.raise_for_status()
            # Set content_type=None because some feeds return JSON as text/plain
            data = await resp.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError) as err:
        raise CannotConnect(f"Error querying {url}: {err}") from err
    except ValueError as err:
        raise InvalidFeed(f"Invalid JSON in {url}") from err
    if not isinstance(data, dict):
        raise InvalidFeed(f"Unexpected response in {url}")
    return data


def _pick_language[T](items: Iterable[tuple[Any, T]], language: str | None) -> T | None:
    """Select the item matching the requested language subtag, or the first item."""
    items = list(items)
    if not items:
        return None
    if language:
        wanted = language.split("-")[0].lower()
        for lang, item in items:
            if isinstance(lang, str) and lang.split("-")[0].lower() == wanted:
                return item
    return items[0][1]


def resolve_feeds(
    discovery: dict[str, Any], language: str | None = None
) -> dict[str, str]:
    """Resolve gbfs.json discovery payload to a feed name to URL mapping."""
    data = discovery.get("data")
    if not isinstance(data, dict):
        raise InvalidFeed("gbfs.json does not contain the 'data' key")

    if isinstance(data.get("feeds"), list):
        feeds_list = data["feeds"]
    else:
        feeds_list = _pick_language(
            (
                (lang, value["feeds"])
                for lang, value in data.items()
                if isinstance(value, dict) and isinstance(value.get("feeds"), list)
            ),
            language,
        )
        if feeds_list is None:
            raise InvalidFeed("gbfs.json does not contain any feed list")

    feeds = {
        feed["name"]: feed["url"]
        for feed in feeds_list
        if isinstance(feed, dict) and "name" in feed and "url" in feed
    }
    for required in (FEED_STATION_INFORMATION, FEED_STATION_STATUS):
        if required not in feeds:
            raise InvalidFeed(f"The GBFS feed does not publish {required}")
    return feeds


def localized_text(value: Any, language: str | None) -> str | None:
    """Extract localized string from a plain text value or GBFS 3.0 translation list."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return _pick_language(
            (
                (item.get("language"), item["text"])
                for item in value
                if isinstance(item, dict) and isinstance(item.get("text"), str)
            ),
            language,
        )
    return None


def parse_timestamp(value: Any) -> datetime | None:
    """Parse POSIX epoch seconds or RFC 3339 datetime text."""
    if isinstance(value, (int, float)):
        return dt_util.utc_from_timestamp(value)
    if isinstance(value, str) and (parsed := dt_util.parse_datetime(value)):
        # Require timezone offset to prevent ambiguous local timestamps
        return parsed if parsed.tzinfo else None
    return None


def ebike_type_ids(vehicle_types: dict[str, Any]) -> set[str]:
    """Extract vehicle type IDs representing electric bicycles."""
    data = vehicle_types.get("data")
    types = data.get("vehicle_types") if isinstance(data, dict) else None
    if not isinstance(types, list):
        return set()
    return {
        str(vehicle_type["vehicle_type_id"])
        for vehicle_type in types
        if isinstance(vehicle_type, dict)
        and "vehicle_type_id" in vehicle_type
        and vehicle_type.get("form_factor") in EBIKE_FORM_FACTORS
        and vehicle_type.get("propulsion_type") in EBIKE_PROPULSION_TYPES
    }


def _first(record: dict[str, Any], *fields: str) -> Any:
    """Return value of the first matching field found in the record."""
    return next((record[field] for field in fields if field in record), None)


def _as_bool(value: Any) -> bool | None:
    return None if value is None else bool(value)


def _ebikes_available(record: dict[str, Any], ebike_types: set[str]) -> int | None:
    """Extract available e-bike count from direct field or vehicle type breakdown."""
    if "num_ebikes_available" in record:
        return record["num_ebikes_available"]
    counts = record.get("vehicle_types_available")
    if not ebike_types or not isinstance(counts, list):
        return None
    return sum(
        item["count"]
        for item in counts
        if isinstance(item, dict)
        and str(item.get("vehicle_type_id")) in ebike_types
        and isinstance(item.get("count"), int)
    )


@dataclass(frozen=True, kw_only=True, slots=True)
class StationStatus:
    """Normalized status for a bike-share station across GBFS versions."""

    bikes_available: int | None = None
    ebikes_available: int | None = None
    bikes_disabled: int | None = None
    docks_available: int | None = None
    docks_disabled: int | None = None
    is_renting: bool | None = None
    is_returning: bool | None = None
    last_reported: datetime | None = None

    @classmethod
    def from_feed(cls, record: dict[str, Any], ebike_types: set[str]) -> StationStatus:
        """Parse a raw station_status.json record into StationStatus."""
        return cls(
            bikes_available=_first(
                record, "num_bikes_available", "num_vehicles_available"
            ),
            ebikes_available=_ebikes_available(record, ebike_types),
            bikes_disabled=_first(
                record, "num_bikes_disabled", "num_vehicles_disabled"
            ),
            docks_available=record.get("num_docks_available"),
            docks_disabled=record.get("num_docks_disabled"),
            is_renting=_as_bool(record.get("is_renting")),
            is_returning=_as_bool(record.get("is_returning")),
            last_reported=parse_timestamp(record.get("last_reported")),
        )


class GbfsCoordinator(DataUpdateCoordinator[dict[str, StationStatus]]):
    """Coordinator that polls station_status.json for all stations."""

    config_entry: GbfsConfigEntry

    def __init__(self, hass: HomeAssistant, entry: GbfsConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._session = async_get_clientsession(hass)
        self._url: str = entry.data[CONF_URL]
        self._feeds: dict[str, str] = {}
        self.station_info: dict[str, dict[str, Any]] = {}
        self.ebike_types: set[str] = set()
        self.raw_status: dict[str, dict[str, Any]] = {}
        self.published_fields: set[str] = set()

    def station_name(self, station_id: str) -> str | None:
        """Return station name in Home Assistant's language if available."""
        info = self.station_info.get(station_id, {})
        return localized_text(info.get("name"), self.hass.config.language)

    async def _async_setup(self) -> None:
        """Perform initial feed discovery and load station metadata."""
        try:
            discovery = await async_fetch_json(self._session, self._url)
            self._feeds = resolve_feeds(discovery, self.hass.config.language)
            info = await async_fetch_json(
                self._session, self._feeds[FEED_STATION_INFORMATION]
            )
            stations = info["data"]["stations"]
        except GbfsError as err:
            raise UpdateFailed(str(err)) from err
        except (KeyError, TypeError) as err:
            raise UpdateFailed(f"Malformed station_information.json: {err}") from err
        self.station_info = {
            str(station["station_id"]): station
            for station in stations
            if isinstance(station, dict) and "station_id" in station
        }
        self.ebike_types = await self._async_ebike_types()

    async def _async_ebike_types(self) -> set[str]:
        """Fetch and identify e-bike vehicle types if published."""
        if (url := self._feeds.get(FEED_VEHICLE_TYPES)) is None:
            return set()
        try:
            return ebike_type_ids(await async_fetch_json(self._session, url))
        except GbfsError as err:
            _LOGGER.warning("Not counting e-bikes by vehicle type: %s", err)
            return set()

    async def _async_update_data(self) -> dict[str, StationStatus]:
        """Fetch and parse station_status.json for all stations."""
        try:
            status = await async_fetch_json(
                self._session, self._feeds[FEED_STATION_STATUS]
            )
            stations = status["data"]["stations"]
            if not isinstance(stations, list):
                raise TypeError("'stations' is not a list")
        except GbfsError as err:
            raise UpdateFailed(str(err)) from err
        except (KeyError, TypeError) as err:
            raise UpdateFailed(f"Malformed station_status.json: {err}") from err

        self.raw_status = {
            str(station["station_id"]): station
            for station in stations
            if isinstance(station, dict) and "station_id" in station
        }
        self.published_fields = {
            field for station in self.raw_status.values() for field in station
        }

        # Respect the feed's ttl if greater than the default interval
        ttl = status.get("ttl")
        if isinstance(ttl, int):
            interval = timedelta(seconds=max(DEFAULT_SCAN_INTERVAL, ttl))
            if self.update_interval != interval:
                _LOGGER.debug("Adjusting poll interval to %s due to feed ttl", interval)
                self.update_interval = interval

        return {
            station_id: StationStatus.from_feed(record, self.ebike_types)
            for station_id, record in self.raw_status.items()
        }
