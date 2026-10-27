# Allure History — GitHub Pages & S3

Publish static Allure reports with persistent history to GitHub Pages or S3.
Choose the action by its path:

| Destination | Action path |
| --- | --- |
| GitHub Pages | `aleksandr-kotlyar/allure-history-github/pages@REF` |
| S3 | `aleksandr-kotlyar/allure-history-github/s3@REF` |
| Navigation for existing S3 reports | `aleksandr-kotlyar/allure-history-github/s3-index@REF` |

Use a commit or release tag containing the selected action directory for `REF`.
Release `2026.4.1` predates these paths. S3 inputs are documented in
[`s3/action.yml`](s3/action.yml) and [`s3-index/action.yml`](s3-index/action.yml).

The examples below use GitHub Pages. Fork this repository as a working example,
add the Pages action to your own job, or call the complete publishing workflow.

Report generation, history, retention, and indexes come from
[Allure History Core](https://github.com/aleksandr-kotlyar/allure-history-core).
The Pages action runs a tested public GHCR image pinned by digest in `pages/action.yml`.
Consumers do not need registry credentials or a container build.

## Fork the example

1. Fork this public repository and enable GitHub Actions in your fork.
2. In **Settings → Pages**, choose **GitHub Actions** as the source.
3. Run **CI** from the Actions tab, or push to `master`/`main`.

The CI tests this checkout's Pages action, then calls the local reusable workflow.
That workflow references its own action using `$/pages`, so edits in your fork are
used at the same commit. The Core image remains the tested upstream image.
The workflow creates `gh-pages` in your repository and deploys your report:

```text
https://<owner>.github.io/<repository>/dev/<branch-slug>/latest/
```

Repository names and report URLs are derived from the caller's GitHub context.
Pull requests run tests and isolated action checks. After those checks pass,
PRs from branches in this repository also publish their report and create or
update one Allure comment on the PR. PRs from forks only run the checks because
their token cannot publish reports or write comments.

In **Settings → Environments → github-pages**, allow `refs/pull/*/merge` as a
deployment branch rule alongside `master`/`main` to enable PR publication.
Pushes to `master`/`main` and manual runs permitted by the environment continue
to deploy Pages.

This publisher owns the repository's entire Pages site. Use a dedicated report
repository if an existing Pages site must be preserved.

## Add the Pages action to an existing job

Replace `RELEASE_TAG` with a release containing `pages/action.yml`. Your test
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

      - uses: aleksandr-kotlyar/allure-history-github/pages@RELEASE_TAG
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
the `github-pages` environment. GitHub.com self repository references (`$/pages`)
ensure that the workflow uses the action from the selected workflow version.

## Inputs and outputs

| Action input | Default | Purpose |
| --- | --- | --- |
| `results-dir` | `allure-results` | Results directory in the caller workspace. |
| `environment` | `dev` | Report environment folder. |
| `group-path` | empty | Custom relative report group; otherwise `environment/branch-slug`. |
| `pages-branch` | `gh-pages` | Persistent report/history storage branch. |
| `reports-to-keep` | `30` | Snapshots retained per group. |
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

## Custom report groups

The action and reusable workflow accept `group-path`. Build it with GitHub
expressions; for example, in a browser matrix:

```yaml
with:
  group-path: ${{ github.event.repository.name }}/${{ matrix.browser }}/${{ github.ref_name }}
```

Core automatically creates this tree and places each `job_<id>/` inside its
group, alongside `history/` and `latest/`. Each exact path has independent history
and retention. Include the branch and project when they need separate histories.
Snapshot IDs must be unique in a group; publishing the same ID replaces that
snapshot. `$VARIABLE` strings are not expanded by the action; use expressions.

Omitting the input keeps `environment/branch-slug`. Changing it starts a new
group without moving existing reports. The path must be relative, with no
empty, `.` or `..` segments, backslashes, or reserved report/service names.
Spaces and Unicode are preserved and URL-encoded. See the
[Core group contract](https://github.com/aleksandr-kotlyar/allure-history-core#custom-report-groups)
for reserved names. Select an action revision containing this input and its
updated Core pin; older release tags retain their existing layout.

## Development

```bash
python3 -m pip install -r requirements.txt
pytest -m "not demo"
```

CI runs `./pages` against an isolated bare Git repository, then runs the workflow's
`$/pages` reference to verify a second report restores history.
It checks both immutable snapshots, Allure trends, persistent storage, and
returned outputs. These checks do not deploy Pages or push report storage to
GitHub. Successful runs on the allowed publishing branch also deploy the demo.

The root `action.yml` mirrors `pages/action.yml` for the GitHub Marketplace
listing. Tests check that both files stay identical.

Core owns the runtime image and its registry publication. Releases of this
repository pin a tested Core digest; forks can use that image unchanged.
