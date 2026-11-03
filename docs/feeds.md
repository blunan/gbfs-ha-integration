# Supported Feeds

Technical reference for General Bikeshare Feed Specification ([GBFS](https://gbfs.org/)) compatibility and data mapping.

## Feed Requirements

A bike-share feed is compatible if it provides:

1. A publicly accessible `gbfs.json` auto-discovery URL that does not require authentication, API keys, or custom headers.
2. Both `station_information` and `station_status` feeds listed in its discovery file.
3. At least one physical docking station defined in `station_information.json`.

Optional feeds:
- `system_information.json`: Used to title the integration entry. If omitted, the hostname is used.
- `vehicle_types.json`: Used to identify e-bike vehicle types (GBFS 2.1+).

## GBFS Versions

The integration normalizes differences between GBFS versions automatically without version-specific user settings:

| Feature | GBFS 1.x & 2.x | GBFS 3.0 |
|---|---|---|
| **Discovery structure** | Feeds nested under language keys: `data.<lang>.feeds` | Single unified list: `data.feeds` |
| **String localization** | Separate files per language | Inline translation lists `[{"text": "...", "language": "..."}]` |
| **Timestamps** | POSIX epoch seconds | ISO 8601 / RFC 3339 strings with timezone offset |
| **Bike counts** | `num_bikes_available`, `num_bikes_disabled` | `num_vehicles_available`, `num_vehicles_disabled` |
| **Status flags** | `0`/`1` (1.x) or `true`/`false` (2.x) | `true`/`false` |
| **E-bike counts** | Custom `num_ebikes_available` or `vehicle_types_available` | `vehicle_types_available` |

## Language Handling { #languages }

- **GBFS 1.x / 2.x:** The integration selects the feed set matching Home Assistant's configured language (primary subtag match, e.g., `es` matches `es-MX`). If no match is found, the first listed language set is used.
- **GBFS 3.0:** Localized strings are resolved against Home Assistant's language, falling back to the default translation.

This determines the station names and entry title displayed in Home Assistant.

## Processed Endpoints and Fields

The integration reads only the fields required for station monitoring:

| Feed | Fields Read | Purpose |
|---|---|---|
| `gbfs.json` | `name`, `url` | Locates sub-feeds |
| `system_information.json` | `name` | Integration entry title |
| `station_information.json` | `station_id`, `name`, `lat`, `lon` | Station metadata and coordinates |
| `station_status.json` | `ttl`, `station_id`, `num_bikes_available`, `num_vehicles_available`, `num_bikes_disabled`, `num_vehicles_disabled`, `num_docks_available`, `num_docks_disabled`, `num_ebikes_available`, `vehicle_types_available`, `is_renting`, `is_returning`, `last_reported` | Live station metrics and availability |
| `vehicle_types.json` | `vehicle_type_id`, `form_factor`, `propulsion_type` | Identifies which vehicle types represent electric bicycles |

Unused feeds (such as `free_bike_status.json`, `geofencing_zones.json`, and `system_pricing_plans.json`) are ignored to minimize bandwidth.

## E-bike Detection Logic { #e-bikes }

The **E-bikes available** entity is generated when the feed provides e-bike metrics using either:

1. **Direct counts:** The station record contains `num_ebikes_available` (standard in systems operated by Lyft/Motivate, such as Citi Bike and Divvy).
2. **Vehicle type breakdown (GBFS 2.1+):** The station record includes `vehicle_types_available`, and `vehicle_types.json` defines types where:
    - `form_factor` is `bicycle` or `cargo_bicycle`
    - `propulsion_type` is `electric_assist` or `electric`

Counts for non-bicycle vehicles (scooters, mopeds, cars) are excluded. If a feed provides neither mechanism, the e-bike entity is not created.

## Unsupported Feed Types

- **Dockless-only systems:** Systems with free-floating vehicles and no docking stations (`free_bike_status.json` or `vehicle_status.json` only).
- **Authenticated feeds:** Feeds requiring API keys, tokens, or basic authentication.
- **Non-station metrics:** System alerts, pricing plans, and individual vehicle battery levels.

## Server Polling and Traffic

- **Routine updates:** Fetches `station_status.json` at most once every 60 seconds, or at the feed's reported `ttl` if longer.
- **Startup:** Fetches `gbfs.json`, `station_information.json`, and optionally `system_information.json` and `vehicle_types.json`.
- A single request updates all stations tracked from that feed.
