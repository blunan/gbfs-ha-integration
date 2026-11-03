# Installation

GBFS is a custom integration: it isn't built into Home Assistant, so you add it from its GitHub repository. Home Assistant 2026.11 replaced HACS with the built-in **Marketplace**, so pick the tab for your version.

=== "Marketplace (2026.11 or later)"

    1. Go to **Settings → Marketplace**. The first time, accept the warning about community content. Only administrators can open the Marketplace.
    2. Select **Add from link** in the top right.
    3. In **GitHub link**, enter `blunan/gbfs-ha-integration` or `https://github.com/blunan/gbfs-ha-integration`, and select **Add**. If you haven't connected GitHub yet, the Marketplace asks you to do it now. If it asks for a type, choose integrations and select **Add** again.
    4. Open **GBFS**, select **Install** and confirm.
    5. If the Marketplace says Home Assistant needs a restart, restart it. A repair under **Settings → System → Repairs** can do it for you. Otherwise the GBFS setup opens right away.

=== "HACS (2026.3 – 2026.10)"

    [Open GBFS in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=blunan&repository=gbfs-ha-integration&category=integration){ .md-button .md-button--primary }

    The button opens the repository in your HACS. To add it by hand instead:

    1. Open **HACS** and select **⋮ → Custom repositories** in the top right.
    2. Enter `https://github.com/blunan/gbfs-ha-integration`, choose the type **Integration** and select **Add**.
    3. Search for **GBFS**, open it and select **Download**.
    4. Restart Home Assistant.

    When you update Home Assistant to 2026.11 or later, HACS moves into the Marketplace by itself: GBFS stays installed and keeps getting updates.

=== "Manual"

    1. Download the repository, preferably from a [release](https://github.com/blunan/gbfs-ha-integration/releases).
    2. Copy its `custom_components/gbfs/` folder into the `custom_components/` folder of your Home Assistant configuration directory, the one with `configuration.yaml`. Create `custom_components/` if it doesn't exist. You should end up with:

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

    Manual installs don't update themselves. Repeat these steps to upgrade.

Next, [add the integration](configuration.md).

## Updates

The Marketplace and HACS create an update entity for GBFS, so a new release appears under **Settings → Updates** like any other update. Check the [release notes](https://github.com/blunan/gbfs-ha-integration/releases), install it, and restart Home Assistant if asked.

Pre-releases, such as `0.2.0-rc1`, are only offered if you opt in. In the Marketplace, go to **Settings → Devices & services → Marketplace** and open the GBFS device. Its **Pre-release** switch entity is disabled by default: enable the entity, then turn the switch on.

## Uninstall

1. Delete the GBFS entries: go to **Settings → Devices & services → GBFS** and select **⋮ → Delete** on each entry. This removes their devices and entities.
2. Remove the files:
    - **Marketplace:** open GBFS and select **⋮ → Uninstall**. **Delete and uninstall** does step 1 for you as well.
    - **HACS:** open GBFS and select **⋮ → Remove**.
    - **Manual:** delete `custom_components/gbfs/`.
3. Restart Home Assistant.
