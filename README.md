# PCC – Config Entry Rewrite (Vibe-Coded)

This is a **vibe-coded rewrite** of the original *Paulo's Custom Components* (PCC) cover integration for Home Assistant.

The goal of this rewrite was to update PCC to work with **Home Assistant 2025+** while modernizing the integration for my own setup.

## ✨ Changes from the original

- **Config Flow Support**  
  - You can now add and configure PCC covers entirely from the UI via **Settings → Devices & Services → Add Integration → PCC**.  
  - No more YAML is required (but the logic and options are the same as the original YAML format).
  - Includes an **Options Flow** so you can change templates, scripts, or travel times without editing files.

- **Removed Blocking Imports**  
  - The old platform/YAML loading method caused warnings about `import_module` inside the event loop.  
  - Now uses config entries (`async_setup_entry`) for async-safe loading.

- **Cover Feature Updates**  
  - Migrated from deprecated `SUPPORT_OPEN`, `SUPPORT_CLOSE`, `SUPPORT_STOP` constants to `CoverEntityFeature`.

- **Template Handling**  
  - Raw Jinja templates are still supported for `value_template` just like the original, but are stored and edited via the config flow.

- **UI Selectors**  
  - `action` selectors for open/close/stop scripts (no more manual YAML editing).
  - `template` selector for value templates.
  - `number` selectors for travel times.

- **Name & ID Management**  
  - Friendly name is set in the UI.
  - Entity ID can be changed via the Home Assistant UI after creation.

- **Legacy YAML Removed**  
  - This integration no longer loads via `cover: - platform: pcc`.
  - All setup is done via config entries.

## 🔧 Installation

1. Copy the `custom_components/pcc/` folder to your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration → PCC**.
4. Fill in the details:
   - **Unique ID** (must be unique across HA)
   - **Friendly Name**
   - **Device Class** (optional)
   - **Value Template** (Jinja string)
   - **Open/Close/Stop actions**
   - **Travel times** (optional)
5. Save. Your entity will be created and ready to use.

## 💡 Notes

- The underlying logic (scripts, travel time simulation, template state handling) is unchanged from the original PCC cover component.
- This rewrite is focused on keeping the integration **working and maintainable** for current and future Home Assistant versions.

## 🤝 Contributing

While this update was made for my own purposes, **pull requests are welcome**.  
If you find bugs, have suggestions, or want to extend functionality — feel free to open an issue or submit a PR.
