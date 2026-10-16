# GBFS – Bike-Share Integration for Home Assistant

[![Test](https://github.com/blunan/gbfs-home-assistant-integration/actions/workflows/test.yml/badge.svg)](https://github.com/blunan/gbfs-home-assistant-integration/actions/workflows/test.yml)
[![Validate](https://github.com/blunan/gbfs-home-assistant-integration/actions/workflows/validate.yml/badge.svg)](https://github.com/blunan/gbfs-home-assistant-integration/actions/workflows/validate.yml)
![Home Assistant](https://img.shields.io/badge/home%20assistant-2026.3%2B-41BDF5)
![Python](https://img.shields.io/badge/python-3.14-blue)
![GBFS](https://img.shields.io/badge/GBFS-1.x%20%7C%202.x%20%7C%203.0-green)
![HACS](https://img.shields.io/badge/HACS-custom-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Custom integration that monitors stations from **any** bike-share system publishing a [GBFS](https://gbfs.org/) feed — Ecobici CDMX, Citi Bike, Vélib', Divvy, and hundreds more. Paste the system's `gbfs.json` URL, pick your stations by name, and each one becomes a device with live sensors.

---

## ✨ Features

* 🖱️ **100% UI-based setup** — no YAML. Paste the `gbfs.json` URL and the integration auto-discovers the feeds (supports GBFS 1.x/2.x language-keyed feeds and GBFS 3.0).
* 🚲 **One device per station** with sensors for available bikes, e-bikes, docks, occupancy %, out-of-service bikes/docks, and last report time.
* 🧠 **Feed-aware entities** — optional sensors (e-bikes, disabled bikes/docks) are only created when the feed actually publishes those fields.
* 📡 **Efficient polling** — a single request to `station_status.json` every 60 s (or the feed's `ttl` if greater) feeds all stations.
* 📈 **Long-term statistics ready** — numeric sensors use `state_class: measurement`, so they work with HA statistics and InfluxDB/Grafana export.
* 🗺️ **Map friendly** — the bikes sensor carries the station's latitude/longitude, so stations show up on the map card.
* 🔁 **Options flow** — add or remove stations at any time without reinstalling.
* 🩺 **Diagnostics support** — download the entry's feed state, published fields, and per-station data from **Devices & Services** for easy debugging.
* 🌐 **Translations** — English and Spanish.

---

## 📦 Installation

### HACS (custom repository)

1. HACS → ⋮ → **Custom repositories**.
2. Add this repository URL with category **Integration**.
3. Install **GBFS** and restart Home Assistant.

### Manual

Copy `custom_components/gbfs/` into the `custom_components/` directory of your Home Assistant instance and restart.

---

## ⚙️ Configuration

1. **Settings → Devices & Services → Add Integration → GBFS**.
2. Paste the auto-discovery URL of your bike-share system, e.g. Ecobici CDMX:
   `https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json`
3. Select your stations by name from the multi-select list.
4. Done — each station appears as a device. Use **Configure** on the entry to add/remove stations later.

---

## 🚲 Entities per Station

| Entity | Type | GBFS source | Notes |
|--------|------|-------------|-------|
| Bikes available | Sensor | `num_bikes_available` | Carries `latitude`/`longitude` attributes for the map |
| E-bikes available | Sensor | `num_ebikes_available` | Only if the feed publishes it |
| Bikes disabled | Sensor | `num_bikes_disabled` | Only if the feed publishes it |
| Docks available | Sensor | `num_docks_available` | |
| Docks disabled | Sensor | `num_docks_disabled` | Only if the feed publishes it |
| Occupancy | Sensor | calculated | `bikes / (bikes + docks) × 100` |
| Last reported | Sensor | `last_reported` | Timestamp, diagnostic |
| Renting | Binary sensor | `is_renting` | Station is renting bikes |
| Returning | Binary sensor | `is_returning` | Station is accepting returns |

---

## 🐳 Develop in a Dev Container (Recommended)

The fastest way to get a zero-setup environment — no host-level Python or Home Assistant installs required.

**Prerequisites:** [Docker](https://www.docker.com/) and the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) VSCode extension.

1. Open the repo in VSCode.
2. When prompted, click **Reopen in Container** — or run `Dev Containers: Reopen in Container` from the command palette.
3. Wait for the container to build; dependencies install automatically via `scripts/setup`.
4. `scripts/develop` → Home Assistant starts at the forwarded `http://localhost:8123` with the integration loaded from the repo.

The container uses Python 3.14 (Debian trixie, matching current Home Assistant), forwards port 8123, and pre-installs the Python, Ruff, GitLens, and Claude Code VSCode extensions.

---

## 🧞 Available Scripts

| Script | Description |
|--------|-------------|
| `scripts/setup` | Installs development dependencies (`homeassistant`, `pytest-homeassistant-custom-component`, `ruff`). |
| `scripts/develop` | Runs a local Home Assistant with debug logging at `http://localhost:8123`. |
| `scripts/lint` | Lints and formats the code with Ruff. |
| `scripts/test` | Runs the test suite with pytest. |

---

## 🏗️ Project Structure

```
/
├─ .devcontainer/              # Dev container definition (Python 3.14, port 8123)
├─ .github/workflows/          # CI: lint + pytest, hassfest & HACS validation
├─ config/                     # HA config used by scripts/develop
├─ custom_components/gbfs/
│   ├─ __init__.py             # Config entry setup, platform forwarding
│   ├─ config_flow.py          # URL step → station multi-select + options flow
│   ├─ coordinator.py          # Feed auto-discovery + 60 s polling coordinator
│   ├─ entity.py               # Base entity: one device per station
│   ├─ sensor.py               # Bikes, e-bikes, docks, occupancy, last report
│   ├─ binary_sensor.py        # Renting / returning
│   ├─ diagnostics.py          # Config entry diagnostics download
│   ├─ brand/                  # Integration icon (HA 2026.3+ local brand images)
│   ├─ strings.json            # UI strings
│   └─ translations/           # en, es
├─ tests/                      # pytest suite with real-feed fixtures
├─ scripts/                    # setup / develop / lint / test
└─ hacs.json                   # HACS metadata
```

---

## 🧪 Tests

Fixtures are trimmed captures of a real Lyft-style GBFS feed. The suite covers the config flow (happy path, errors, duplicates, options), the coordinator (language-keyed and GBFS 3.0 discovery, `ttl` handling, network failures), and entity states — including that optional sensors are only created when the feed supports them.

```bash
scripts/test
```

Every push and pull request runs the suite plus Ruff on GitHub Actions (**Test** workflow), and the **Validate** workflow runs [hassfest](https://developers.home-assistant.io/blog/2020/04/16/hassfest/) and HACS validation — also daily, to catch upstream requirement changes.
