# Installation

Install GBFS using the method corresponding to your Home Assistant version.

=== "Marketplace (Home Assistant 2026.11+)"

    1. Go to **Settings → Marketplace**.
    2. Select **Add from link** in the top right.
    3. Enter `blunan/gbfs-ha-integration` or `https://github.com/blunan/gbfs-ha-integration`, and select **Add**.
    4. Select **GBFS**, click **Install**, and confirm.
    5. Restart Home Assistant if prompted.

=== "HACS (Home Assistant 2026.3 – 2026.10)"

    [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=blunan&repository=gbfs-ha-integration&category=integration)

    Or install manually via HACS:

    1. Open **HACS** and select **⋮ → Custom repositories** in the top right.
    2. Enter `https://github.com/blunan/gbfs-ha-integration`, select category **Integration**, and click **Add**.
    3. Search for **GBFS**, open it, and select **Download**.
    4. Restart Home Assistant.

=== "Manual"

    1. Download the latest release from the [Releases](https://github.com/blunan/gbfs-ha-integration/releases) page.
    2. Copy the `custom_components/gbfs/` folder into your Home Assistant `config/custom_components/` directory:

        ```text
        config/
        ├── configuration.yaml
        └── custom_components/
            └── gbfs/
                ├── __init__.py
                ├── manifest.json
                └── …
        ```

    3. Restart Home Assistant.

    !!! note "Updates for manual installs"
        Manual installations do not update automatically. Repeat these steps whenever a new version is released.

## Updates

Both Marketplace and HACS notify you when a new release is available under **Settings → Updates**. Review the release notes and install the update as usual.

To opt into pre-releases (e.g., `0.2.0-rc1`):

- **Marketplace:** Go to **Settings → Devices & services → Marketplace**, open the **GBFS** device, enable the disabled **Pre-release** switch entity, and turn it on.
- **HACS:** Open the GBFS integration page in HACS, select **⋮ → Redownload**, and enable **Show beta versions**.

## Uninstall

To completely remove the integration:

1. **Delete configured entries:** Go to **Settings → Devices & services → GBFS** and select **⋮ → Delete** on each configured feed entry. This removes all associated devices and entities.
2. **Remove integration files:**
    - **Marketplace:** Open GBFS and select **⋮ → Uninstall** (or choose **Delete and uninstall** to perform step 1 automatically).
    - **HACS:** Open GBFS and select **⋮ → Remove**.
    - **Manual:** Delete the `custom_components/gbfs/` directory.
3. Restart Home Assistant.

---

Once installed, proceed to [Configuration](configuration.md) to add your bike-share feed.
