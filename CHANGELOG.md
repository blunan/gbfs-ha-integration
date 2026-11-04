# Changelog

## [0.2.0](https://github.com/blunan/gbfs-ha-integration/compare/v0.1.0...v0.2.0) (2026-11-03)

- Support GBFS 3.0 feeds: renamed vehicle counts, RFC 3339 timestamps, and station and system names translated into Home Assistant's language ([#10](https://github.com/blunan/gbfs-ha-integration/pull/10)).
- Count e-bikes by vehicle type, so feeds with vehicle types but no `num_ebikes_available`, such as Buenos Aires' Ecobici, gain an E-bikes available sensor ([#10](https://github.com/blunan/gbfs-ha-integration/pull/10)).
- Allow deleting the devices of stations that are no longer selected ([#10](https://github.com/blunan/gbfs-ha-integration/pull/10)).
- Add a documentation site at [gbfs-ha-integration.blunan.com](https://gbfs-ha-integration.blunan.com/) ([#10](https://github.com/blunan/gbfs-ha-integration/pull/10)).
- Fix the manifest's documentation and issue tracker links, which pointed to a repository that doesn't exist.
- Fix a Hassfest failure by moving the example feed URL out of the translations and into a description placeholder.

## [0.1.0](https://github.com/blunan/gbfs-ha-integration/releases/tag/v0.1.0) (2026-11-03)

First release of the GBFS integration for Home Assistant.

- Set up from the UI, discovering a bike-share system's feeds from its `gbfs.json` URL.
- Sensors for available bikes, e-bikes and docks, disabled bikes and docks, occupancy, and last report time, plus renting and returning binary sensors.
- Diagnostics for troubleshooting feeds.
- Stable station identifiers and normalized feed URLs, which prevent duplicates.
- Local brand icons, and English and Spanish translations.
- Dev: test suite with pytest, and linting in CI.
