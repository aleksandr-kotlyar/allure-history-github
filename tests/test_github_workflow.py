from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_reusable_workflow_delegates_report_generation_to_core():
    template = (PROJECT_ROOT / ".github/workflows/allure-history.yml").read_text(
        encoding="utf-8"
    )

    assert "repository: aleksandr-kotlyar/core-allure-history" in template
    assert "ref: ${{ inputs.core-ref }}" in template
    assert "python3 .allure-history-core/allure_history.py build-report \\" in template
    assert "python3 .allure-history-core/allure_history.py slug \\" in template
    assert "--ci-type github" in template
    assert "--output-file allure-history-output.json" in template
    assert "allure generate" not in template
    assert "executor.json" not in template


def test_reusable_workflow_contains_github_pages_deploy_steps():
    workflow = (PROJECT_ROOT / ".github/workflows/allure-history.yml").read_text(
        encoding="utf-8"
    )

    assert "uses: actions/download-artifact@v8" in workflow
    assert "uses: actions/configure-pages@v6" in workflow
    assert "uses: actions/upload-pages-artifact@v5" in workflow
    assert "uses: actions/deploy-pages@v5" in workflow
    assert 'default: gh-pages' in workflow
    assert 'default: allure-results' in workflow
    assert 'default: jobid' in workflow
    assert "default: main" in workflow
    assert 'PAGES_BASE_URL="https://${GITHUB_REPOSITORY_OWNER}.github.io/${GITHUB_EVENT_REPOSITORY_NAME}"' in workflow
    assert 'git clone --single-branch --branch "${PAGES_BRANCH}"' in workflow
    assert "output.report_url" in workflow


def test_project_ci_dogfoods_reusable_workflow():
    workflow = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(
        encoding="utf-8"
    )

    assert "uses: ./.github/workflows/allure-history.yml" in workflow
    assert "needs: test_gate" in workflow
    assert "name: allure-results" in workflow
    assert "name: jobid" in workflow
    assert "comment-pr: ${{ github.event_name == 'pull_request' }}" in workflow
