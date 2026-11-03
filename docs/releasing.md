# CI and releases

## Workflows

| Workflow | Runs on | What it does |
|---|---|---|
| **Test** (`test.yml`) | Pushes to `main`, pull requests, manual runs | **Lint and pytest:** on Python 3.14, runs `ruff check .`, `ruff format --check .` and `pytest` |
| **Validate** (`validate.yml`) | Pushes to `main`, pull requests, daily at 06:00 UTC, manual runs | **Hassfest:** Home Assistant's checks of the manifest, translations and structure. **HACS:** the HACS repository checks |
| **Docs** (`docs.yml`) | Pull requests, pushes to `main` that change the site, manual runs | **Docs build:** `mkdocs build --strict`. On `main`, it then deploys the site to GitHub Pages |
| **Release** (`release.yml`) | Pushed tags that start with `v` | **Publish GitHub release:** see [Release a version](#release-a-version) |

The daily Validate run catches new Hassfest and HACS rules before they surprise a pull request.

## Dependency updates

[Renovate](https://docs.renovatebot.com/) proposes dependency updates, as configured in `renovate.json`:

- **Once a week.** Update pull requests open early on Mondays, Mexico City time.
- **Grouped.** Minor and patch updates share one pull request. GitHub Actions updates share another, and pin actions to commit digests. Other major updates come one at a time.
- **At least 14 days old.** Renovate only proposes releases that are at least 14 days old.
- **Merged by hand.** Nothing merges automatically.
- **Python on its own.** Python version updates, including the dev container image, come in a separate **Python** pull request. Home Assistant has to support the new version first, and `target-version` in `pyproject.toml` should change in the same pull request.
- **Docs packages by hand.** Renovate ignores `docs/requirements.in` and `docs/requirements.txt`; see [Update the pinned packages](development.md#update-docs-packages).

## Release a version { #release-a-version }

1. Open a pull request that bumps `version` in `custom_components/gbfs/manifest.json`, and merge it.
2. Tag the merge commit and push the tag:

    ```sh
    git switch main && git pull
    git tag v0.2.0
    git push origin v0.2.0
    ```

3. The **Release** workflow checks that the tag, without its `v`, matches the manifest's `version`, and fails if it doesn't. Then it publishes a GitHub release, with notes generated from the merged pull requests.

A tag with a hyphen, such as `v0.2.0-rc1`, is published as a pre-release, and the manifest version must match it too (`0.2.0-rc1`). The Marketplace and HACS offer new releases as updates, but pre-releases only reach users who opt in; see [Updates](installation.md#updates).

## Documentation site

The **Docs** workflow builds this site on every pull request with `mkdocs build --strict`, so a broken link or anchor fails the check. When a push to `main` changes `docs/`, `mkdocs.yml` or the workflow itself, the workflow also deploys the site to GitHub Pages at <https://gbfs-ha-integration.blunan.com/>, one deployment at a time. To preview changes before you push, see [Work on this site](development.md#docs).
