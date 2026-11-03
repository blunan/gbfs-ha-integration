# GBFS for Home Assistant

Live bike, e-bike and dock availability in Home Assistant for the stations you use, from **any** bike-share system that publishes a [GBFS](https://gbfs.org/) feed: Ecobici in Mexico City, Citi Bike, Vélib', Divvy and hundreds more.

Paste the system's `gbfs.json` URL, pick your stations by name, and each station becomes a device with its own sensors. You don't need YAML or an API key.

[Install it](installation.md){ .md-button .md-button--primary }
[Find your system's feed](configuration.md#find-your-feed){ .md-button }

## What you get

- **Setup from the UI.** Paste the feed URL and choose stations from a list sorted by name. Change them later with **Configure**, without removing anything.
- **A device per station**, with sensors for available bikes and e-bikes, free docks, out-of-service bikes and docks, occupancy and the station's last report. Binary sensors show whether the station rents bikes and accepts returns.
- **Any GBFS version.** 1.x, 2.x and 3.0 feeds give the same sensors, with station names in your language when the feed translates them.
- **Only the sensors your feed can fill.** Optional sensors are created only when the feed publishes their fields. E-bikes are counted directly or by vehicle type.
- **One request per update.** A single download of `station_status.json` every 60 seconds, or at the feed's `ttl` if that's longer, refreshes every station you picked.
- **History and maps.** Counts and occupancy keep long-term statistics, and each station's bikes sensor carries its coordinates for the map card.
- **Diagnostics** to download for bug reports, and the UI in English and Spanish.

## How it maps

```text
Ecobici (one GBFS feed)               → one integration entry
├── CE-003 Reforma - Insurgentes      → one device
│   ├── Bikes available               → sensor
│   ├── Docks available               → sensor
│   ├── Occupancy                     → sensor
│   ├── …
│   ├── Renting                       → binary sensor
│   └── Returning                     → binary sensor
└── CE-029 Reforma - Bucareli         → one device
    └── …
```

[Entities](entities.md) describes every sensor.

## What you need

- Home Assistant 2026.3 or later.
- The `gbfs.json` URL of a **station-based** bike-share system with a **public** feed. [Configuration](configuration.md#find-your-feed) shows where to find it.
- Internet access from Home Assistant to the operator's server.

## What isn't supported

- **Dockless systems**, which publish free-floating vehicles and no stations.
- **Feeds behind authentication**: API keys, logins or custom headers.

See [Supported feeds](feeds.md) for details.

## License

MIT, see [LICENSE](https://github.com/blunan/gbfs-ha-integration/blob/main/LICENSE). Not affiliated with or endorsed by MobilityData, the Home Assistant project or any bike-share operator.
