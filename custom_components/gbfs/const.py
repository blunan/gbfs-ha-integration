"""Constants for the GBFS integration."""

DOMAIN = "gbfs"

CONF_URL = "url"
CONF_STATIONS = "stations"

DEFAULT_SCAN_INTERVAL = 60

FEED_STATION_INFORMATION = "station_information"
FEED_STATION_STATUS = "station_status"
FEED_SYSTEM_INFORMATION = "system_information"


class GbfsError(Exception):
    """Base error for the GBFS integration."""


class CannotConnect(GbfsError):
    """Could not connect to the GBFS feed."""


class InvalidFeed(GbfsError):
    """The GBFS feed does not have the expected structure."""
