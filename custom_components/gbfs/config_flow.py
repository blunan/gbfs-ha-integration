"""Config flow for the GBFS integration."""

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
    EXAMPLE_URL,
    FEED_STATION_INFORMATION,
    FEED_SYSTEM_INFORMATION,
    CannotConnect,
    GbfsError,
    InvalidFeed,
)
from .coordinator import (
    GbfsConfigEntry,
    async_fetch_json,
    localized_text,
    resolve_feeds,
)


def _normalize_url(url: str) -> str:
    """Normalize feed URL for unique ID matching (scheme and host are lowercased)."""
    parts = urlparse(url)
    return urlunparse(
        parts._replace(scheme=parts.scheme.lower(), netloc=parts.netloc.lower())
    ).rstrip("/")


def _station_label(station: dict[str, Any], language: str | None) -> str:
    """Return station name for the selector, or station ID if unnamed."""
    return localized_text(station.get("name"), language) or str(station["station_id"])


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
    """Build station selector schema ordered by name."""
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
    """Handle GBFS config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._url: str = ""
        self._title: str = ""
        self._stations: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle initial step: validate feed URL and discover stations."""
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
            except InvalidFeed, KeyError, TypeError:
                errors["base"] = "invalid_feed"
            else:
                self._url = url
                language = self.hass.config.language
                self._stations = {
                    str(station["station_id"]): _station_label(station, language)
                    for station in stations
                    if isinstance(station, dict) and "station_id" in station
                }
                self._title = await self._async_system_name(session, feeds)
                return await self.async_step_stations()

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
            description_placeholders={"example_url": EXAMPLE_URL},
        )

    async def _async_system_name(self, session: Any, feeds: dict[str, str]) -> str:
        """Fetch system name for the entry title."""
        if url := feeds.get(FEED_SYSTEM_INFORMATION):
            try:
                data = (await async_fetch_json(session, url)).get("data")
            except GbfsError:
                data = None
            if isinstance(data, dict) and (
                name := localized_text(data.get("name"), self.hass.config.language)
            ):
                return name
        return urlparse(self._url).hostname or "GBFS"

    async def async_step_stations(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle station selection step."""
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
    """Handle GBFS options flow to add or remove stations."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_STATIONS: user_input[CONF_STATIONS]}
            )

        coordinator = self.config_entry.runtime_data
        stations = {
            station_id: coordinator.station_name(station_id) or station_id
            for station_id in coordinator.station_info
        }
        selected = [
            station_id
            for station_id in self.config_entry.options.get(CONF_STATIONS, [])
            if station_id in stations
        ]
        return self.async_show_form(
            step_id="init", data_schema=_stations_schema(stations, selected)
        )
