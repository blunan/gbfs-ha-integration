# Development & Contributing

Guidelines for setting up a local development environment, running tests, contributing code, and releasing new versions.

## Development Setup

### Dev Container (Recommended)

The dev container provides an isolated environment pre-configured with Python 3.14, Home Assistant test fixtures, and development tooling.

Requirements: [Docker](https://www.docker.com/) and VS Code with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension.

1. Open the project repository in VS Code.
2. Select **Reopen in Container** when prompted.
3. Dependencies are installed automatically during container creation.
4. Run `scripts/develop` in the container terminal to start Home Assistant at `http://localhost:8123`.

### Local Virtual Environment

Alternatively, set up a local virtual environment with Python 3.14:

```sh
python3.14 -m venv .venv
source .venv/bin/activate
scripts/setup
```

## Helper Scripts

| Script | Purpose |
|---|---|
| `scripts/setup` | Installs development and test dependencies from `requirements.txt` |
| `scripts/develop` | Starts Home Assistant in debug mode with the local integration loaded |
| `scripts/lint` | Formats and lints code using Ruff (`ruff check . --fix && ruff format .`) |
| `scripts/test` | Runs the test suite via pytest, passing through any arguments (e.g., `scripts/test -k ttl`) |

## Running Home Assistant Locally

`scripts/develop` runs Home Assistant using `config/configuration.yaml`:

```yaml
default_config:

logger:
  default: info
  logs:
    custom_components.gbfs: debug
```

All generated database files, logs, and `.storage` items in `config/` are excluded from git. Access the local instance at `http://localhost:8123`, complete the onboarding wizard, and add a test feed (such as Ecobici: `https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json`).

To reload code edits, restart `scripts/develop` (Ctrl+C and re-run). To reset the test configuration completely, run `git clean -fdX config/`.

## Project Structure

```text
.
├── .devcontainer/                 Dev container configuration
├── .github/workflows/             CI and release automation
├── config/                        Local Home Assistant test configuration
├── custom_components/gbfs/        Integration source code
├── docs/                          Documentation source files
├── scripts/                       Development helper scripts
├── tests/                         pytest test suite and feed fixtures
├── .release-please-manifest.json  The last released version, kept by release-please
├── AGENTS.md                      Instructions for AI coding agents
├── CHANGELOG.md                   What changed in each version, kept by release-please
├── hacs.json                      HACS and Marketplace metadata
├── mkdocs.yml                     Documentation site configuration
├── pyproject.toml                 Tool settings (Ruff, pytest)
├── release-please-config.json     Release settings: changelog sections and version files
├── renovate.json                  Automated dependency update policy
└── requirements.txt               Development dependencies
```

## Code Style & Formatting

Code style is enforced via Ruff and configured in `pyproject.toml`:

- **Rule sets:** Pyflakes (`F`), pycodestyle (`E`, `W`), isort (`I`), flake8-bugbear (`B`), flake8-simplify (`SIM`), and pyupgrade (`UP`) targeting Python 3.14.
- **Formatting:** Handled automatically by `ruff format`.
- **Indentation:** 4 spaces for Python; 2 spaces for JSON, YAML, and TOML; LF line endings.
- **Commits:** Use [Conventional Commits](https://www.conventionalcommits.org/), such as `fix: …`, `docs: …`, or `chore(deps): …`. A pull request's title decides the next version; see the [release process](#release-process).

Run `scripts/lint` before committing changes.

## Testing

The test suite runs on pytest using `pytest-homeassistant-custom-component`. All HTTP requests are mocked via `aioclient_mock`; tests make no real network calls.

```sh
scripts/test                        # Run entire test suite
scripts/test tests/test_sensor.py   # Run single test module
scripts/test -k options             # Run tests matching an expression
```

### Test Fixtures

- `mock_feeds`: Mocks GBFS 1.x/2.x feeds using sample responses in `tests/fixtures/`.
- `mock_feeds_v3`: Mocks GBFS 3.0 feeds with translations and ISO 8601 timestamps.
- `config_entry`: Pre-configured config entry instance tracking sample stations.

## Adding a Sensor

1. **Extract data:** If adding a new field from GBFS, add an attribute to `StationStatus` in `coordinator.py` and parse it in `StationStatus.from_feed`.
2. **Define entity:** Add a `GbfsSensorEntityDescription` to `SENSORS` in `sensor.py`:

    ```python
    GbfsSensorEntityDescription(
        key="new_metric",
        translation_key="new_metric",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda station: station.new_metric,
        optional=True,
    )
    ```

3. **Add translations:** Add the entity label to `strings.json`, `translations/en.json`, and `translations/es.json`.
4. **Add tests:** Update fixture files in `tests/fixtures/` and add test assertions in `tests/test_sensor.py`.
5. **Update docs:** Document the new sensor in [Entities](entities.md) and [Supported Feeds](feeds.md).

## Translations

UI strings and entity labels live in `strings.json` and `translations/<lang>.json`.

To add a new language, create `translations/<lang>.json` copied from `translations/en.json` and translate the string values. Maintain matching keys and placeholder tokens (`{example_url}`).

## Working on Documentation

The documentation site is built with Material for MkDocs.

To preview changes locally:

```sh
python3 -m venv .venv-docs
.venv-docs/bin/pip install --require-hashes -r docs/requirements.txt
.venv-docs/bin/mkdocs serve
```

To validate links and formatting strictly (matching CI):

```sh
.venv-docs/bin/mkdocs build --strict
```

Without a local Python, preview it in a throwaway container on the same Python version as CI (`python-version` in `.github/workflows/docs.yml`):

```sh
docker run --rm -it -p 127.0.0.1:8000:8000 -v "$PWD:/work:ro" -w /work python:3.14-slim-trixie \
  sh -c 'pip install -q --root-user-action=ignore --require-hashes -r docs/requirements.txt && mkdocs serve -a 0.0.0.0:8000'
```

Browse to `http://127.0.0.1:8000`. To run the strict build in the container, add `--site-dir /tmp/site`, since the checkout is mounted read-only.

### Updating Documentation Dependencies

Dependency hashes are pinned in `docs/requirements.txt` from `docs/requirements.in`. To upgrade, update the version in `docs/requirements.in` and re-lock using the command specified in the file's header.

The lock is resolved on the Python version that `.github/workflows/docs.yml` installs; change both together.

## CI Workflows

GitHub Actions runs automated checks on every pull request and push to `main`:

| Workflow | Trigger | Description |
|---|---|---|
| **Test** (`test.yml`) | Pull requests, pushes to `main` | Runs Ruff linter, formatting checks, and full pytest suite on Python 3.14. |
| **Validate** (`validate.yml`) | Pull requests, pushes, daily schedule | Runs Home Assistant `hassfest` validation and HACS repository checks. |
| **Docs** (`docs.yml`) | Pull requests modifying docs | Runs `mkdocs build --strict`. Pushes to `main` deploy the site to GitHub Pages. |
| **Release** (`release.yml`) | Pushes to `main` | Runs release-please, which keeps the release pull request up to date and, once it's merged, tags the version and publishes the GitHub release. |

## Dependency Updates

[Renovate](https://docs.renovatebot.com/) manages dependency updates according to `renovate.json`:

- Checks weekly (Mondays).
- Minor and patch updates are grouped into a single pull request.
- Pinned actions use immutable commit hashes.
- Only releases at least 14 days old are proposed.
- All dependency pull requests require manual review and passing CI before merging.
- Updates are titled `chore(deps):` and release nothing: the integration has no runtime dependencies, so they only change development tooling.

## Release Process

Versions come from `.github/workflows/release.yml`, which runs [release-please](https://github.com/googleapis/release-please) on every push to `main`. Pull request titles follow [Conventional Commits](https://www.conventionalcommits.org/), and since `main` takes squash merges only, each title becomes the commit release-please reads:

- `feat:` (new or changed behavior) proposes a minor version, and `fix:`, `perf:`, or `revert:` a patch. `feat!:` or a `BREAKING CHANGE:` footer proposes a major.
- Other types (`docs:`, `ci:`, `chore:`, `refactor:`, `test:`, `build:`, `style:`) propose none.

release-please keeps a release pull request open with the next version and its `CHANGELOG.md` entry. That pull request also bumps the `version` in `custom_components/gbfs/manifest.json`, so don't change it by hand. When a version should go out, merge the release pull request. That tags `vX.Y.Z` and publishes the [GitHub release](https://github.com/blunan/gbfs-ha-integration/releases), which Marketplace and HACS then offer as an update.

The workflow uses a GitHub App token (the `RELEASE_APP_CLIENT_ID` variable and the `RELEASE_APP_PRIVATE_KEY` secret), not `GITHUB_TOKEN`, because a pull request opened with `GITHUB_TOKEN` runs no workflows, so the required checks would never report on it.
