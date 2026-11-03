# Supported feeds

[GBFS](https://gbfs.org/), the General Bikeshare Feed Specification, is the open standard that bike-share systems use to publish real-time data. [MobilityData](https://mobilitydata.org/) maintains it. A system's feed is a set of JSON files, listed in an auto-discovery file called `gbfs.json`.

## What a feed needs

- A public `gbfs.json` URL that works without API keys, logins or custom headers.
- `station_information` and `station_status` among the files it lists.
- At least one station in `station_information.json`.

`system_information` is optional: the integration only uses it to title the entry. `vehicle_types` is optional too; it lets the integration count e-bikes, see [E-bikes](#e-bikes). The server can label the files as JSON or as plain text; both work, and Ecobici's server uses plain text.

## GBFS versions

The integration reads GBFS 1.x, 2.x and 3.0 feeds. It doesn't need to be told the version: it reads each field in whatever form the feed uses, and your sensors look the same either way.

| | 1.x and 2.x | 3.0 |
|---|---|---|
| Files in `gbfs.json` | Listed once per language | Listed once |
| Names | Text | A list of translations |
| Times | Seconds since 1970 | Date and time text (RFC 3339) |
| Available and disabled bikes | `num_bikes_available`, `num_bikes_disabled` | `num_vehicles_available`, `num_vehicles_disabled` |
| Renting and returning flags | `1` and `0` (1.x), `true` and `false` (2.x) | `true` and `false` |
| E-bikes | `num_ebikes_available` (not in the spec), or counts by vehicle type (2.1+) | Counts by vehicle type |

## Languages { #languages }

GBFS 1.x and 2.x list a feed's files once per language, such as `en` and `es` for Ecobici. GBFS 3.0 lists them once and translates each name instead. Either way, the integration picks the language that matches Home Assistant's, comparing only the main part of the code, so `es-MX` matches `es`. If none matches, it uses the first language listed. This decides the station and system names you see.

## Fields the integration reads

| File | Fields |
|---|---|
| `gbfs.json` | The `name` and `url` of each listed feed |
| `system_information.json` | `name` |
| `station_information.json` | `station_id`, `name`, `lat` and `lon` of each station |
| `station_status.json` | The top-level `ttl`, and for each station: `station_id`, `num_bikes_available` or `num_vehicles_available`, `num_bikes_disabled` or `num_vehicles_disabled`, `num_docks_available`, `num_docks_disabled`, `num_ebikes_available`, `vehicle_types_available`, `is_renting`, `is_returning` and `last_reported` |
| `vehicle_types.json` | `vehicle_type_id`, `form_factor` and `propulsion_type` of each vehicle type |

Other fields are ignored, though [diagnostics](troubleshooting.md#diagnostics) include each station's full records. Other files a system may publish, such as `free_bike_status.json`, `vehicle_status.json` or `system_alerts.json`, aren't downloaded.

## E-bikes { #e-bikes }

The E-bikes available sensor counts the electric bikes ready to rent at a station. It takes the count from:

1. **`num_ebikes_available`**, if the station has it. The field isn't part of the GBFS specification, but some operators add it, Citi Bike and Divvy among them.
2. **Counts by vehicle type** otherwise: the station's `vehicle_types_available` (GBFS 2.1 and later), adding up the types that `vehicle_types.json` describes as electric bicycles. That's a `form_factor` of `bicycle` or `cargo_bicycle`, with `electric_assist` or `electric` propulsion. Electric scooters, mopeds and cars don't count.

If the feed has neither, there's no E-bikes available sensor. The integration downloads `vehicle_types.json` when the entry starts. If that fails, it logs a warning and carries on without counting by type until the entry reloads.

## Not supported

- **Dockless systems:** free-floating bikes and scooters published in `free_bike_status.json` (`vehicle_status.json` in 3.0), with no stations.
- **Authentication:** feeds that need an API key, a token or custom HTTP headers. systems.csv marks these in its **Authentication Type** column.
- **Other GBFS data:** system alerts, pricing plans, geofencing zones, and counts of vehicles other than e-bikes, such as scooters, at a station.

## Load on the operator's server

Each entry downloads `station_status.json` at most once a minute, or less often if the feed's `ttl` asks for it. Each time the entry starts, it downloads `gbfs.json`, `station_information.json` and, if the feed has it, `vehicle_types.json`. Feeds are public, but each operator sets its own terms of use; check them if you're unsure.
