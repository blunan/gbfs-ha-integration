"""Tests for GBFS config flow and options flow."""

from __future__ import annotations

import aiohttp

from custom_components.gbfs.const import CONF_STATIONS, CONF_URL, DOMAIN
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import GBFS_URL


async def test_full_flow(hass: HomeAssistant, mock_feeds) -> None:
    """Happy path: URL → station selection → entry created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: GBFS_URL}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "stations"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATIONS: ["1", "3"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Example Bikes"
    assert result["data"] == {CONF_URL: GBFS_URL}
    assert result["options"] == {CONF_STATIONS: ["1", "3"]}


async def test_cannot_connect(hass: HomeAssistant, aioclient_mock) -> None:
    """Network error in gbfs.json shows cannot_connect."""
    aioclient_mock.get(GBFS_URL, exc=aiohttp.ClientError("boom"))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: GBFS_URL}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_invalid_feed(hass: HomeAssistant, aioclient_mock) -> None:
    """A JSON that is not GBFS shows invalid_feed."""
    aioclient_mock.get(GBFS_URL, json={"hello": "world"})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: GBFS_URL}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_feed"}


async def test_already_configured(
    hass: HomeAssistant, mock_feeds, config_entry
) -> None:
    """The same URL cannot be configured twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: GBFS_URL}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_already_configured_normalizes_url(
    hass: HomeAssistant, mock_feeds, config_entry
) -> None:
    """URL variants (host/scheme casing, trailing slash) dedupe against the same feed."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: "HTTPS://GBFS.EXAMPLE.COM/gbfs/gbfs.json/"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant, mock_feeds, config_entry) -> None:
    """The options flow allows changing the selected stations."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_STATIONS: ["2", "3"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {CONF_STATIONS: ["2", "3"]}
