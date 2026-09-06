# PCC Cover agent instructions

## Product scope

Communicate in English. PCC Cover is a private-use Home Assistant custom
integration that creates one template-backed cover per config entry. Keep the
integration compact and preserve UI-only configuration.

## Home Assistant conventions

- Follow current Home Assistant developer patterns and inspect the local Home
  Assistant Core checkout for version-sensitive APIs.
- Keep config entry setup unloadable and tie background work to the config entry
  or entity lifecycle.
- Keep `strings.json` and `translations/en.json` synchronized.
- Add focused tests for every production behavior change.
- Never store credentials, local paths, container IDs, or live acceptance output
  in the repository.

## Development workflow

1. Start from a clean, updated `main` and create a `codex/` branch.
2. Make the smallest complete change and add regression tests with it.
3. Run `./scripts/validate --fix`, `./scripts/validate`, and `git diff --check`.
4. Review the complete diff before reporting completion.
5. Before production deployment or release, deploy to the configured local Home
   Assistant instance and run `./scripts/run-real-ha-acceptance`.
6. Do not commit, push, merge, release, or deploy to production without explicit
   user authority.

## Environment

- Integration: `custom_components/pcc`
- Tests: `tests/components/pcc`
- Validation: `./scripts/validate`
- Local live acceptance: `./scripts/run-real-ha-acceptance`
- Release version: `custom_components/pcc/manifest.json`

## Validation and release

- Pull requests must pass HACS, Hassfest, and project validation.
- Releases are manual and stable-only. Keep unreleased work at the current
  manifest version until a dedicated release branch is requested.
- Keep no changelog file. Draft user-facing GitHub release notes outside the
  repository from the commits and diff since the latest stable release, then
  obtain approval before publication.
- Prepare versions with `./scripts/set-version X.Y.Z` on a dedicated release
  branch. Publish only with explicit authority and approved release notes.
- Keep GitHub Actions pinned to immutable commits.
