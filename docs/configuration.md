# Configuration

## Find Your System's Feed { #find-your-feed }

Every GBFS feed publishes an auto-discovery file named `gbfs.json` that lists all related endpoints. This single URL is all the integration needs to discover and configure your stations.

The integration supports **GBFS 1.x, 2.x, and 3.0** feeds automatically. Feeds must be **public** (no API keys, tokens, or logins) and **station-based** (dockless-only systems without physical stations are not supported).

To find your system's auto-discovery URL:

- **MobilityData's [systems.csv](https://github.com/MobilityData/gbfs/blob/master/systems.csv):** Official catalog of worldwide feeds. Look up your city and copy the value from the **Auto-Discovery URL** column. If **Authentication Type** is populated, the feed requires credentials and cannot be used.
- **[The Mobility Database](https://mobilitydatabase.org/feeds):** Searchable transit and micro-mobility catalog.
- **City or operator open-data portals:** Check developer pages for local transit authorities.

### Example Feeds

| System | City | Version | Feed URL (`gbfs.json`) |
|---|---|---|---|
| Ecobici | Mexico City | 1.0 | `https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json` |
| Citi Bike | New York | 2.3 | `https://gbfs.citibikenyc.com/gbfs/2.3/gbfs.json` |
| Divvy | Chicago | 2.3 | `https://gbfs.divvybikes.com/gbfs/2.3/gbfs.json` |
| Vélib' Métropole | Paris | 1.0 | `https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/gbfs.json` |
| Ecobici | Buenos Aires | 3.0 | `https://buenosaires.publicbikesystem.net/customer/gbfs/v3.0/gbfs.json` |

## Add the Integration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=gbfs){ .md-button .md-button--primary }

Or navigate to **Settings → Devices & services**, select **Add integration**, and search for **GBFS**.

### Step 1: Feed URL

Enter your system's `gbfs.json` URL and select **Submit**.

The integration downloads the discovery file, locates the station information and status feeds, and fetches the system name. If the feed publishes multiple language options, the integration automatically matches your Home Assistant language.

#### Setup Errors { #setup-errors }

If initial validation fails, the dialog displays one of the following errors:

| Error | Cause | Resolution |
|---|---|---|
| **Failed to connect to the feed** | The server timed out (30 s) or returned an HTTP error (e.g., 404, 503). | Check the URL for typos, verify it opens in a browser, and ensure Home Assistant has internet access. |
| **The URL does not point to a valid GBFS feed** | The response is not valid JSON, lacks required `station_information` or `station_status` endpoints, or reports zero stations. | Ensure you entered the root `gbfs.json` discovery URL (not a sub-feed like `station_status.json`) and that the system has physical docking stations. |
| **This GBFS feed is already configured** | A config entry for this feed URL already exists. | Use **Configure** on the existing integration entry to select additional stations. |

### Step 2: Station Selection

Select one or more stations from the alphabetized multi-select list and click **Submit**.

!!! tip "Large systems"
    Major systems have hundreds or thousands of stations. Search by station name or code (e.g., *CE-003 Reforma - Insurgentes*) as shown in the operator's app.

## What Gets Created

Once configured, the integration creates:

- **One config entry** for the bike-share system, titled with the operator's system name.
- **One device per station selected**, named after the station.
- **Live entities per station:** Sensors for available bikes, e-bikes (if supported), free docks, occupancy percentage, and last report time, alongside renting and returning binary sensors.

Initial data updates immediately upon completion.

## Managing Stations { #change-stations }

You can modify your tracked stations at any time without reinstalling:

1. Go to **Settings → Devices & services → GBFS**.
2. Select **Configure** on the integration entry.
3. Check or uncheck stations in the list, then select **Submit**.

When options are saved:

- **Added stations** immediately create their device and entities.
- **Removed stations** stop updating and are marked unavailable. Their entity IDs and historical statistics are preserved in case you re-add them later.
- **Deleting removed devices permanently:** Open the removed station's device page and select **⋮ → Delete**. (Only unselected stations can be deleted; active stations will be restored on entry reload).

## Multiple Systems

To track stations across different cities or networks, add the GBFS integration again with each system's `gbfs.json` URL. Each system creates an independent integration entry with its own devices and polling cycle.

## Updating Station Metadata

Station names, coordinates, and optional feature detection (such as e-bike counts) are loaded when the integration entry starts. If the operator renames or relocates stations, or starts publishing new fields, reload the entry via **⋮ → Reload** on the integration card.
