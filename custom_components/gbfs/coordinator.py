"""DataUpdateCoordinator for GBFS: a single poll to station_status.json feeds all stations."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
        by_language = {
            lang: value["feeds"]
            for lang, value in data.items()
            if isinstance(value, dict) and isinstance(value.get("feeds"), list)
        }
        if not by_language:
            raise InvalidFeed("gbfs.json does not contain any feed list")
        feeds_list = None
        if language:
            short = language.split("-")[0].lower()
            for lang, feeds in by_language.items():
                if lang.split("-")[0].lower() == short:
                    feeds_list = feeds
                    break
        if feeds_list is None:
            feeds_list = next(iter(by_language.values()))

    feeds = {
        feed["name"]: feed["url"]
        for feed in feeds_list
        if isinstance(feed, dict) and "name" in feed and "url" in feed
    }
    for required in (FEED_STATION_INFORMATION, FEED_STATION_STATUS):
        if required not in feeds:
            raise InvalidFeed(f"The GBFS feed does not publish {required}")
    return feeds


class GbfsCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
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
        # Optional station_status fields that the feed publishes; conditional
        # sensors (e-bikes, disabled) depend on this.
        self.published_fields: set[str] = set()

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

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
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

        data = {
            str(station["station_id"]): station
            for station in stations
            if isinstance(station, dict) and "station_id" in station
        }
        self.published_fields = {
            field for station in data.values() for field in station
        }

        # Respect the feed's ttl if greater than the default interval
        ttl = status.get("ttl")
        if isinstance(ttl, int):
            interval = timedelta(seconds=max(DEFAULT_SCAN_INTERVAL, ttl))
            if self.update_interval != interval:
                _LOGGER.debug("Adjusting poll interval to %s due to feed ttl", interval)
                self.update_interval = interval

        return data
