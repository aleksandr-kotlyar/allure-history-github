import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def run_action(tmp_path, publish, *, fail_publish=False):
    workspace = tmp_path / "workspace with spaces"
    workspace.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        f"#!{sys.executable}\n"
        "import json, os, subprocess, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['DOCKER_LOG']).write_text(json.dumps(sys.argv[1:]))\n"
        "sys.exit(subprocess.run(['/bin/sh', '-ec', sys.argv[-1]]).returncode)\n"
    )
    docker.chmod(0o755)
    cli = bin_dir / "allure-history-s3"
    cli.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "with open(os.environ['CLI_LOG'], 'a') as log: log.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "if sys.argv[1] == 'index':\n"
        "    Path('allure-navigation/public').mkdir(parents=True)\n"
        "    Path('allure-navigation/plan.json').write_text('{}')\n"
        "elif os.environ.get('FAIL_PUBLISH') == 'true': sys.exit(7)\n"
    )
    cli.chmod(0o755)
    home = tmp_path / "home"
    (home / ".aws").mkdir(parents=True)
    token = tmp_path / "identity token"
    token.write_text("synthetic-token")
    env = {name: value for name, value in os.environ.items()
           if not name.startswith(("AWS_", "ALLURE_HISTORY_"))}
    env.update({"PATH": f"{bin_dir}:{env['PATH']}", "HOME": str(home),
                "GITHUB_WORKSPACE": str(workspace), "GITHUB_OUTPUT": str(tmp_path / "outputs"),
                "ALLURE_HISTORY_CORE_IMAGE": "core:test", "ALLURE_HISTORY_S3_URI": "s3://reports/team with spaces",
                "ALLURE_HISTORY_S3_PUBLIC_URL": "https://reports.test/custom", "ALLURE_HISTORY_PUBLIC_TITLE": "Team reports",
                "ALLURE_HISTORY_S3_PUBLISH": publish, "ALLURE_HISTORY_SHOW_INTRO": "false",
                "AWS_ACCESS_KEY_ID": "synthetic-access", "AWS_SECRET_ACCESS_KEY": "synthetic-secret",
                "AWS_WEB_IDENTITY_TOKEN_FILE": str(token), "AWS_ENDPOINT_URL_S3": "https://storage.test",
                "DOCKER_LOG": str(tmp_path / "docker.json"), "CLI_LOG": str(tmp_path / "cli.jsonl"),
                "FAIL_PUBLISH": str(fail_publish).lower()})
    result = subprocess.run(["bash", str(ROOT / "s3-index/run.sh")], env=env,
                            capture_output=True, text=True)
    return result, workspace


@pytest.mark.parametrize("publish", ["false", "true"])
def test_action_delegates_to_core_and_preserves_standard_aws_configuration(tmp_path, publish):
    result, workspace = run_action(tmp_path, publish)
    assert result.returncode == 0, result.stderr
    args = json.loads((tmp_path / "docker.json").read_text())
    assert "AWS_ACCESS_KEY_ID" in args and "AWS_SECRET_ACCESS_KEY" in args
    assert "AWS_ENDPOINT_URL_S3" in args
    assert "synthetic-access" not in " ".join(args)
    assert "synthetic-secret" not in " ".join(args)
    assert f"{workspace}:{workspace}" in args
    assert f"{tmp_path}/home/.aws:{tmp_path}/home/.aws:ro" in args
    assert f"{tmp_path}/identity token:{tmp_path}/identity token:ro" in args
    commands = [json.loads(line) for line in (tmp_path / "cli.jsonl").read_text().splitlines()]
    assert commands[0] == ["index", "--s3-uri", "s3://reports/team with spaces", "--public-url",
                            "https://reports.test/custom", "--public-title", "Team reports",
                            "--output-dir", "allure-navigation"]
    assert commands[1:] == ([["publish", "--plan", "allure-navigation/plan.json"]] if publish == "true" else [])
    assert (workspace / "allure-navigation/plan.json").exists()
    assert "plan-path=allure-navigation/plan.json" in (tmp_path / "outputs").read_text()


def test_failed_publication_fails_action_and_preserves_recovery_files(tmp_path):
    result, workspace = run_action(tmp_path, "true", fail_publish=True)
    assert result.returncode == 7
    assert (workspace / "allure-navigation/plan.json").exists()


def test_invalid_publish_value_fails_before_docker_is_called(tmp_path):
    result, _ = run_action(tmp_path, "yes")
    assert result.returncode == 1
    assert not (tmp_path / "docker.json").exists()


def test_separate_action_defaults_to_preview_without_pages_permissions():
    action = (ROOT / "s3-index/action.yml").read_text()
    assert "  publish:\n" in action and "    default: 'false'" in action
    assert "  core-image:\n" in action and "    required: true" in action
    assert "  show-intro:\n" in action
    assert "pages:" not in action and "github-token:" not in action
    assert 'bash "$GITHUB_ACTION_PATH/run.sh"' in action
