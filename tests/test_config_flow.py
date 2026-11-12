"""Tests for GBFS config flow and options flow."""

from __future__ import annotations

from typing import Any

import aiohttp
import pytest

from custom_components.gbfs.const import CONF_STATIONS, CONF_URL, DOMAIN, EXAMPLE_URL
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import GBFS_URL, GBFS_URL_V3


def _station_labels(result: dict[str, Any]) -> list[str]:
    """Return station picker labels from form schema in display order."""
    selector = result["data_schema"].schema[CONF_STATIONS]
    return [option["label"] for option in selector.config["options"]]


async def test_full_flow(hass: HomeAssistant, mock_feeds) -> None:
    """Happy path: URL → station selection → entry created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["description_placeholders"] == {"example_url": EXAMPLE_URL}

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


@pytest.mark.parametrize(
    ("language", "title", "labels"),
    [
        ("en", "Example Bikes", ["Estación Gamma", "Station Alpha", "Station Beta"]),
        (
            "es",
            "Bicis de Ejemplo",
            ["Estación Alfa", "Estación Beta", "Estación Gamma"],
        ),
    ],
)
async def test_full_flow_v3(
    hass: HomeAssistant,
    mock_feeds_v3,
    language: str,
    title: str,
    labels: list[str],
) -> None:
    """GBFS 3.0: system and station names in Home Assistant's language."""
    hass.config.language = language
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: GBFS_URL_V3}
    )
    assert result["step_id"] == "stations"
    assert _station_labels(result) == labels

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATIONS: ["1"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == title


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
    """Non-GBFS JSON payload shows invalid_feed."""
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


async def test_options_flow_v3(
    hass: HomeAssistant, mock_feeds_v3, config_entry_v3
) -> None:
    """GBFS 3.0: the options flow lists translated station names."""
    assert await hass.config_entries.async_setup(config_entry_v3.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry_v3.entry_id)
    assert _station_labels(result) == [
        "Estación Gamma",
        "Station Alpha",
        "Station Beta",
    ]
