# GBFS for Home Assistant

Live bike, e-bike, and dock availability in Home Assistant for the stations you use, from any bike-share system publishing an open [GBFS](https://gbfs.org/) feed — including Ecobici, Citi Bike, Vélib', Divvy, and hundreds more worldwide.

Paste your system's `gbfs.json` URL and choose your stations. Each station becomes a Home Assistant device with live availability sensors, map coordinates, and long-term statistics.

[Installation](installation.md){ .md-button .md-button--primary }
[Configuration](configuration.md){ .md-button }

## Highlights

- **UI setup:** Enter the feed URL and choose stations from a multi-select list. Add or remove stations later at any time.
- **Universal GBFS support:** Seamlessly handles GBFS 1.x, 2.x, and 3.0 feeds, including localized station names.
- **Feed-aware entities:** Automatically adapts to what each system publishes (standard bikes, e-bikes, free docks, out-of-service equipment).
- **Efficient polling:** A single request to `station_status.json` every 60 seconds (or the feed's `ttl`) updates all configured stations at once.
- **Ready for dashboards and maps:** Station coordinates attach to the bikes sensor for map cards, and numeric sensors support long-term statistics.
- **Built-in diagnostics:** Export integration state and raw station records directly from the UI for easy troubleshooting.

## How it maps

```text
GBFS Feed (e.g., Ecobici)             → Integration entry
├── Station 1 (CE-003 Reforma)         → Device
│   ├── Bikes available                → Sensor (with coordinates)
│   ├── E-bikes available              → Sensor (if supported)
│   ├── Docks available                → Sensor
│   ├── Occupancy                      → Sensor (%)
│   ├── Last reported                  → Sensor (diagnostic timestamp)
│   ├── Renting                        → Binary sensor
│   └── Returning                      → Binary sensor
└── Station 2 (CE-029 Bucareli)        → Device
    └── …
```

## Requirements & Scope

- **Home Assistant:** Version 2026.3 or newer.
- **Feed requirements:** Publicly accessible `gbfs.json` URL for a station-based bike-share system (no login, API key, or custom headers required).
- **Not supported:** Dockless-only systems that publish free-floating vehicles without stations (`free_bike_status.json` only), and feeds requiring authentication.

## Documentation Overview

| Guide | Description |
|---|---|
| [Installation](installation.md) | Install via Marketplace, HACS, or manual file copy |
| [Configuration](configuration.md) | Find feed URLs, add the integration, and manage stations |
| [Entities](entities.md) | Sensor definitions, occupancy formulas, and status states |
| [Dashboards and Automations](examples.md) | Map cards, gauge displays, and commute alert automations |
| [Supported Feeds](feeds.md) | Technical reference on GBFS specifications, fields, and versions |
| [Troubleshooting](troubleshooting.md) | Resolve setup errors, missing entities, and download diagnostics |
| [How It Works](architecture.md) | Technical architecture, feed parsing, and coordinator lifecycle |
| [Development & Contributing](development.md) | Local development setup, testing, code style, CI, and releases |

## License

MIT License. This project is independent and not affiliated with or endorsed by MobilityData, the Home Assistant project, or any bike-share operator.
