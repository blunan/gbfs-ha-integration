# Troubleshooting

## Download diagnostics { #diagnostics }

Go to **Settings → Devices & services → GBFS** and, on the entry, select **⋮ → Download diagnostics**. You get a JSON file with:

| Key | Contents |
|---|---|
| `entry.data` | The feed URL |
| `entry.options` | The IDs of the stations you picked |
| `update_interval_seconds` | The current time between updates: 60, or the feed's `ttl` if that's longer |
| `last_update_success` | Whether the latest update worked |
| `published_fields` | Every field seen in the latest `station_status.json`, across all stations |
| `ebike_vehicle_types` | The vehicle types counted as e-bikes, if the feed has `vehicle_types.json` |
| `station_info` | The `station_information.json` record of every station in the system |
| `station_status` | The latest `station_status.json` record of every station in the system |

The file covers every station in the system, not only yours, so it can be large for big systems. It holds nothing private, since the feed is public. Attach it when you [report a problem](#report-a-problem).

## Debug logs { #debug-logs }

To log what the integration does in detail:

1. Go to **Settings → Devices & services → GBFS** and select **⋮ → Enable debug logging**.
2. Reproduce the problem. For update problems, wait a few minutes to cover several updates.
3. Select **⋮ → Disable debug logging**. Your browser downloads the log.

To keep debug logging on across restarts, add this to `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.gbfs: debug
```

With debug logging, each update logs a line like `Finished fetching gbfs data in 0.214 seconds (success: True)`. When the feed's `ttl` changes the update interval, you'll see `Adjusting poll interval to 0:05:00 due to feed ttl`.

## Errors when adding the integration

**Failed to connect to the feed**, **The URL does not point to a valid GBFS feed** and **This GBFS feed is already configured** are explained in [Configuration](configuration.md#setup-errors).

## The entry keeps retrying setup

When the entry starts, the integration downloads `gbfs.json`, `station_information.json` and `station_status.json`. If any of these fails, Home Assistant shows the error on the entry and retries the setup in the background, waiting longer each time. The entry sets itself up once the feed answers again; you don't need to do anything. If it never does, open the feed URL in a browser and check the [debug logs](#debug-logs).

## All entities are unavailable

The latest update failed, for example because the operator's server is down or answered with an error page. The integration tries again at the next update, and the entities come back on their own. The log shows `Error fetching gbfs data` when updates start failing, and `Fetching gbfs data recovered` once they work again.

## One station's entities are unavailable

The station is missing from the latest `station_status.json`. Operators remove stations that are closed, being moved or under maintenance. Check the operator's app; the entities come back with the station. If it's gone for good, remove it with [Configure](configuration.md#change-stations).

## A sensor is unknown

- **Occupancy** is unknown when the station has neither bikes nor free docks, or the feed leaves out one of the two counts. See [Occupancy](entities.md#occupancy).
- **Docks available** is unknown for stations that don't report docks, such as stations with unlimited docking capacity.
- **Last reported** is unknown if the feed's time has no time zone offset, which GBFS 3.0 requires.

## A sensor is missing

Bikes disabled and Docks disabled are only created when the feed publishes their fields, and E-bikes available when the feed counts e-bikes; see [E-bikes](feeds.md#e-bikes). Check `published_fields` and `ebike_vehicle_types` in the [diagnostics](#diagnostics).

- If the log shows `Not counting e-bikes by vehicle type`, the integration couldn't download `vehicle_types.json` when the entry started. Reload the entry with **⋮ → Reload** to try again.
- If the operator started publishing a field after you set up the integration, reload the entry too.

## A station is missing from Configure, or names are out of date

The integration loads the station list, names and coordinates when the entry starts. Reload the entry with **⋮ → Reload**, then open **Configure** again.

## A station isn't on the map

Only the **Bikes available** sensor has coordinates, so add that entity to the map card. If the feed has no coordinates for the station, it can't have a marker.

## The values look old

Check the station's **Last reported** time. If it's old, the operator's data is stale, and the integration can't do better. Otherwise, remember that the integration updates every 60 seconds, or at the feed's `ttl`, while the operator's app may update more often.

## A removed station's device is still listed

Home Assistant keeps the device of a station you removed with **Configure**, in case you add it back. To delete it, open the device and select **⋮ → Delete**; its entities go with it.

If deleting fails, the station is still selected, and its device would come back at the next reload. Remove the station with [Configure](configuration.md#change-stations) first.

## Report a problem { #report-a-problem }

[Open an issue](https://github.com/blunan/gbfs-ha-integration/issues) on GitHub with:

- Your Home Assistant version, shown under **Settings → About**, and the GBFS version, shown in the Marketplace or HACS.
- The feed URL.
- The [diagnostics](#diagnostics) file, and the [debug log](#debug-logs) if the problem is about updates.
- What you expected, and what happened instead.
