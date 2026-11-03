"""DataUpdateCoordinator for GBFS: a single poll to station_status.json feeds all stations."""

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
    CannotConnect,
    GbfsError,
    InvalidFeed,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

type GbfsConfigEntry = ConfigEntry[GbfsCoordinator]


async def async_fetch_json(session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
    """Downloads and parses a JSON from the GBFS feed."""
    try:
        async with session.get(url, timeout=REQUEST_TIMEOUT) as resp:
            resp.raise_for_status()
            # content_type=None: some feeds serve JSON as text/plain
            data = await resp.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError) as err:
        raise CannotConnect(f"Error querying {url}: {err}") from err
    except ValueError as err:
        raise InvalidFeed(f"Invalid JSON in {url}") from err
    if not isinstance(data, dict):
        raise InvalidFeed(f"Unexpected response in {url}")
    return data


def _pick_language[T](items: Iterable[tuple[Any, T]], language: str | None) -> T | None:
    """Item whose language matches `language` (primary subtag), or else the first one."""
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
    """Resolves gbfs.json to a name→URL map of feeds.

    Supports GBFS 1.x/2.x (data.{lang}.feeds) and GBFS 3.0 (data.feeds).
    """
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
    """Text of a GBFS string: plain (1.x/2.x) or a list of translations (3.0)."""
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
    """A GBFS timestamp: POSIX seconds (1.x/2.x) or RFC 3339 text (3.0)."""
    if isinstance(value, (int, float)):
        return dt_util.utc_from_timestamp(value)
    if isinstance(value, str) and (parsed := dt_util.parse_datetime(value)):
        # RFC 3339 requires an offset: without one, the time is ambiguous
        return parsed if parsed.tzinfo else None
    return None


def _first(record: dict[str, Any], *fields: str) -> Any:
    """Value of the first field the record has: GBFS 3.0 renamed some."""
    return next((record[field] for field in fields if field in record), None)


def _as_bool(value: Any) -> bool | None:
    # GBFS 1.x uses 0/1, later versions true/false
    return None if value is None else bool(value)


@dataclass(frozen=True, kw_only=True, slots=True)
class StationStatus:
    """A station's status, read the same way from every GBFS version."""

    bikes_available: int | None = None
    ebikes_available: int | None = None
    bikes_disabled: int | None = None
    docks_available: int | None = None
    docks_disabled: int | None = None
    is_renting: bool | None = None
    is_returning: bool | None = None
    last_reported: datetime | None = None

    @classmethod
    def from_feed(cls, record: dict[str, Any]) -> StationStatus:
        """Reads a station of station_status.json, whatever its GBFS version."""
        return cls(
            bikes_available=_first(
                record, "num_bikes_available", "num_vehicles_available"
            ),
            # Not in the GBFS spec, but some operators (Lyft-run systems) publish it
            ebikes_available=record.get("num_ebikes_available"),
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
    """Coordinator that polls station_status.json and exposes data by station_id."""

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
        # The latest station_status.json records as published, and the fields
        # they have (for diagnostics)
        self.raw_status: dict[str, dict[str, Any]] = {}
        self.published_fields: set[str] = set()

    def station_name(self, station_id: str) -> str | None:
        """Station name, in Home Assistant's language if the feed translates it."""
        info = self.station_info.get(station_id, {})
        return localized_text(info.get("name"), self.hass.config.language)

    async def _async_setup(self) -> None:
        """Feed auto-discovery and loading station_information (once only)."""
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

    async def _async_update_data(self) -> dict[str, StationStatus]:
        """A single poll to station_status.json for all stations."""
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
            station_id: StationStatus.from_feed(record)
            for station_id, record in self.raw_status.items()
        }
