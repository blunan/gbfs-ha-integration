# Development setup

## Dev container (recommended)

The dev container has everything you need, with no Python or Home Assistant installed on your machine. You need [Docker](https://www.docker.com/) and VS Code with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension.

1. Open the repository in VS Code.
2. Select **Reopen in Container** when prompted, or run **Dev Containers: Reopen in Container** from the command palette.
3. Wait for the build. `scripts/setup` installs the dependencies when the container is created.
4. Run `scripts/develop`. Home Assistant starts at `http://localhost:8123`, forwarded from the container, with the integration loaded from your checkout.

`.devcontainer/devcontainer.json` defines:

- **The image:** `mcr.microsoft.com/devcontainers/python` on Debian trixie. CI tests on Python 3.14, the version Home Assistant runs on.
- **VS Code extensions:** Python, Ruff, GitLens, EditorConfig, GitHub Actions and Claude Code. Ruff formats Python files on save, and the test explorer finds the pytest suite.
- **Mounts:** your `~/.claude` folder and `~/.claude.json` from the host, so Claude Code in the container keeps your sign-in and settings. They're created empty if they don't exist.

## Without the container

You need Python 3.14, the version Home Assistant and CI use.

```sh
python3.14 -m venv .venv
source .venv/bin/activate
scripts/setup
```

`scripts/setup` upgrades pip and installs `requirements.txt`:

| Package | Why |
|---|---|
| `homeassistant` | Pinned to the release the tests run against |
| `pytest-homeassistant-custom-component` | Test fixtures such as `hass` and `aioclient_mock`. Unpinned on purpose: each release pins one exact `homeassistant`, so pip picks the one that matches the pin above |
| `ruff` | Linter and formatter |
| `colorlog` | Colored Home Assistant logs in the terminal |

## Scripts

| Script | What it does |
|---|---|
| `scripts/setup` | Installs the development dependencies |
| `scripts/develop` | Runs Home Assistant in debug mode with `config/` as its configuration folder. The repository is on `PYTHONPATH`, so Home Assistant loads `custom_components/gbfs` from your checkout |
| `scripts/lint` | Runs `ruff check . --fix`, then `ruff format .` |
| `scripts/test` | Runs pytest and passes on any arguments, as in `scripts/test -k ttl` |

## Run Home Assistant locally

`scripts/develop` uses `config/configuration.yaml`, the only file in `config/` that git tracks:

```yaml
default_config:

logger:
  default: info
  logs:
    custom_components.gbfs: debug
```

Everything else Home Assistant writes to `config/`, such as its database, `.storage` and logs, is ignored by git. The first time, complete the onboarding at `http://localhost:8123`, then add GBFS from **Settings → Devices & services**. Ecobici's feed, `https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json`, is a good one to try.

To load code changes, stop `scripts/develop` with Ctrl+C and run it again. To start from scratch, `git clean -fdX config/` deletes everything git ignores in `config/` and keeps `configuration.yaml`.

## Project layout

```text
.
├── .devcontainer/            Dev container definition
├── .github/workflows/        Test, Validate, Docs and Release workflows
├── config/                   Home Assistant configuration for scripts/develop
├── custom_components/gbfs/   The integration; see How it works
├── docs/                     This site's pages
├── scripts/                  setup, develop, lint and test
├── tests/                    pytest suite and fixtures
├── hacs.json                 HACS and Marketplace metadata
├── mkdocs.yml                This site's configuration
├── pyproject.toml            pytest and Ruff settings
├── renovate.json             Dependency update policy
└── requirements.txt          Development dependencies
```

[How it works](architecture.md) explains each file in `custom_components/gbfs/`.

## Code style

Ruff lints and formats the code, configured in `pyproject.toml`:

- **Rules:** pyflakes (`F`), pycodestyle (`E`, `W`), isort (`I`), bugbear (`B`), simplify (`SIM`) and pyupgrade (`UP`), for Python 3.14. Line length isn't enforced (`E501` is off); the formatter takes care of it.
- **Imports** are sorted within their sections, with `homeassistant` treated as first-party, as in Home Assistant core.

CI fails on lint errors or unformatted files, so run `scripts/lint` before you push. Ruff also formats the Python code blocks in Markdown files, including this site's pages, so code examples must be valid, formatted Python. `.editorconfig` sets 4-space indentation for Python, 2 spaces for JSON, YAML and TOML, and LF line endings.

## Tests

The suite uses pytest with [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component), which provides a real `hass` instance and `aioclient_mock` to fake HTTP. No test touches the network: a request without a mock fails the test.

```sh
scripts/test                        # the whole suite
scripts/test tests/test_sensor.py   # one file
scripts/test -k options             # tests whose name matches
```

`tests/conftest.py` provides these fixtures:

| Fixture | What it does |
|---|---|
| `auto_enable_custom_integrations` | Lets every test load `custom_components/gbfs` (applies automatically) |
| `mock_feeds` | Serves the GBFS 1.x/2.x fixture files at `https://gbfs.example.com/gbfs/gbfs.json` and its `en` feeds |
| `mock_feeds_v3` | Serves the GBFS 3.0 fixture files at `https://gbfs.example.com/gbfs/3.0/gbfs.json`. `mock_v3_feeds(aioclient_mock, skip=…)` does the same but leaves out the feeds you name, to mock them differently |
| `config_entry`, `config_entry_v3` | An entry for each feed, with stations `1` and `2` selected |

`load_json_fixture(name)` reads a file from `tests/fixtures/`. The fixtures are trimmed, anonymized captures of real feeds:

| Fixture | Contents |
|---|---|
| `gbfs.json` | GBFS 1.x/2.x discovery, with `en` and `es` feed lists |
| `system_information.json` | The system name, "Example Bikes" |
| `station_information.json` | Three stations: Alpha, Beta and Gamma |
| `station_status.json` | Their status, with disabled bikes and docks but no e-bikes. Beta has no bikes or docks and isn't renting |
| `station_status_ebikes.json` | Alpha and Beta with `num_ebikes_available`, but without disabled counts |
| `gbfs_v3.json` | GBFS 3.0 discovery, with a single `data.feeds` list that includes `vehicle_types` |
| `system_information_v3.json` | The system name, translated: "Example Bikes" and "Bicis de Ejemplo" |
| `station_information_v3.json` | The same three stations with translated names; Gamma's is only in Spanish |
| `station_status_v3.json` | Their status with 3.0 field names, counts by vehicle type and RFC 3339 times, one with an offset |
| `vehicle_types_v3.json` | A classic bike, an e-bike and an e-scooter |

What each test file covers:

| File | Covers |
|---|---|
| `test_config_flow.py` | The full setup, in English and Spanish for a 3.0 feed; connection and invalid-feed errors; duplicate feeds, including URL variants; the options flow |
| `test_coordinator.py` | Feed discovery by language with fallback, for 3.0, and for invalid files. Reading names, times, e-bike types and station status the same way for every version. The first refresh, for 1.x/2.x and 3.0; a failed `vehicle_types.json`; `ttl` handling; failed updates |
| `test_sensor.py` | Sensor and binary sensor states for 1.x/2.x and 3.0 feeds, occupancy edge cases, location attributes, optional sensors with and without the feed's support, and per-entry device identifiers |
| `test_init.py` | Deleting a station's device: refused while the station is selected, allowed once it isn't |
| `test_diagnostics.py` | The diagnostics payload |

## Add a sensor

1. **Read the value.** If it comes from a GBFS field the integration doesn't read yet, add it to `StationStatus` in `coordinator.py`, such as `new_count: int | None = None`, and read it in `StationStatus.from_feed`. If GBFS 3.0 renamed the field, use `_first(record, old_name, new_name)`.
2. **Describe the sensor** in `SENSORS` in `sensor.py`:

    ```python
    GbfsSensorEntityDescription(
        key="new_count",
        translation_key="new_count",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda station: station.new_count,
        # Optional GBFS fields: only created if a station reports a value
        optional=True,
    )
    ```

3. **Name it** under `entity.sensor.<translation_key>.name` in `strings.json`, `translations/en.json` and `translations/es.json`. Keep `strings.json` and `translations/en.json` identical.
4. **Test it.** Add the field to the 1.x/2.x and 3.0 fixtures in `tests/fixtures/`, and check the new entity's state in `tests/test_sensor.py`. For an optional field, also check that the entity isn't created when the feed doesn't have the field.
5. **Document it** in the tables of [Entities](entities.md) and [Supported feeds](feeds.md), and in the README.

Binary sensors work the same way, in `binary_sensor.py`.

!!! warning "Keep existing keys"
    A description's `key` is part of its entities' unique IDs. Changing it creates new entities, and leaves the old ones orphaned in users' installations.

## Translations

The UI text lives in `strings.json` and `translations/<language>.json`. To add a language, copy `translations/en.json` to `translations/<code>.json`, such as `fr.json`, and translate the values. Keep the keys and the `{example_url}` placeholder.

## Contribute

1. Fork the repository and create a branch from `main`.
2. Make your change, with tests, and run `scripts/lint` and `scripts/test`.
3. Open a pull request that describes the change. Commit messages and pull request titles follow [Conventional Commits](https://www.conventionalcommits.org/), as in `fix(coordinator): Handle a missing ttl`.

`main` only accepts changes through pull requests, and their checks must pass; see [CI and releases](releasing.md).

## Work on this site { #docs }

The site is built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) from `docs/` and `mkdocs.yml`. Its packages are pinned with hashes in `docs/requirements.txt`, which is generated from `docs/requirements.in`.

To preview it with a local Python, use a separate virtual environment, since the docs pin some of the same packages as Home Assistant at other versions:

```sh
python3 -m venv .venv-docs
.venv-docs/bin/pip install --require-hashes -r docs/requirements.txt
.venv-docs/bin/mkdocs serve
```

Without a local Python, preview it in a throwaway container with the same Python version as CI, set by `python-version` in `.github/workflows/docs.yml`:

```sh
docker run --rm -it -p 127.0.0.1:8000:8000 -v "$PWD:/work:ro" -w /work python:3.15-slim-trixie \
  sh -c 'pip install -q --root-user-action=ignore --require-hashes -r docs/requirements.txt && mkdocs serve -a 0.0.0.0:8000'
```

Browse to `http://127.0.0.1:8000`; the page reloads when you save. Before you push, run `mkdocs build --strict`, as CI does: a broken link or anchor fails the build. In the container, add `--site-dir /tmp/site`, since the checkout is mounted read-only.

### Update the pinned packages { #update-docs-packages }

To move to a newer Material for MkDocs, change its version in `docs/requirements.in`. Then regenerate `docs/requirements.txt` with the command in that file's header. The command locks every package with its hashes, on the Python version the Docs workflow uses, and only accepts releases that are at least 14 days old. Renovate leaves both files alone, so these updates are always made by hand.
