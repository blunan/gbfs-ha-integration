# How it works

How the integration discovers a feed, reads any GBFS version, polls it and turns stations into entities. This page is for contributors; you don't need it to use the integration.

## Code map

All code lives in `custom_components/gbfs/`:

| File | What it does |
|---|---|
| `manifest.json` | Integration metadata: a `hub` with a config flow and `cloud_polling`, and no Python requirements beyond Home Assistant's own |
| `__init__.py` | Sets up an entry: creates the coordinator, runs its first refresh and forwards the entry to the `sensor` and `binary_sensor` platforms. Reloads the entry when its options change, and decides which devices users may delete |
| `config_flow.py` | The two setup steps (feed URL, stations), the options flow and the entry's unique ID |
| `coordinator.py` | Downloads and checks JSON, resolves `gbfs.json` into feed URLs, reads station data of any GBFS version, and polls `station_status.json` |
| `entity.py` | `GbfsEntity`, the base of every entity: device info, unique ID and availability |
| `sensor.py` | The seven sensors, as entity descriptions |
| `binary_sensor.py` | The two binary sensors |
| `diagnostics.py` | The entry's diagnostics |
| `const.py` | Constants, and the `GbfsError` exceptions |
| `strings.json`, `translations/` | UI text in English and Spanish |
| `brand/` | The integration's icon, which Home Assistant 2026.3 and later load from the integration's folder |

## Lifecycle

```text
Config flow (once, when the user adds a feed)
  user step        GET gbfs.json → resolve_feeds() → GET station_information.json
                   GET system_information.json (optional, for the entry title)
  stations step    create the entry: data = {url}, options = {stations: [ids]}

Entry start (Home Assistant start, reload, options change)
  _async_setup()          GET gbfs.json → resolve_feeds() → GET station_information.json
                          GET vehicle_types.json (optional, for e-bikes)
  _async_update_data()    GET station_status.json (first refresh)
  platforms               one entity per selected station and description

Every update interval (60 s, or the feed's ttl if longer)
  _async_update_data()    GET station_status.json → every entity updates
```

## Feed discovery

`resolve_feeds(discovery, language)` turns a parsed `gbfs.json` into a `{feed name: URL}` map:

- If `data.feeds` is a list, it's the GBFS 3.0 layout and is used as is.
- Otherwise, every `data.<language>` block with a `feeds` list is a candidate (GBFS 1.x and 2.x). The block whose primary language subtag matches Home Assistant's, ignoring case, wins. If none matches, the first block does.
- Entries without both `name` and `url` are skipped. If `station_information` or `station_status` is missing from the result, it raises `InvalidFeed`.

## Downloads

`async_fetch_json(session, url)` uses Home Assistant's shared aiohttp session with a 30-second total timeout:

| Problem | Raises |
|---|---|
| Connection error, timeout or HTTP error status | `CannotConnect` |
| A body that isn't JSON, or isn't a JSON object | `InvalidFeed` |

It parses the body whatever its `Content-Type`, because some operators serve JSON as `text/plain`. Both exceptions derive from `GbfsError`. The config flow maps them to the `cannot_connect` and `invalid_feed` form errors.

## Reading any GBFS version

The integration never checks a feed's version. Each value is read in whatever form the feed uses, so the rest of the code only sees one model:

| Helper | Handles |
|---|---|
| `localized_text(value, language)` | Names as plain text (1.x and 2.x) or as a list of translations (3.0), picking the language like `resolve_feeds` does |
| `parse_timestamp(value)` | Times as POSIX seconds (1.x and 2.x) or RFC 3339 text (3.0). Text without an offset is ambiguous and returns `None` |
| `ebike_type_ids(vehicle_types)` | The IDs of the electric bicycle types in `vehicle_types.json`: `bicycle` or `cargo_bicycle` with `electric_assist` or `electric` propulsion |
| `StationStatus.from_feed(record, ebike_types)` | One `station_status.json` record into a typed `StationStatus` |

`StationStatus` is a frozen dataclass with `bikes_available`, `ebikes_available`, `bikes_disabled`, `docks_available`, `docks_disabled`, `is_renting`, `is_returning` and `last_reported`, each `None` when the feed doesn't say. `from_feed`:

- Reads renamed counts by their 1.x and 2.x name first, then their 3.0 name (`num_vehicles_available`, `num_vehicles_disabled`).
- Turns `1`/`0` and `true`/`false` flags into booleans.
- Counts e-bikes from `num_ebikes_available` when the record has it. Otherwise, it adds up `vehicle_types_available` for the e-bike types, or gives `None` if the feed has no e-bike types.

## The coordinator

`GbfsCoordinator` is a `DataUpdateCoordinator` whose data maps each station ID to its `StationStatus`. Station IDs are always strings, whatever type the feed uses.

- **`_async_setup()`** runs once per entry start, before the first refresh. It discovers the feeds and loads `station_information.json` into `station_info`, keyed by station ID. It also loads the e-bike types into `ebike_types`. `vehicle_types.json` is optional: if the download fails, it logs a warning and carries on without them. Station names, coordinates, e-bike types and the list the options flow offers come from here, so they only change when the entry restarts.
- **`station_name(station_id)`** returns a station's name in Home Assistant's language, through `localized_text`.
- **`_async_update_data()`** downloads `station_status.json` and keeps it, as published, in `raw_status`. It stores every field any station has in `published_fields`, and returns each record read through `StationStatus.from_feed`.
- **Interval.** It starts at 60 seconds (`DEFAULT_SCAN_INTERVAL`). After each update, if the response's top-level `ttl` is an integer, the interval becomes `max(60, ttl)`.
- **Errors.** A `GbfsError`, a missing key or a wrong type becomes `UpdateFailed`. During the first refresh, Home Assistant turns that into `ConfigEntryNotReady` and retries the setup with backoff. After that, a failed update marks every entity unavailable until an update works again.

## Entities

Sensors are declared as `GbfsSensorEntityDescription`s, which extend Home Assistant's `SensorEntityDescription` with:

| Field | Purpose |
|---|---|
| `value_fn(station)` | Computes the state from the station's `StationStatus` |
| `optional` | Create the sensor only if `value_fn` gives a value for at least one station of the feed |
| `has_location` | Adds `latitude` and `longitude` from `station_info`. Only Bikes available sets it, so the map shows one marker per station |

Binary sensors use `GbfsBinarySensorEntityDescription`, whose `value_fn` reads `is_renting` or `is_returning`.

The platforms create one entity per selected station and description, and skip optional descriptions that no station reports. They run after the first refresh, so this reflects the first `station_status.json`. A field that appears later needs an entry reload.

`GbfsEntity` sets:

| | Value |
|---|---|
| Unique ID | `<entry_id>_<station_id>_<description key>` |
| Device identifier | `("gbfs", "<entry_id>_<station_id>")`, from `station_identifier()` |
| Device name | `station_name()`, or `Station <station_id>` |
| Entity name | From the translation key, after the device name (`has_entity_name`) |
| Available | The last update worked and included the station |

The entry ID prefix keeps two systems that reuse a station ID apart.

## The config entry

| | Value |
|---|---|
| Unique ID | The feed URL, with its scheme and host in lowercase and any trailing `/` removed, so the same feed can't be added twice |
| `data` | `{"url": <the feed URL as entered>}` |
| `options` | `{"stations": [<station IDs>]}` |
| Version | 1 |

The options flow only edits `options.stations`. An update listener reloads the entry when the options change, which recreates the entities for the new selection. The devices and entities of unselected stations stay in Home Assistant's registries, unavailable, so adding a station back restores them.

## Device removal

`async_remove_config_entry_device` in `__init__.py` lets users delete a station's device from its page. It returns `True`, and Home Assistant deletes the device with its entities, only if none of the device's identifiers belongs to a station the entry still has selected. A selected station's device would come back at the next reload, so for those it returns `False`, and Home Assistant reports that the integration rejected the removal.

## Diagnostics

`async_get_config_entry_diagnostics` returns the entry's data and options, the update interval, whether the last update worked, `published_fields`, the e-bike vehicle types, `station_info`, and `raw_status`, the station records as published. Nothing is redacted: the only configuration is a public URL.

## Design choices

- **One request per update.** `station_status.json` holds every station in the system, so the integration downloads it once per entry, however many stations you pick.
- **Static data at start.** Station names, coordinates and vehicle types rarely change, so their files are only read when the entry starts.
- **A 60-second floor.** Many feeds have a `ttl` of 10 seconds or less, and following it would mean several downloads a minute for little benefit. A longer `ttl` is respected.
- **One model for every version.** Version differences are handled where the feed is read, so entities, statistics and entity IDs are the same whatever version a system publishes, including when it upgrades.
- **Feed-aware entities.** Sensors for optional fields are only created when the feed has them, rather than sitting at unknown forever.
- **Operator e-bike counts first.** When a feed publishes `num_ebikes_available`, it's used instead of the counts by vehicle type. Some operators that publish both, such as Citi Bike, include disabled bikes in their counts by type at some stations.
- **A device per station, scoped to its entry.** It matches how people think about stations, and keeps separate systems apart.
