# Entities

Each station you pick becomes a device with up to seven sensors and two binary sensors.

## The station device

| | |
|---|---|
| **Name** | The station's name in the feed (`station_information.json`), in your Home Assistant language if the feed translates it, or "Station" and its ID if the feed gives no name |
| **Manufacturer** | GBFS |
| **Model** | Bike share station |

## Sensors

| Entity | Entity ID ends in | Value | From the feed | Created |
|---|---|---|---|---|
| Bikes available | `_bikes_available` | Count | `num_bikes_available` (3.0: `num_vehicles_available`) | Always |
| E-bikes available | `_e_bikes_available` | Count | `num_ebikes_available`, or counts by vehicle type | If the feed counts e-bikes |
| Bikes disabled | `_bikes_disabled` | Count | `num_bikes_disabled` (3.0: `num_vehicles_disabled`) | If the feed publishes it |
| Docks available | `_docks_available` | Count | `num_docks_available` | Always |
| Docks disabled | `_docks_disabled` | Count | `num_docks_disabled` | If the feed publishes it |
| Occupancy | `_occupancy` | % | Calculated | Always |
| Last reported | `_last_reported` | Timestamp | `last_reported` | Always |

- **Bikes available:** bikes ready to rent. The feed counts every vehicle the station offers, so in systems that also dock scooters, those count too. It also carries the station's coordinates; see [Location](#location).
- **E-bikes available:** electric bikes ready to rent. Some operators publish this count directly; for others, the integration adds up the electric bicycle types in the feed's counts by vehicle type. Citi Bike and Buenos Aires' Ecobici have it, Mexico City's Ecobici doesn't. See [E-bikes](feeds.md#e-bikes).
- **Bikes disabled:** bikes at the station that can't be rented, for example because they need repairs.
- **Docks available:** empty, working docks where you can return a bike.
- **Docks disabled:** docks that are out of service.
- **Occupancy:** how full the station is; see [Occupancy](#occupancy).
- **Last reported:** when the station last reported to the operator; see [Last reported](#last-reported).

The entity ID endings are for Home Assistant in English. [Names and entity IDs](#names-and-entity-ids) explains how IDs are made.

## Binary sensors

| Entity | Entity ID ends in | On when | From the feed |
|---|---|---|---|
| Renting | `_renting` | The station rents out bikes | `is_renting` |
| Returning | `_returning` | The station accepts returns | `is_returning` |

Both are always created. GBFS 1.x publishes these flags as `1` and `0`, and later versions as `true` and `false`; both work. They can differ: an operator can stop rentals at a station while it still accepts returns.

## Occupancy { #occupancy }

```text
Occupancy = Bikes available / (Bikes available + Docks available) × 100
```

The result is rounded to one decimal.

- **0 %** means there are no bikes to rent.
- **100 %** means there's no free dock to return a bike to.

Out-of-service bikes and docks don't count. Occupancy is **unknown** when the station has neither bikes nor free docks (both are zero, for example while it's closed), or when the feed leaves out either count. The specification lets stations with unlimited docking capacity, such as valet stations, leave out `num_docks_available`.

## Last reported { #last-reported }

The time the station last sent its status to the operator, shown as a relative time such as "3 minutes ago". A station that stops reporting keeps showing its last counts, so this time tells you whether they're stale. [An example](examples.md#stale-station) warns you when that happens.

GBFS 1.x and 2.x publish this time as seconds since 1970, and 3.0 as date and time text; both work. A 3.0 time without a time zone offset is ambiguous, so the sensor shows it as unknown.

It's a **diagnostic** entity: it appears under **Diagnostic** on the device page, and Home Assistant leaves it out of auto-generated dashboards.

## Location { #location }

**Bikes available** has `latitude` and `longitude` attributes with the station's position from `station_information.json`, so the [map card](examples.md#map) can place it. The other entities don't have them, so the map shows one marker per station.

## Statistics and history

All counts and occupancy have the `measurement` state class, so Home Assistant keeps long-term statistics for them: hourly mean, minimum and maximum, kept after the recorder purges detailed history. Statistics graph cards use them, and export integrations such as InfluxDB pick these sensors up like any other.

Counts have no unit of measurement, and occupancy is in %.

## Unknown and unavailable

| State | When |
|---|---|
| A value | The latest update includes the station and the field. |
| **Unknown** | The station is in the latest update, but the field is missing or the value can't be calculated, as with [Occupancy](#occupancy). |
| **Unavailable**, one station | The station is missing from the latest `station_status.json`. Operators drop stations that are closed, being moved or under maintenance. |
| **Unavailable**, every station of the entry | The latest update failed: the server didn't answer, or didn't answer with valid station status. The integration tries again at the next update. |

## Updates

The integration downloads `station_status.json` every 60 seconds. If the file's `ttl`, the time the operator says the data stays fresh, is longer than that, it waits for the `ttl` instead. Many feeds have a shorter `ttl`, such as Ecobici's 10 seconds, and then the integration stays at 60 seconds.

One download covers every station you picked from that system, however many there are. The data is only as fresh as the operator's feed: check each station's [Last reported](#last-reported) time.

## Names and entity IDs { #names-and-entity-ids }

- **Names** combine the station's name and the entity's name, as in *CE-003 Reforma - Insurgentes Bikes available*. Entity names are translated into English and Spanish. Station names come from the feed, in your Home Assistant language when the feed translates them; see [Languages](feeds.md#languages).
- **Entity IDs** are made once, when an entity first appears, from the same two names in your Home Assistant language. With Home Assistant in English, Ecobici's *CE-003 Reforma - Insurgentes* station gets `sensor.ce_003_reforma_insurgentes_bikes_available`, `binary_sensor.ce_003_reforma_insurgentes_renting` and so on. In other languages, the endings may be translated too.
- Renaming a station later, in Home Assistant or at the operator, doesn't change existing entity IDs.

To find your entity IDs, open the station's device page or search for the station under **Settings → Devices & services → Entities**.
