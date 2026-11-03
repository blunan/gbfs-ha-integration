# Entities

Each selected bike-share station becomes a device in Home Assistant equipped with availability sensors and status flags.

## Station Device

| Attribute | Value |
|---|---|
| **Name** | Station name from `station_information.json` (localized to Home Assistant's language if available), or `Station <ID>` |
| **Manufacturer** | GBFS |
| **Model** | Bike share station |

## Sensors

| Entity | Entity ID Suffix | Type | Published Field | Description & Behavior |
|---|---|---|---|---|
| **Bikes available** | `_bikes_available` | Count | `num_bikes_available` (3.0: `num_vehicles_available`) | Total rentable bikes at the station. Carries station `latitude` and `longitude` attributes for map cards. |
| **E-bikes available** | `_e_bikes_available` | Count | `num_ebikes_available` or `vehicle_types_available` | Rentable electric bikes. Created only if the feed reports direct e-bike counts or defines electric bicycle vehicle types. |
| **Bikes disabled** | `_bikes_disabled` | Count | `num_bikes_disabled` (3.0: `num_vehicles_disabled`) | Bikes at the station needing repair or unavailable for rent. Created only if published by the feed. |
| **Docks available** | `_docks_available` | Count | `num_docks_available` | Empty, functioning docks ready for bike returns. |
| **Docks disabled** | `_docks_disabled` | Count | `num_docks_disabled` | Out-of-service docks. Created only if published by the feed. |
| **Occupancy** | `_occupancy` | Percentage | Calculated | Station fullness percentage: `bikes / (bikes + docks) * 100`. |
| **Last reported** | `_last_reported` | Timestamp | `last_reported` | Diagnostic timestamp showing when the station last reported to the operator. |

## Binary Sensors

| Entity | Entity ID Suffix | Condition When On | GBFS Field |
|---|---|---|---|
| **Renting** | `_renting` | Station is actively renting bikes | `is_renting` |
| **Returning** | `_returning` | Station is actively accepting bike returns | `is_returning` |

Both binary sensors handle 1.x integer flags (`0`/`1`) and 2.x/3.0 boolean values (`true`/`false`). An operator may permit returns while disabling rentals (e.g., during maintenance or rebalancing).

## Occupancy Calculation { #occupancy }

Occupancy indicates how full a station is, rounded to one decimal place:

```text
Occupancy = Bikes available / (Bikes available + Docks available) × 100
```

- **0%**: No bikes available to rent.
- **100%**: No free docks available for returns.
- **Unknown state**: Set to `unknown` if a station has zero total capacity (e.g., closed stations reporting 0 bikes and 0 docks), or if the feed omits dock counts (such as valet stations or floating zones). Out-of-service bikes and docks are excluded from the calculation.

## Diagnostic Timestamp: Last Reported { #last-reported }

The **Last reported** sensor displays the timestamp of the station's last communication with the bike-share operator. If a station loses network connectivity, its counts may become stale while the operator continues serving the last known data.

- **Timestamp formats:** Automatically parses POSIX epoch timestamps (GBFS 1.x/2.x) and RFC 3339 datetime strings (GBFS 3.0).
- **Timezone requirement:** GBFS 3.0 timestamps without a timezone offset are ambiguous and display as `unknown`.
- **Diagnostic category:** Categorized as a diagnostic entity, keeping auto-generated dashboards clean.

## Map Location Attributes { #location }

The **Bikes available** sensor includes `latitude` and `longitude` attributes populated from `station_information.json`. Adding this entity to a Home Assistant Map card places a marker at the station's physical coordinates displaying its current bike count.

Other station entities omit coordinates so each station generates a single marker on map cards.

## Long-Term Statistics & History

All count sensors and the occupancy sensor use `state_class: measurement`. Home Assistant automatically records long-term hourly statistics (mean, minimum, maximum), which persist after raw state history is purged. These sensors integrate seamlessly with Statistics Graph cards and database exports like InfluxDB.

## Entity State Behavior

| Entity State | Cause |
|---|---|
| **Numeric or On/Off** | Feed update succeeded and included status for the station. |
| **Unknown** | Station is present in update, but field is omitted or cannot be computed (e.g., occupancy with 0 total capacity). |
| **Unavailable** *(single station)* | Station is omitted from the operator's latest `station_status.json` (e.g., undergoing station maintenance or temporary closure). |
| **Unavailable** *(all stations)* | Polling request failed (network timeout, HTTP error, or malformed JSON). Entities restore automatically on the next successful update. |

## Polling Interval & Data Freshness

The integration polls `station_status.json` every **60 seconds**, or at the feed's specified `ttl` (cache duration) if greater than 60 seconds. A single request updates all configured stations for that feed simultaneously.

## Names and Entity IDs { #names-and-entity-ids }

- **Display Names:** Combine the station name and entity name (e.g., *CE-003 Reforma - Insurgentes Bikes available*). Station names match your Home Assistant language when the feed publishes translations; otherwise, the operator's default name is used.
- **Entity IDs:** Generated upon initial discovery from the station and entity names (e.g., `sensor.ce_003_reforma_insurgentes_bikes_available`). Once created, entity IDs remain stable even if station names are updated later.
- **Finding Entities:** View all entities for a station on its device page under **Settings → Devices & services → Entities**.
