import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_reusable_workflow_delegates_report_generation_to_core():
    template = (PROJECT_ROOT / ".github/workflows/allure-history.yml").read_text(
        encoding="utf-8"
    )

    assert "git clone https://gitlab.com/aleksandr-kotlyar/allure-history-core.git .allure-history-core" in template
    assert "CORE_REF: ${{ inputs.core-ref }}" in template
    assert 'git -C .allure-history-core checkout --detach "$CORE_REF"' in template
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

    assert "uses: actions/download-artifact@v4" in workflow
    assert "uses: actions/configure-pages@v5" in workflow
    assert "uses: actions/upload-pages-artifact@v3" in workflow
    assert "uses: actions/deploy-pages@v4" in workflow
    assert 'default: gh-pages' in workflow
    assert 'default: allure-results' in workflow
    assert 'default: jobid' in workflow
    assert "default: 2026.4.1" in workflow
    assert 'PAGES_BASE_URL="https://${GITHUB_REPOSITORY_OWNER}.github.io/${GITHUB_REPOSITORY#*/}"' in workflow
    assert 'git clone --single-branch --branch "${PAGES_BRANCH}"' in workflow
    assert "output.report_url" in workflow
    assert 'const marker = "<!-- github-allure-history-report -->";' in workflow


def test_project_ci_dogfoods_reusable_workflow():
    workflow = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(
        encoding="utf-8"
    )

    assert "uses: ./.github/workflows/allure-history.yml" in workflow
    assert "needs: test_gate" in workflow
    assert "if: github.event_name != 'pull_request'" in workflow
    assert "name: allure-results" in workflow
    assert "name: jobid" in workflow
    assert "comment-pr: ${{ github.event_name == 'pull_request' }}" in workflow


def test_default_pages_url_uses_standard_github_environment():
    workflow = (PROJECT_ROOT / ".github/workflows/allure-history.yml").read_text(
        encoding="utf-8"
    )
    assignment = next(
        line.strip()
        for line in workflow.splitlines()
        if line.strip().startswith('PAGES_BASE_URL="https://')
    )
    url = subprocess.check_output(
        ["bash", "-eu", "-c", assignment + '\nprintf "%s" "$PAGES_BASE_URL"'],
        env={
            "GITHUB_REPOSITORY_OWNER": "example",
            "GITHUB_REPOSITORY": "example/allure-history-github",
        },
        text=True,
    )
    assert url == "https://example.github.io/allure-history-github"
