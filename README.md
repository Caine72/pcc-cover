# PCC Cover: Template-Based Cover Integration for Home Assistant 

This is a **vibe-coded rewrite** of the original [*Paulo's Custom Components* (PCC) cover integration](https://github.com/pfandrade/ha-custom-components) for Home Assistant by Paulo Andrade.

The goal of this rewrite was to update PCC to work with **Home Assistant 2025+** while modernizing the integration for my own setup.

---

## Table of Contents

* [What this component does](#what-this-component-does)
* [Installation via HACS](#installation-via-hacs)
* [Setup](#setup)
* [Changes from the original](#changes-from-the-original)
* [Notes](#notes)
* [Contributing](#contributing)

---

## What this component does

The **PCC Cover** integration lets you create a cover entity (e.g., garage door, gate, shutter) whose **open/close/stop actions** are defined by your own Home Assistant service calls (like switching a relay), while the **state** (open vs. closed) is determined by a **Jinja value template** you provide (for example, a binary sensor). The integration also simulates **opening/closing** for a configurable time window so the UI shows motion while your hardware is actuating. In short, it gives you a simple but powerful way to turn existing devices (smart or dumb) into a first-class **`cover`** in Home Assistant — entirely from the UI, no YAML required.

---

## Installation via HACS

This integration can be installed and managed through [HACS](https://hacs.xyz/).

1. In Home Assistant, go to **HACS → Integrations → 3-dot menu → Custom repositories**.
2. Add this repository URL:

   ```
   https://github.com/Caine72/pcc-cover
   ```

   Category: **Integration**.
3. Click **ADD** and close the dialog.
4. Search for **PCC Cover** in HACS Integrations and click **Download**.
5. Restart Home Assistant.

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration → PCC**.
2. Fill in the details:

   * **Unique ID** (must be unique across HA)
   * **Friendly Name**
   * **Device Class** (optional)
   * **Value Template** (Jinja string)
   * **Open/Close/Stop actions**
   * **Travel times** (optional)
3. Click **Submit**. Your entity will be created and ready to use.

---

## Changes from the original

* **Config Flow Support**

  * You can now add and configure PCC covers entirely from the UI via **Settings → Devices & Services → Add Integration → PCC**.
  * No more YAML is required (but the logic and options are the same as the original YAML format).
  * Includes an **Options Flow** so you can change templates, scripts, or travel times without editing files.

* **Removed Blocking Imports**

  * The old platform/YAML loading method caused warnings about `import_module` inside the event loop.
  * Now uses config entries (`async_setup_entry`) for async-safe loading.

* **Cover Feature Updates**

  * Migrated from deprecated `SUPPORT_OPEN`, `SUPPORT_CLOSE`, `SUPPORT_STOP` constants to `CoverEntityFeature`.

* **Template Handling**

  * Raw Jinja templates are still supported for `value_template` just like the original, but are stored and edited via the config flow.

* **UI Selectors**

  * `action` selectors for open/close/stop scripts (no more manual YAML editing).
  * `template` selector for value templates.
  * `number` selectors for travel times.

* **Name & ID Management**

  * Friendly name is set in the UI.
  * Entity ID can be changed via the Home Assistant UI after creation.

* **Legacy YAML Removed**

  * This integration no longer loads via `cover: - platform: pcc`.
  * All setup is done via config entries.

---

## Notes

* The underlying logic (scripts, travel time simulation, template state handling) is unchanged from the original PCC cover component.
* This rewrite is focused on keeping the integration **working and maintainable** for current and future Home Assistant versions.

---

## Contributing

While this update was made for my own purposes, **pull requests are welcome**.
If you find bugs, have suggestions, or want to extend functionality — feel free to open an issue or submit a PR.

