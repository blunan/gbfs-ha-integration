# How It Works

Technical overview of integration architecture, feed normalization, coordinator lifecycle, and entity design.

## Code Map

Integration source files live in `custom_components/gbfs/`:

| File | Purpose |
|---|---|
| `manifest.json` | Integration metadata, IoT class (`cloud_polling`), and platforms |
| `__init__.py` | Entry setup and unloading, platform forwarding, and device cleanup validation |
| `config_flow.py` | Feed discovery UI, station picker, and options flow |
| `coordinator.py` | Data fetching, feed resolution, version normalization, and polling logic |
| `entity.py` | `GbfsEntity` base class: device registration, unique IDs, and availability |
| `sensor.py` | Sensor entity descriptions and value extractors |
| `binary_sensor.py` | Binary sensor descriptions for station rental and return flags |
| `diagnostics.py` | Diagnostic payload generator for config entries |
| `const.py` | Integration constants and exception hierarchy |
| `strings.json`, `translations/` | UI and entity strings in English and Spanish |
| `brand/` | Integration icon and branding assets |

## Lifecycle Overview

```text
Config Flow (Setup)
  1. User enters feed URL → fetch gbfs.json → resolve_feeds()
  2. Fetch station_information.json (station list) & system_information.json (title)
  3. User selects stations → creates config entry

Entry Startup (Boot, Reload, or Options Change)
  1. GbfsCoordinator._async_setup():
     - Resolve feeds and fetch station_information.json
     - Fetch vehicle_types.json (if present, to identify e-bike types)
  2. GbfsCoordinator._async_update_data():
     - Fetch station_status.json (first refresh)
  3. Platform Setup:
     - Instantiate entities for selected stations matching available feed fields

Periodic Polling (Every 60s or feed TTL)
  1. GbfsCoordinator._async_update_data():
     - Fetch station_status.json
     - Parse records into typed StationStatus dataclasses
     - Dynamically adjust update interval if feed TTL exceeds 60 seconds
  2. Entities update state
```

## Feed Discovery and Resolution

`resolve_feeds(discovery, language)` processes `gbfs.json` into a `{feed_name: url}` dictionary:

- **GBFS 3.0:** Reads `data.feeds` directly.
- **GBFS 1.x & 2.x:** Iterates `data.<lang>.feeds` dictionaries, matching Home Assistant's primary language subtag (e.g., `es` matches `es-MX`). Falls back to the first listed language if none match.
- Validates that required endpoints (`station_information` and `station_status`) are present, raising `InvalidFeed` if either is missing.

## Network Requests

`async_fetch_json(session, url)` handles HTTP requests using Home Assistant's shared aiohttp client session:

- Configured with a 30-second timeout.
- Sets `content_type=None` when parsing JSON, accommodating operators that return JSON payloads with `text/plain` headers.
- Network and HTTP errors raise `CannotConnect`; malformed or unexpected JSON raises `InvalidFeed`. Both inherit from `GbfsError`.

## Multi-Version Data Normalization

The integration normalizes variations across GBFS specifications into a consistent internal model:

| Helper Function | Normalization Handled |
|---|---|
| `localized_text(value, language)` | Resolves plain strings (1.x/2.x) and localized object lists (3.0) against current language |
| `parse_timestamp(value)` | Converts POSIX epoch seconds (1.x/2.x) and RFC 3339 datetime strings (3.0 with offset) to UTC datetimes |
| `ebike_type_ids(vehicle_types)` | Extracts IDs for vehicle types where `form_factor` is `bicycle`/`cargo_bicycle` and `propulsion_type` is `electric_assist`/`electric` |
| `StationStatus.from_feed(record, ebike_types)` | Maps raw station records to typed `StationStatus` instances |

### StationStatus Dataclass

`StationStatus` is a frozen dataclass representing the normalized state of a single station:

- Evaluates renamed fields (`num_bikes_available` vs. 3.0 `num_vehicles_available`).
- Converts `0`/`1` and boolean values into native Python booleans.
- Resolves e-bikes from `num_ebikes_available` first; if absent, aggregates counts from `vehicle_types_available` matching identified e-bike types.

## DataUpdateCoordinator Implementation

`GbfsCoordinator` coordinates polling of `station_status.json`:

- **Single Polling Request:** One HTTP GET retrieves status for all stations in the system, eliminating per-station overhead.
- **Station Metadata Caching:** Station names, coordinates, and e-bike definitions are loaded during `_async_setup` and cached for the duration of the entry.
- **Dynamic Polling Interval:** Defaults to 60 seconds. If `station_status.json` includes a valid integer `ttl` greater than 60 seconds, the coordinator dynamically extends its interval to match.
- **Diagnostics Snapshot:** Retains raw unparsed status records and tracks all observed field names in `published_fields`.

## Entity Design

Entities inherit from `GbfsEntity`, which extends Home Assistant's `CoordinatorEntity`:

- **Device Linking:** Groups all entities for a station into a single Home Assistant device using the identifier `("gbfs", f"{entry_id}_{station_id}")`. Scoping with `entry_id` prevents ID collisions across independent bike-share operators.
- **Availability:** An entity is `available` only when the coordinator's last update succeeded and the station is present in `coordinator.data`.
- **Feed-Aware Instantiation:** Entity descriptions include an `optional` attribute. Optional entities (such as e-bikes or disabled equipment counts) are only instantiated if at least one station in the system reports data for that field during initial setup.
- **Map Positioning:** Only `bikes_available` sets `has_location=True`, adding `latitude` and `longitude` attributes from cached station metadata so map cards display exactly one marker per station.

## Device Cleanup Validation

`async_remove_config_entry_device` in `__init__.py` allows users to remove station devices from the UI once unselected in options:

- Deleting an active, currently selected station device is rejected (`False`) because reload would recreate it.
- If the station is unselected in `entry.options["stations"]`, the integration returns `True`, removing the device and its entities from the registry.

## Architectural Principles

- **Single Request per Poll:** Download `station_status.json` once per bike-share system, regardless of the number of selected stations.
- **Zero Configuration Versioning:** Ingest GBFS 1.x, 2.x, and 3.0 feeds without requiring version flags from the user.
- **Clean Registry Footprint:** Avoid cluttering entities with permanent `unknown` states by checking feed capabilities before instantiating optional sensors.
- **Network Resilience:** Handle HTTP transients with coordinator retry backoff without losing historical device associations.
