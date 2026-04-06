# Changelog

## [2.1.3] - 2026-04-06
### Fixed
- Fixed crash when opening Configure (options flow) from the integration card on Home Assistant 2026.x.
- Resolved AttributeError: property 'config_entry' has no setter caused by outdated OptionsFlow initialization.

### Changed
- Updated Options Flow implementation to follow current Home Assistant guidelines:
  - Removed passing config_entry to PCCOptionsFlow constructor.
  - Now relies on self.config_entry provided by Home Assistant.
- Aligned integration with post-2025.12 Home Assistant API changes for config entries and options flows.

## [2.1.1] - 2025-08-26
### Fixed
- Existing PCC entries can now be reconfigured from the integration card (Configure opens the options form).

### Changed
- Options Flow no longer exposes unique_id (kept immutable per HA guidelines).
- Minor logging cleanup and manifest version bump.

## [2.1.0] - 2025-08-12
### Changed
- Updated integration to support Home Assistant 2025+.
- Migrated from YAML platform setup to full Config Entry support with UI-based setup.
- Added Options Flow to modify templates, scripts, and travel times without editing files.
- Replaced deprecated `SUPPORT_*` constants with `CoverEntityFeature`.
- Fixed blocking `import_module` calls by moving to `async_setup_entry`.
- Updated manifest and repository links for new GitHub location: `https://github.com/Caine72/pcc-cover`.
- Reorganized README with clearer instructions and integration purpose.

### Removed
- Legacy YAML platform loading (`cover: - platform: pcc`).

---

