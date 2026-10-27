# Allure History GitHub

Publish static Allure reports with persistent branch history to GitHub Pages.
Use this repository as a working example to fork, as a GitHub Action inside your
own job, or as a reusable workflow that handles the complete Pages deployment.

Report generation, history, retention, and indexes come from
[Allure History Core](https://github.com/aleksandr-kotlyar/allure-history-core).
The action runs a tested public GHCR image pinned by digest in `action.yml`.
This feature branch uses a Core feature runtime because release `2026.4.1`
does not yet support custom report groups or S3 publishing.
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

For existing reports in object storage, use the separate
[`s3-index` action](s3-index/action.yml) described below. Its inputs and runtime
are independent of the Pages action.

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

CI runs the local Docker action against an isolated bare Git repository, then
runs the workflow's `$/` reference to verify a second report restores history.
It checks both immutable snapshots, Allure trends, persistent storage, and
returned outputs. These checks do not deploy Pages or push report storage to
GitHub. Successful runs on the allowed publishing branch also deploy the demo.

Core owns the runtime image and its registry publication. Releases of this
repository pin a tested Core digest; forks can use that image unchanged.

## Generate and publish reports to S3

Use the separate `s3` action after your tests produce `allure-results`:

```yaml
- uses: aleksandr-kotlyar/allure-history-github/s3@RELEASE_TAG
  id: report
  with:
    s3-uri: s3://reports/team/project
    public-url: https://reports.example.test/team/project
    group-path: ${{ github.event.repository.name }}/${{ matrix.browser }}/${{ github.ref_name }}
    reports-to-keep: 30
```

Select an action revision containing `allure-history-s3 publish-job`; it pins a
compatible tested Core image. Configure AWS credentials before the action, through workload
identity, standard `AWS_*` variables, or shared configuration. S3-compatible
endpoints use `AWS_ENDPOINT_URL_S3` and the normal addressing-style configuration.
The Docker action forwards this configuration and the GitHub context by name.

Core restores the S3 tree, reuses group history, generates the new report, updates
navigation and `latest/`, then prunes old snapshots. No report-storage branch,
Git push permission, or GitHub Pages deployment is used. Outputs are `report-url`
and `public-dir` (the local restored tree). An empty `group-path` uses
`environment/branch`; group history and retention remain independent.

The optional `core-image` input overrides the tested runtime pin. Other inputs
are `results-dir` (`allure-results`), `environment` (`dev`),
`job-id` (artifact or run ID), `public-title` (`allure-history`), `show-intro`
(`false`), `comment-pr` (`false`), and `pull-request-number`. `github-token`
defaults to `github.token` and is used only for optional PR comments; those need
`pull-requests: write`. Basic publication requires no repository write permission.

Use a dedicated, non-root S3 prefix owned by this tree. All publishers must share
that prefix and lock, without independently publishing overlapping prefixes.
The whole prefix is downloaded before generation; large archives need time and
disk space. S3 writes are per object. See the
[Core publication contract](https://gitlab.com/aleksandr-kotlyar/allure-history-core/-/blob/s3-navigation-actions/README.md#publishing-reports-to-s3)
for failure and concurrency limits. The separate `s3-index` action below remains
available for navigation over reports generated elsewhere.

## Navigation for reports already in S3

The `s3-index` action uses Core to discover existing reports, prepare a local
navigation preview and optionally publish only the planned navigation objects.
It runs on Linux with Docker, including `ubuntu-24.04`. Supply an immutable Core
image containing `allure-history-s3` as `core-image`; Core release `2026.4.1`
does not contain the new command. There is no fallback to that older image.

Configure AWS credentials before this step, using workload identity, standard
`AWS_*` environment variables or shared AWS configuration files. The action
forwards that configuration to Core without accepting separate credential inputs.
For AWS, an earlier `aws-actions/configure-aws-credentials@v6` step can exchange
GitHub OIDC for temporary credentials; that requires `id-token: write` on the
caller job. A compatible storage provider can use its existing CI credentials.

```yaml
permissions:
  contents: read

jobs:
  navigation:
    runs-on: ubuntu-24.04
    steps:
      # Configure AWS credentials here, or use a runner with an existing identity.
      - uses: aleksandr-kotlyar/allure-history-github/s3-index@RELEASE_TAG
        with:
          core-image: ${{ vars.ALLURE_HISTORY_CORE_IMAGE }}
          s3-uri: s3://reports/team/project
          public-url: https://reports.example.test/team/project
          public-title: Project reports
          publish: 'false'
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_SESSION_TOKEN: ${{ secrets.AWS_SESSION_TOKEN }}
          AWS_DEFAULT_REGION: us-east-1
          AWS_ENDPOINT_URL_S3: ${{ vars.AWS_ENDPOINT_URL_S3 }}

      - uses: actions/upload-artifact@v7
        if: always()
        with:
          name: allure-navigation
          path: allure-navigation/
          include-hidden-files: true
```

For OIDC, omit the credential `env` entries above so the earlier credential
step's temporary values are inherited. `core-image`, `s3-uri`, and `public-url`
are required. `public-title` defaults to `allure-history`; `publish` and
`show-intro` default to `false`. The `No server / No external storage` banner
is hidden by default. Outputs are `public-dir` (the local preview) and
`plan-path`; retain the entire `allure-navigation/` directory for rollback,
including jobs that partially fail publication.

Paths stay as existing object keys. Groups can have any depth; numeric jobs,
timestamp reports and arbitrary report names with normal Allure markers are
supported. Both `history/` and `.history/` are excluded. `public-url` maps to the
selected prefix independently of the S3 API endpoint, so custom hosts and CDN
paths work. The standard AWS config supports endpoint and addressing-style
settings. The action mounts the workspace read/write and default `.aws` and
explicit configuration, web identity and CA files read-only.

With `publish: 'true'`, Core validates the preview and uses conditional writes
and a prefix lock. Reports, attachments and histories are preserved. There is
no report generation, retention, bucket-wide deletion, Git push or Pages
deployment. Use Core's `allure-history-s3 rollback --plan PATH/plan.json` with
the downloaded complete artifact to restore prior navigation. The endpoint must
enforce conditional PUT/DELETE; all publishers must agree on the same prefix.
See the [Core S3 contract](https://github.com/aleksandr-kotlyar/allure-history-core#existing-reports-in-s3)
for rollback and concurrency limits.

## Migration

New action-based releases pin Core in `action.yml`. The reusable workflow's
previous `core-ref` input is removed; callers select the publisher release tag.
Older tags keep their original workflow and inputs.
