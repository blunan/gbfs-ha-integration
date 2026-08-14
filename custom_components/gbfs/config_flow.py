"""GBFS config flow: URL of gbfs.json → multi-select of stations by name."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse, urlunparse

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_STATIONS,
    CONF_URL,
    DOMAIN,
    FEED_STATION_INFORMATION,
    FEED_SYSTEM_INFORMATION,
    CannotConnect,
    GbfsError,
    InvalidFeed,
)
from .coordinator import GbfsConfigEntry, async_fetch_json, resolve_feeds


def _normalize_url(url: str) -> str:
    """Normalized feed URL for the entry's unique_id (scheme/host are case-insensitive)."""
    parts = urlparse(url)
    return urlunparse(
        parts._replace(scheme=parts.scheme.lower(), netloc=parts.netloc.lower())
    ).rstrip("/")


USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        ),
    }
)


def _stations_schema(
    stations: dict[str, str], selected: list[str] | None = None
) -> vol.Schema:
    """Multi-select of stations ordered by name."""
    options = [
        SelectOptionDict(value=station_id, label=name)
        for station_id, name in sorted(stations.items(), key=lambda item: item[1])
    ]
    field = vol.Required(CONF_STATIONS)
    if selected is not None:
        field = vol.Required(CONF_STATIONS, default=selected)
    return vol.Schema(
        {
            field: SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                    sort=False,
                )
            ),
        }
    )


class GbfsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Step 1: Feed URL. Step 2: Station selection."""

    VERSION = 1

    def __init__(self) -> None:
        self._url: str = ""
        self._title: str = ""
        self._stations: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Asks for the gbfs.json URL and performs feed auto-discovery."""
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip()
            await self.async_set_unique_id(_normalize_url(url))
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            try:
                discovery = await async_fetch_json(session, url)
                feeds = resolve_feeds(discovery, self.hass.config.language)
                info = await async_fetch_json(session, feeds[FEED_STATION_INFORMATION])
                stations = info["data"]["stations"]
                if not isinstance(stations, list) or not stations:
                    raise InvalidFeed("station_information.json has no stations")
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except (InvalidFeed, KeyError, TypeError):
                errors["base"] = "invalid_feed"
            else:
                self._url = url
                self._stations = {
                    str(station["station_id"]): str(
                        station.get("name", station["station_id"])
                    )
                    for station in stations
                    if isinstance(station, dict) and "station_id" in station
                }
                self._title = await self._async_system_name(session, feeds)
                return await self.async_step_stations()

        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
        )

    async def _async_system_name(self, session: Any, feeds: dict[str, str]) -> str:
        """System name (system_information.json) for the entry title."""
        if url := feeds.get(FEED_SYSTEM_INFORMATION):
            try:
                info = await async_fetch_json(session, url)
                if name := info.get("data", {}).get("name"):
                    return str(name)
            except GbfsError:
                pass
        return urlparse(self._url).hostname or "GBFS"

    async def async_step_stations(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Multi-select of stations by name."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._title,
                data={CONF_URL: self._url},
                options={CONF_STATIONS: user_input[CONF_STATIONS]},
            )
        return self.async_show_form(
            step_id="stations", data_schema=_stations_schema(self._stations)
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: GbfsConfigEntry) -> GbfsOptionsFlow:
        return GbfsOptionsFlow()


class GbfsOptionsFlow(OptionsFlow):
    """Add/remove stations without reinstalling the integration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_STATIONS: user_input[CONF_STATIONS]}
            )

        coordinator = self.config_entry.runtime_data
        stations = {
            station_id: str(info.get("name", station_id))
            for station_id, info in coordinator.station_info.items()
        }
        selected = [
            station_id
            for station_id in self.config_entry.options.get(CONF_STATIONS, [])
            if station_id in stations
        ]
        return self.async_show_form(
            step_id="init", data_schema=_stations_schema(stations, selected)
        )
