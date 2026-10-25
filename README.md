# Allure History GitHub

Publish static Allure reports with persistent branch history to GitHub Pages.
Use this repository as a working example to fork, as a GitHub Action inside your
own job, or as a reusable workflow that handles the complete Pages deployment.

Report generation, history, retention, and indexes come from
[Allure History Core](https://github.com/aleksandr-kotlyar/allure-history-core).
The action runs a tested public GHCR image pinned by digest in `action.yml`.
Consumers do not need registry credentials or a container build.

## Fork the example

1. Fork this public repository and enable GitHub Actions in your fork.
2. In **Settings → Pages**, choose **GitHub Actions** as the source.
3. Run **CI** from the Actions tab, or push to `master`/`main`.

The CI tests this checkout's action, then calls the local reusable workflow.
That workflow references its own action using `$/`, so edits in your fork are
used at the same commit. The Core image remains the tested upstream image.
The workflow creates `gh-pages` in your repository and deploys your report:

```text
https://<owner>.github.io/<repository>/dev/<branch-slug>/latest/
```

Repository names and report URLs are derived from the caller's GitHub context.
Pull requests run tests and isolated action checks; the example deploys Pages
only on pushes to `master`/`main` and manual runs permitted by the environment.

This publisher owns the repository's entire Pages site. Use a dedicated report
repository if an existing Pages site must be preserved.

## Add the action to an existing job

Replace `RELEASE_TAG` with a release containing `action.yml`. Your test
requirements must include `allure-pytest` to produce `allure-results`.

```yaml
name: Test And Publish

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  test-and-publish:
    runs-on: ubuntu-24.04
    environment:
      name: github-pages
      url: ${{ steps.deploy.outputs.page_url }}
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest --alluredir=allure-results

      - uses: aleksandr-kotlyar/allure-history-github@RELEASE_TAG
        id: report
        with:
          results-dir: allure-results
          environment: dev
          reports-to-keep: 30

      - uses: actions/configure-pages@v6
      - uses: actions/upload-pages-artifact@v5
        with:
          path: ${{ steps.report.outputs.public-dir }}
      - uses: actions/deploy-pages@v5
        id: deploy
```

The action restores history, creates an immutable report, updates `latest/`,
commits the retained `public/` tree to `gh-pages`, and returns its paths. The
following Pages steps upload and deploy that same tree.

The Docker action targets Linux AMD64 runners, including `ubuntu-24.04`.

## Use the complete reusable workflow

If tests run in a separate job, upload an artifact named `allure-results` with
`actions/upload-artifact@v7`, then call the reusable workflow:

```yaml
jobs:
  publish-allure-history:
    needs: tests
    permissions:
      contents: write
      pages: write
      id-token: write
    uses: aleksandr-kotlyar/allure-history-github/.github/workflows/allure-history.yml@RELEASE_TAG
    with:
      environment: dev
      reports-to-keep: 30
```

Enable Pages with the `GitHub Actions` source and allow the publishing branch in
the `github-pages` environment. GitHub.com self repository references (`$/`)
ensure that the workflow uses the action from the selected workflow version.

## Inputs and outputs

| Action input | Default | Purpose |
| --- | --- | --- |
| `results-dir` | `allure-results` | Results directory in the caller workspace. |
| `environment` | `dev` | Report environment folder. |
| `pages-branch` | `gh-pages` | Persistent report/history storage branch. |
| `reports-to-keep` | `30` | Snapshots retained per environment and branch. |
| `job-id` | artifact or run ID | Optional snapshot ID; otherwise uses `.artifacts/jobid/jobid` or `GITHUB_RUN_ID`. |
| `pages-base-url` | inferred | Explicit base URL for a custom Pages domain. |
| `github-token` | `github.token` | Token with `contents: write` for storage pushes. |
| `comment-pr` | `false` | Enable a PR report comment; also requires `pull-requests: write`. |
| `pull-request-number` | empty | PR number to comment on. |

The reusable workflow accepts the shared publishing inputs above, except
`results-dir`, `job-id`, and `github-token`. Instead, it downloads
`allure-results-artifact` (default `allure-results`) and optional
`job-id-artifact` (default `jobid`), and uses the caller's `GITHUB_TOKEN`.

| Action output | Purpose |
| --- | --- |
| `report-url` | Immutable URL of this run's report. |
| `public-dir` | Generated directory passed to `actions/upload-pages-artifact`. |

## Storage

```text
public/
  index.html
  <environment>/
    <branch-slug>/
      index.html
      latest/
      history/
      job_<id>/
```

Each run restores the branch's history, creates a new snapshot, refreshes the
`latest/` redirect, and applies retention. The persistent `gh-pages` branch is
created on the first run. Push access to that branch is required.

## Development

```bash
python3 -m pip install -r requirements.txt
pytest -m "not demo"
```

CI runs the local Docker action against an isolated bare Git repository, then
runs the workflow's `$/` reference to verify a second report restores history.
It checks both immutable snapshots, Allure trends, persistent storage, and
returned outputs. These checks do not deploy Pages or push report storage to
GitHub. Successful runs on the allowed publishing branch also deploy the demo.

Core owns the runtime image and its registry publication. Releases of this
repository pin a tested Core digest; forks can use that image unchanged.

## Migration

New action-based releases pin Core in `action.yml`. The reusable workflow's
previous `core-ref` input is removed; callers select the publisher release tag.
Older tags keep their original workflow and inputs.
