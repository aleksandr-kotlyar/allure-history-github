# Allure History GitHub

Publish Allure reports with preserved history to GitHub Pages using GitHub Actions and static files. No report server, database, web framework, or external storage service is required.

## Scope

This project publishes Allure report history to GitHub Pages using static files only. It is designed for GitHub Actions projects, immutable per-run report snapshots, stable branch-level `latest/` aliases, and lightweight pull request report links.

It is not a test management system, ReportPortal replacement, backend service, database-backed analytics platform, or generic multi-CI report publisher.

## Quick Start

Enable GitHub Pages for the repository with the source set to `GitHub Actions`, then call the reusable workflow after a test job uploads `allure-results`:

```yaml
name: Test And Publish

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: write
  pages: write
  id-token: write
  pull-requests: write

jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: |
          pytest --alluredir=allure-results
          echo "${GITHUB_RUN_ID}" > jobid
      - uses: actions/upload-artifact@v7
        with:
          name: allure-results
          path: allure-results
      - uses: actions/upload-artifact@v7
        with:
          name: jobid
          path: jobid

  publish-allure-history:
    needs: test
    uses: aleksandr-kotlyar/allure-history-github/.github/workflows/allure-history.yml@2026.4.1
    with:
      environment: dev
      pages-branch: gh-pages
      reports-to-keep: 30
      allure-results-artifact: allure-results
      job-id-artifact: jobid
      comment-pr: ${{ github.event_name == 'pull_request' }}
      pull-request-number: ${{ github.event.pull_request.number || '' }}
```

The reusable workflow downloads the uploaded artifacts, restores the previous branch history from `gh-pages`, generates a new immutable report snapshot, updates `latest/`, commits the refreshed `public/` tree back to the storage branch, and deploys the same content to GitHub Pages.

Report generation is delegated to
[`allure-history-core`](https://gitlab.com/aleksandr-kotlyar/allure-history-core).
The workflow checks out the public GitLab core release selected by `core-ref`
(default `2026.4.1`). It does not require access to the GitHub core mirror.
Pin a release tag or commit in production workflows.

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `environment` | `dev` | Report environment folder under `public/`. |
| `pages-branch` | `gh-pages` | Persistent storage branch for generated Pages content and Allure history. |
| `reports-to-keep` | `30` | Report snapshots retained per environment and branch. |
| `allure-results-artifact` | `allure-results` | Artifact name containing `allure-results/`. |
| `job-id-artifact` | `jobid` | Optional artifact name containing a `jobid` file. |
| `pages-base-url` | inferred | Optional explicit Pages base URL. |
| `comment-pr` | `false` | Post or update a pull request comment with the immutable report URL. |
| `pull-request-number` | empty | Pull request number used for comments. |
| `core-ref` | `2026.4.1` | Allure History Core release tag or commit from GitLab. |

## Report Storage Layout

Reports are persisted in the `gh-pages` storage branch:

```text
public/
  index.html
  {environment}/
    index.html
    {branch-slug}/
      index.html
      latest/
        index.html
      history/
      job_NNN/
```

- `latest/` redirects to the newest immutable `job_NNN/` snapshot.
- `history/` is reused by the next run to preserve Allure trends.
- Branch folders are slugged from `github.head_ref` or `github.ref_name` to keep URLs stable and safe.

## Compatibility

| Area | Status | Notes |
| --- | ---: | --- |
| GitHub Actions | Supported | Primary target. |
| GitHub Pages | Supported | Reports are published as static Pages content. |
| Allure Report 2 | Supported | Current target format. |
| GitLab CI/CD | Out of scope | This variant is GitHub-native. |

## Development

Local tests:

```bash
git clone git@github.com:aleksandr-kotlyar/allure-history-github.git
cd allure-history-github
python3 -m pip install -r requirements.txt
pytest
```

GitHub Actions runs contract tests for pull requests. Pushes to `master` or
`main`, and manual workflow runs, also publish the demo through the reusable
workflow. Configure GitHub Pages with the `GitHub Actions` source before
running the demo publication.

## Migration

Update caller `uses:` paths to `aleksandr-kotlyar/allure-history-github` when
adopting the rename. Repository redirects do not preserve Actions references.
