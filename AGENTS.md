# For AI Agents

## Project overview

This repository contains **GBFS for Home Assistant**, a custom integration that discovers station-based bike-share systems and exposes station availability as Home Assistant sensors and binary sensors.

Key compatibility requirements:

- Support GBFS 1.x, 2.x, and 3.0 without requiring users to select a feed version.
- Normalize version-specific feed representations into the integration's internal model.
- Use Home Assistant's shared asynchronous HTTP session and coordinator patterns.
- Create optional entities only when the feed provides the relevant data.
- Poll once per bike-share system, not once per station.
- Preserve stable device/entity registry identity across reloads and options changes.

Read the relevant files and tests before changing behavior. Treat the repository's implementation, `pyproject.toml`, CI workflows, and documentation as authoritative if this file becomes stale.

## Repository map

- `custom_components/gbfs/` — Home Assistant integration source.
  - `manifest.json` — integration metadata, dependencies, platforms, and version.
  - `__init__.py` — config-entry setup/unload, platform forwarding, and device cleanup.
  - `config_flow.py` — feed discovery, station selection, and options flow.
  - `coordinator.py` — feed resolution, HTTP fetching, GBFS normalization, station state, and polling.
  - `entity.py` — shared entity behavior, device association, unique IDs, and availability.
  - `sensor.py` — sensor descriptions and value extraction.
  - `binary_sensor.py` — renting/returning binary sensors.
  - `diagnostics.py` — diagnostics payload.
  - `const.py` — constants and integration exceptions.
  - `strings.json`, `translations/` — config-flow and entity translations.
  - `brand/` — integration branding assets.
- `tests/` — pytest tests and feed fixtures.
- `config/` — local Home Assistant development configuration; generated runtime data is ignored.
- `scripts/` — setup, development, lint, and test helpers.
- `docs/` — MkDocs documentation source.
- `.github/workflows/` — test, validation, documentation, and release automation.
- `pyproject.toml` — Ruff and pytest configuration.
- `requirements.txt` — development/test dependencies.
- `hacs.json` — HACS/Marketplace metadata.
- `release-please-config.json`, `.release-please-manifest.json`, `CHANGELOG.md` — release automation; see [Versions and releases](#versions-and-releases).

## Architecture and invariants

### Config-entry lifecycle

The integration is configured through the Home Assistant UI. The config flow accepts a GBFS auto-discovery URL, resolves the required feeds and system/station metadata, and lets the user select stations. The options flow allows stations to be changed without reinstalling.

Keep setup, unload, reload, platform forwarding, and device-registry cleanup consistent with current Home Assistant APIs. Do not introduce YAML configuration as a replacement for the existing UI flow.

### Feed discovery and HTTP

- Resolve feed URLs from `gbfs.json` according to the published GBFS version.
- GBFS 3.0 publishes feeds under `data.feeds`; GBFS 1.x/2.x use language-keyed feed data. Preserve language matching and fallback behavior.
- `station_information` and `station_status` are required for this station-based integration. Reject unsupported/incomplete feeds with the integration's established exception types.
- Use Home Assistant's shared `aiohttp` client session; do not create an independent session for routine requests.
- Preserve the existing request timeout and JSON parsing behavior, including feeds that return JSON with a non-JSON content-type header.
- Map connection/HTTP failures and malformed or structurally invalid feed data to the existing `GbfsError` hierarchy. Avoid leaking raw implementation exceptions into config-flow or coordinator UX.
- Never make real network requests in unit tests; mock requests using `aioclient_mock`.

### Version normalization

Keep GBFS-specific differences at the feed boundary. Normalize them into the common internal representation before entities consume them.

Pay particular attention to:

- Renamed GBFS 3.0 vehicle-count fields versus earlier bike-count fields.
- Localized text represented as plain strings in older feeds and localized objects in GBFS 3.0.
- Timestamps represented as epoch seconds in older feeds and RFC 3339 strings in GBFS 3.0; normalize timestamps to timezone-aware UTC datetimes.
- Boolean-like feed values represented as either booleans or `0`/`1`.
- E-bike counts supplied directly or inferred from `vehicle_types` metadata and per-station vehicle-type counts.

`StationStatus` is the normalized, immutable station-state model. Extend its parsing path when adding a new GBFS field; do not make each entity independently interpret raw feed versions.

### Coordinator and polling

- `GbfsCoordinator` owns system-wide station-status polling and cached station metadata.
- Fetch `station_status.json` once per update, regardless of how many stations the user selected.
- Preserve the default 60-second polling interval and respect a valid feed `ttl` when it is greater than the default.
- Keep transient network failures within Home Assistant's coordinator retry/backoff behavior.
- Preserve diagnostics data such as raw station records and observed/published field names when changing the update pipeline.
- Do not move network I/O into individual entities.

### Entities and registry behavior

- Reuse the shared `GbfsEntity` base and `CoordinatorEntity` lifecycle.
- Keep device identifiers scoped by config-entry ID and station ID to avoid collisions between different operators.
- Keep unique IDs stable. Changing an entity's unique ID or device identifier is a migration-level change and must be deliberate.
- Entity availability must reflect coordinator update success and whether that station is present in current coordinator data.
- Optional sensors should be instantiated only when the feed actually exposes the relevant capability; avoid permanent `unknown` entities for unsupported fields.
- Only the bikes-available sensor should provide station map coordinates, so a station produces one map marker.
- Preserve the existing device-removal guard: a selected station's device must not be removable if it would be recreated on reload; devices for stations no longer selected may be removed.

## Making changes

### Adding or changing a GBFS field / sensor

1. Update the normalized `StationStatus` model and `StationStatus.from_feed` parsing in `coordinator.py`.
2. Add or update a `GbfsSensorEntityDescription` in `sensor.py`, including the correct translation key, value function, and optional/state-class metadata.
3. Ensure optional entities are gated by actual feed capability rather than fabricated defaults.
4. Update relevant GBFS fixtures in `tests/fixtures/` and tests in the appropriate `tests/test_*.py` module.
5. Update `strings.json`, `translations/en.json`, and `translations/es.json` with matching keys and placeholders.
6. Update the Entities and Supported feeds documentation.

For new numeric measurements, choose Home Assistant device class, unit, and `state_class` only when semantically correct. Preserve `measurement` semantics for continuously measured numeric values where appropriate; do not assign measurement metadata to timestamps or categorical values.

### Config flow and options

- Keep user-facing setup and station selection resilient to incomplete feeds and connection errors.
- Preserve the existing config-entry data/options contract unless a migration is included.
- Test first setup, invalid/unreachable feeds, station selection, options changes, and reload behavior when affected.
- Keep user-visible strings in translation files rather than hardcoding them in Python.

### Translations

- Keep `strings.json` and language translation files structurally aligned.
- English and Spanish are currently supported.
- Preserve placeholder names exactly across languages (for example, `{example_url}`).
- When adding a language, copy the key structure from `translations/en.json` and translate values only.

### Diagnostics and privacy

- Keep diagnostics useful for debugging feed and coordinator behavior.
- Follow Home Assistant diagnostics conventions and redact credentials or other sensitive values if the data model ever introduces them.
- Do not add secrets, private tokens, or personal data to fixtures, logs, or diagnostics.

### Documentation

- Documentation is built with Material for MkDocs.
- Keep README claims, docs, entity descriptions, translations, and actual implementation consistent.
- Update architecture, supported-feed, entity, configuration, or troubleshooting pages when behavior changes.
- Use concise examples that match current Home Assistant entity IDs and configuration.

## Development environment and commands

The documented development environment uses **Python 3.14**.

Recommended: open the repository in VS Code and reopen it in the configured Dev Container. Alternatively:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
scripts/setup
```

Useful commands:

```bash
scripts/lint                         # Ruff lint fixes and formatting
scripts/test                         # Full pytest suite
scripts/test tests/test_sensor.py    # One test module
scripts/test -k options              # Tests matching an expression
scripts/develop                      # Run local Home Assistant with this integration
```

For documentation changes:

```bash
python3 -m venv .venv-docs
.venv-docs/bin/pip install --require-hashes -r docs/requirements.txt
.venv-docs/bin/mkdocs serve
.venv-docs/bin/mkdocs build --strict
```

Use the helper scripts rather than inventing alternate commands. Check `scripts/*`, `requirements.txt`, and workflow files if a command changes.

## Tests and quality gates

- Tests use pytest and `pytest-homeassistant-custom-component`.
- HTTP interactions must be mocked with the repository's `aioclient_mock` fixtures.
- Reuse the existing GBFS 1.x/2.x and GBFS 3.0 fixture patterns (`mock_feeds`, `mock_feeds_v3`, and `config_entry`) where applicable.
- Add regression tests for bug fixes; do not rely only on manual Home Assistant testing.
- Cover version-specific parsing, missing/optional fields, malformed data, timestamps, language selection, TTL behavior, coordinator failures, and entity availability when relevant.
- Run `scripts/lint` and the narrowest relevant tests first, then `scripts/test` for meaningful changes.
- For documentation changes, run `mkdocs build --strict` using the locked docs dependencies.
- CI also runs Home Assistant `hassfest` and HACS validation. Keep metadata and platform declarations valid.

Do not claim checks passed unless they were actually run.

## Code style

- Follow Ruff configuration in `pyproject.toml`; current target is Python 3.14.
- Enabled Ruff rule families include `B`, `E`, `F`, `I`, `SIM`, `UP`, and `W`; `E501` is ignored.
- Use `ruff format` formatting via `scripts/lint`.
- Python indentation: 4 spaces. JSON, YAML, and TOML indentation: 2 spaces. Use LF line endings.
- Prefer clear typed functions and small parsing helpers. Keep version-specific parsing centralized.
- Follow current Home Assistant APIs and established patterns already used in this integration; avoid speculative compatibility abstractions.

## Dependencies, CI, and releases

- Keep runtime dependencies minimal and justified; prefer Home Assistant-provided facilities.
- Dependency updates are managed by Renovate. Review compatibility and CI results rather than accepting automated updates blindly.
- GitHub Actions validates tests/style, Home Assistant/HACS metadata, documentation, and releases.
- Releases are automated by release-please, which keeps the version in `custom_components/gbfs/manifest.json`; see [Versions and releases](#versions-and-releases).

## Agent workflow

Before editing:

1. Inspect the target code, its callers, relevant fixtures/tests, and current documentation.
2. Identify which architectural invariant(s) the change could affect.
3. Prefer the smallest coherent change; avoid unrelated refactors.

While editing:

1. Keep feed-version compatibility and Home Assistant registry stability in mind.
2. Update tests, translations, and docs alongside behavior changes.
3. Do not add dependencies or change public entity IDs without a clear requirement.

Before finishing:

1. Run relevant tests and lint/format checks when the environment permits.
2. Review the diff for accidental changes, generated files, secrets, and stale comments.
3. Report exactly what changed and which checks were run; call out anything not run or any remaining uncertainty.

## GitHub

- Always use Conventional Commits spec.
- Never commit secrets, credentials, environment files, personal configuration, or build artifacts.
- Keep pull requests focused and document any intentional compatibility changes.

### Versions and releases

`main` takes squash merges only, so a PR's title becomes its commit on `main`, and release-please reads that title to pick the next version. A new version means what users install (`custom_components/gbfs/`) changed:

- `feat:`: new or changed behavior. Minor version.
- `fix:`, `perf:`, `revert:`: a bug fix, a performance improvement, or a reverted change. Patch version.
- `feat!:` / `fix!:`, or a `BREAKING CHANGE:` footer: a change that breaks existing setups, such as removing an entity or changing the config-entry contract without a migration. Major version.
- `docs:`, `ci:`, `chore:`, `refactor:`, `test:`, `build:`, `style:`: no version. Use these when what users install stays the same.

Renovate titles its updates `chore(deps):`, because the integration has no runtime dependencies, so they release nothing.

The `Release` workflow (`.github/workflows/release.yml`) runs release-please on every push to `main`. It keeps a release PR open (`chore(main): release X.Y.Z`) with the next version and its `CHANGELOG.md` entry. Merging that PR by hand, when the version should go out, tags `vX.Y.Z` and publishes the GitHub release. The workflow uses a GitHub App token (`RELEASE_APP_CLIENT_ID` variable, `RELEASE_APP_PRIVATE_KEY` secret), not `GITHUB_TOKEN`, because a PR opened with `GITHUB_TOKEN` runs no workflows and the required checks (`Lint and pytest`, `Hassfest`, `HACS`, `Docs build`) would never report.

- Don't edit `CHANGELOG.md`, `.release-please-manifest.json`, or the `version` in `manifest.json` by hand; release-please updates them in its release PR.
- To correct a merged PR's type before its release, add the corrected message to that PR's description between a `BEGIN_COMMIT_OVERRIDE` line and an `END_COMMIT_OVERRIDE` line; release-please reads it instead of the commit. To force a version, end that message with a `Release-As: X.Y.Z` footer.
- This project doesn't publish pre-releases. Don't force a version with a suffix such as `0.3.0-rc1`: it would go out to every user as a normal stable release. release-please's `prerelease` option can't prevent that here, because it would also flag every 0.x release.
- Don't start a paragraph in a commit body with `feat:`, `fix:` or another type: release-please reads it as another commit.

## Security and Guardrails

- Never commit secrets, credentials, tokens, or private keys.
- Always validate untrusted input at appropriate boundaries.
- Always use parameterized queries and safe APIs for external input.
- Avoid logging sensitive information.
- Always follow least-privilege principles.
- Never disable security controls to bypass errors.
