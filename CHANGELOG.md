# Changelog

## Unreleased

### Added

- Docker action backed by a tested, immutable Core image from public GHCR.
- Action outputs for the immutable report URL and generated Pages directory.
- An isolated CI integration check that generates a real report and persists
  history through the same action used by consumers and forks.

### Changed

- CI now publishes reports and enables the existing PR comment update flow
  for pull requests from branches in the same repository after checks pass.
  Fork pull requests continue to run tests without publication.
- The reusable workflow delegates report publishing to this repository's action
  and keeps artifact downloads and GitHub Pages deployment as workflow steps.
- Core is pinned by image digest in `action.yml`; callers no longer select a
  source checkout with `core-ref`.

### Fixed

- Re-running publication uses a Pages artifact named for the current attempt,
  avoiding deployment failures caused by multiple artifacts with the same name.

## 2026.4.1 (2026-10-26)

### Changed

- Renamed the project to `allure-history-github` and aligned workflow names,
  report metadata, documentation, and issue links.
- Fetch the core from its public GitLab repository and pin `core-ref` to
  published release `2026.4.1` by default.
- Retain the existing PR comment marker so report comments update in place.

### Fixed

- Build the default Pages URL from standard GitHub repository variables.

### Migration

- Update caller workflow paths to `aleksandr-kotlyar/allure-history-github`.
  GitHub Actions does not redirect references to renamed repositories.
