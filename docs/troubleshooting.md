# Troubleshooting

Diagnostic steps and solutions for common questions and issues.

## Diagnostics { #diagnostics }

Download integration diagnostic data for debugging or bug reports:

1. Go to **Settings → Devices & services → GBFS**.
2. Select **⋮ → Download diagnostics** on the integration card.

The downloaded JSON file contains:

- Config entry data and selected station IDs.
- Current polling interval and last update success state.
- Set of all field names published in the latest `station_status.json`.
- List of vehicle type IDs identified as e-bikes.
- Raw station metadata (`station_info`) and live status records (`station_status`).

Feed data is public, so diagnostic dumps contain no credentials or private information.

## Debug Logs { #debug-logs }

To enable live debug logging via the UI:

1. Go to **Settings → Devices & services → GBFS**.
2. Select **⋮ → Enable debug logging**.
3. Allow a few minutes for polling cycles to run, then select **⋮ → Disable debug logging** to download the log file.

To enable persistent debug logging across Home Assistant restarts, add this to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.gbfs: debug
```

When enabled, logs record network response times (`Finished fetching gbfs data in 0.214 seconds`), TTL-based interval changes, and any HTTP or JSON parsing errors.

## Setup Errors { #setup-errors }

| Error Message | Cause | What to Check |
|---|---|---|
| **Failed to connect to the feed** | The server timed out (30 s limit) or returned an HTTP error (404, 500, 503). | Open the feed URL in a browser. Verify Home Assistant has internet access. If the operator's server is down, retry later. |
| **The URL does not point to a valid GBFS feed** | URL returned non-JSON data, is missing `station_information` or `station_status`, or has zero stations. | Ensure you entered the root `gbfs.json` URL (not a sub-feed like `station_status.json`). Verify the system has physical docking stations. |
| **This GBFS feed is already configured** | A config entry for this feed already exists. | Use **Configure** on the existing entry to select additional stations. |

## Startup Retries

If the initial connection to `gbfs.json` or `station_information.json` fails during startup, Home Assistant retries connection with exponential backoff. The entry initializes automatically once the feed responds.

## All Entities Are Unavailable

Occurs when recent polling requests fail (server outage, network interruption, or HTTP errors):

- The integration continues polling at the normal interval and restores entities automatically once the feed responds.
- Check debug logs for `Error fetching gbfs data`. When connection recovers, the log records `Fetching gbfs data recovered`.

## One Station Is Unavailable

The operator omitted this station from `station_status.json`, typically due to maintenance, seasonal closure, or relocation:

- The entities restore automatically once the operator includes the station in updates again.
- If the station was permanently decommissioned, remove it via **Configure** on the integration entry.

## Sensor Displays Unknown State

- **Occupancy:** Displays `unknown` when a station reports zero total capacity (0 available bikes and 0 docks, such as closed stations), or when the feed does not report dock counts.
- **Docks available:** Displays `unknown` if the operator does not report dock capacity (e.g., valet stations or virtual docks).
- **Last reported:** Displays `unknown` if a GBFS 3.0 timestamp lacks a required timezone offset.

## Sensor Is Missing

- **E-bikes available:** Only created if the feed reports `num_ebikes_available` or defines e-bike types in `vehicle_types.json`.
- **Disabled counts:** `bikes_disabled` and `docks_disabled` are created only if the operator publishes those fields.
- **Operator updates:** If an operator recently added new fields, reload the integration via **⋮ → Reload** to discover them.

## Stations Missing from Selection or Renamed

Station names, locations, and the selectable station list are loaded once when the integration initializes. If the operator renames or adds stations, reload the integration via **⋮ → Reload** to update metadata.

## Station Missing on Map Card

Ensure you added the station's **Bikes available** (`_bikes_available`) entity to the map card. Coordinates are attached exclusively to this sensor so each station produces a single marker.

## Stale or Delayed Values

Station sensor values reflect data published by the operator. If the **Last reported** timestamp is old, the operator backend is not updating. The integration checks for updates every 60 seconds (or the feed's TTL).

## Removed Station Device Still Visible

When a station is unselected in **Configure**, Home Assistant retains its device in an unavailable state to preserve history and automations:

1. Ensure the station is unchecked in **Configure** on the integration card.
2. Open the station's device page and select **⋮ → Delete**.

## Reporting Issues { #report-a-problem }

If you encounter an issue not resolved above, [open an issue on GitHub](https://github.com/blunan/gbfs-ha-integration/issues) with:

1. Home Assistant version and integration version.
2. The `gbfs.json` feed URL.
3. The downloaded [Diagnostics](#diagnostics) file.
4. Relevant excerpts from the [Debug logs](#debug-logs).
5. Description of expected versus observed behavior.
