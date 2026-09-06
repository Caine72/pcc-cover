# PCC Cover

PCC Cover is a template-based Home Assistant cover integration. It is based on
the original [Paulo's Custom Components cover integration](https://github.com/pfandrade/ha-custom-components)
by Paulo Andrade.

Home Assistant **2025.12 or newer** is required.

> [!IMPORTANT]
> This integration is maintained for a private Home Assistant setup and
> published primarily for HACS installation. Bug reports are welcome, but there
> is no support or broad compatibility promise.

Development is AI-assisted.

## What this component does

The **PCC Cover** integration lets you create a cover entity (e.g., garage door, gate, shutter) whose **open/close/stop actions** are defined by your own Home Assistant service calls (like switching a relay), while the **state** (open vs. closed) is determined by a **Jinja value template** you provide (for example, a binary sensor). The integration also simulates **opening/closing** for a configurable time window so the UI shows motion while your hardware is actuating. In short, it gives you a simple but powerful way to turn existing devices (smart or dumb) into a first-class **`cover`** in Home Assistant — entirely from the UI, no YAML required.

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

For example, a garage-door contact sensor can be used as the state template:

```jinja
{{ is_state('binary_sensor.garage_door', 'on') }}
```

The template must return `true`/`on` while the cover is open and `false`/`off`
while it is closed. Open and close actions start their configured travel timers
immediately. Reversing direction cancels the previous timer, reaching the
matching end state ends travel early, and the optional stop action clears all
simulated movement.
