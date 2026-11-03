# Configuration

## Find your system's feed { #find-your-feed }

Every GBFS feed starts with an auto-discovery file, `gbfs.json`, that lists the system's other files. Its URL is all the integration needs. To find it:

- **MobilityData's [systems.csv](https://github.com/MobilityData/gbfs/blob/master/systems.csv)**, the official catalog of public GBFS feeds. Search for your city. The **Auto-Discovery URL** column has the URL, and **Supported Versions** lists the GBFS versions the system publishes. A value under **Authentication Type** means the feed needs credentials, which the integration doesn't support.
- **The [Mobility Database](https://mobilitydatabase.org/feeds)**, a searchable catalog of transit and GBFS feeds.
- **Your operator's or city's open-data page**, often under "developers" or "open data".

Some systems that work:

| System | City | GBFS | `gbfs.json` URL |
|---|---|---|---|
| Ecobici | Mexico City | 1.0 | `https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json` |
| Citi Bike | New York | 2.3 | `https://gbfs.citibikenyc.com/gbfs/2.3/gbfs.json` |
| Divvy | Chicago | 2.3 | `https://gbfs.divvybikes.com/gbfs/2.3/gbfs.json` |
| Vélib' Métropole | Paris | 1.0 | `https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/gbfs.json` |
| Ecobici | Buenos Aires | 3.0 | `https://buenosaires.publicbikesystem.net/customer/gbfs/v3.0/gbfs.json` |

Any GBFS version works; see [Supported feeds](feeds.md#gbfs-versions).

## Add the integration

[Add GBFS to Home Assistant](https://my.home-assistant.io/redirect/config_flow_start/?domain=gbfs){ .md-button .md-button--primary }

Or go to **Settings → Devices & services**, select **Add integration** and search for **GBFS**.

### Step 1: the feed URL

Paste the `gbfs.json` URL and select **Submit**. The integration then:

1. Downloads `gbfs.json` and looks up the `station_information` and `station_status` feeds in it.
2. Downloads `station_information.json` to list the system's stations.
3. Reads the system's name from `system_information.json` to title the entry. If the feed has no such file, the entry is named after the URL's host.

When a feed is published in several languages, the integration uses the one that matches your Home Assistant language, so `es-MX` matches `es`. If none matches, it uses the first language listed. For systems that translate station names, this decides the names you see.

#### Errors { #setup-errors }

If something goes wrong, the form shows one of these errors:

| Error | What it means | What to try |
|---|---|---|
| **Failed to connect to the feed** | The server didn't answer within 30 seconds, or answered with an HTTP error such as 404 or 503. | Check the URL for typos and open it in a browser. Make sure Home Assistant can reach the internet. If the operator's server is down, try again later. |
| **The URL does not point to a valid GBFS feed** | The response isn't JSON or isn't a `gbfs.json` file, the file doesn't list both `station_information` and `station_status`, or the system has no stations. | Use the `gbfs.json` URL, not the URL of another file such as `station_status.json`. Check that the system has stations: dockless-only systems aren't supported. |
| **This GBFS feed is already configured** | You already added this feed. Letter case in the scheme and host, and a trailing `/`, don't make it a different feed. | Use [Configure](#change-stations) on the existing entry to add stations. |

### Step 2: stations

Select one or more stations from the list, which is sorted by name, and select **Submit**. Each station becomes a device with its own entities.

!!! tip "Finding your station"
    Big systems have hundreds of stations: Ecobici has more than 600 and Citi Bike more than 2,000. Look up your station's exact name in the operator's app or map first. Many systems include a station code in the name, like Ecobici's *CE-003 Reforma - Insurgentes*.

## What gets created

- One **entry** per feed, titled with the system's name.
- One **device** per station you picked, named after the station.
- Up to nine **entities** per device, depending on what the feed publishes. See [Entities](entities.md).

Values arrive with the first update, right after setup.

## Change your stations { #change-stations }

1. Go to **Settings → Devices & services → GBFS**.
2. On the entry, select **Configure**.
3. Add or remove stations, then select **Submit**.

The entry reloads with the new selection:

- **Stations you add** get their device and entities right away.
- **Stations you remove** stop updating. Home Assistant keeps their device and entities, shown as unavailable, in case you add the station back. Adding it back restores them, with the same entity IDs and history.

To get rid of a removed station for good, open its device and select **⋮ → Delete**. Home Assistant deletes the device together with its entities. You can only delete the device of a station you've removed with **Configure**, because a station that's still selected would get its device back at the next reload.

The list in **Configure** comes from the station data loaded when the entry started. To see stations the operator added since then, reload the entry first with **⋮ → Reload**.

## Several systems

Add the integration once per feed, for example once for Ecobici and once for Citi Bike. Each entry has its own devices and polls its own feed. Stations from different systems never clash, even if they share an ID.

You can't add the same feed twice. To follow more stations from a system you already added, use [Configure](#change-stations).

## When the operator changes things

The integration reads station names and coordinates once, when the entry starts. It also decides which optional sensors to create from the first update. Reload the entry with **⋮ → Reload**, or restart Home Assistant, when:

- The operator renames, moves or adds stations.
- The feed starts publishing a field it didn't have before, such as e-bike counts.

Reloading keeps your entities and their history.

## Remove a system

On the entry, select **⋮ → Delete**. Home Assistant removes the entry with its devices and entities. To remove the integration itself, see [Uninstall](installation.md#uninstall).
