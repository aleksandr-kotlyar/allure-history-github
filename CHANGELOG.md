# Changelog

## Unreleased

### Changed

- Renamed the project to `allure-history-github` and aligned workflow names,
  report metadata, documentation, and issue links.
- Fetch the core from its public GitLab repository and pin `core-ref` to
  published release `2026.2.11` by default.
- Retain the existing PR comment marker so report comments update in place.

### Fixed

- Build the default Pages URL from standard GitHub repository variables.

### Migration

- Update caller workflow paths to `aleksandr-kotlyar/allure-history-github`.
  GitHub Actions does not redirect references to renamed repositories.
