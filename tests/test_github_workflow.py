from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_action_runs_pinned_public_core_image():
    action = (PROJECT_ROOT / "action.yml").read_text(encoding="utf-8")

    assert "using: docker" in action
    assert "docker://ghcr.io/aleksandr-kotlyar/allure-history-core@sha256:" in action
    assert "/usr/local/bin/allure-history-github" in action
    assert "- publish-job" in action
    assert "GITHUB_TOKEN: ${{ inputs.github-token }}" in action
    assert "report-url:" in action
    assert "public-dir:" in action


def test_reusable_workflow_composes_its_own_action_and_pages():
    workflow = (PROJECT_ROOT / ".github/workflows/allure-history.yml").read_text(
        encoding="utf-8"
    )

    assert "uses: $/" in workflow
    assert "uses: actions/download-artifact@v8" in workflow
    assert "uses: actions/configure-pages@v6" in workflow
    assert "uses: actions/upload-pages-artifact@v5" in workflow
    assert "uses: actions/deploy-pages@v5" in workflow
    assert "path: ${{ steps.report.outputs.public-dir }}" in workflow
    assert "core-ref:" not in workflow
    assert "git clone" not in workflow
    assert "actions/setup-python" not in workflow
    assert "actions/setup-java" not in workflow
    assert "actions/setup-node" not in workflow


def test_project_ci_dogfoods_local_action_and_reusable_workflow():
    workflow = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(
        encoding="utf-8"
    )

    assert "uses: ./" in workflow
    assert "uses: $/" in workflow
    assert "uses: ./.github/workflows/allure-history.yml" in workflow
    assert "needs: [test_gate, action_smoke]" in workflow
    assert "if: github.event_name != 'pull_request'" in workflow
    assert "name: allure-results" in workflow
    assert "name: jobid" in workflow
