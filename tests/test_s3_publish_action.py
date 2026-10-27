import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_s3_action_passes_ci_context_credentials_grouping_and_outputs(tmp_path):
    workspace = tmp_path / "workspace with spaces"
    workspace.mkdir()
    output = tmp_path / "outputs"
    output.touch()
    cli = tmp_path / "allure-history-s3"
    cli.write_text(f'#!{sys.executable}\n'
                   'import json, os, sys\nfrom pathlib import Path\n'
                   'Path(os.environ["CLI_LOG"]).write_text(json.dumps(sys.argv[1:]))\n'
                   'with open(os.environ["GITHUB_OUTPUT"], "a") as stream:\n'
                   '    stream.write("report-url=https://reports.test/run/\\npublic-dir=allure-s3/public\\n")\n')
    cli.chmod(0o755)
    docker = tmp_path / "docker"
    docker.write_text(f'#!{sys.executable}\n'
                      'import json, os, subprocess, sys\nfrom pathlib import Path\n'
                      'Path(os.environ["DOCKER_LOG"]).write_text(json.dumps(sys.argv[1:]))\n'
                      'sys.exit(subprocess.run(["/bin/sh", "-ec", sys.argv[-1]]).returncode)\n')
    docker.chmod(0o755)
    env = {key: value for key, value in os.environ.items() if not key.startswith(("AWS_", "ALLURE_HISTORY_", "GITHUB_"))}
    env.update({"PATH": f"{tmp_path}:{env['PATH']}", "GITHUB_WORKSPACE": str(workspace),
                "GITHUB_OUTPUT": str(output), "GITHUB_REPOSITORY": "example/project", "GITHUB_RUN_ID": "123",
                "GITHUB_TOKEN": "synthetic-github-token", "AWS_ACCESS_KEY_ID": "synthetic-access",
                "AWS_SECRET_ACCESS_KEY": "synthetic-secret", "ALLURE_HISTORY_CORE_IMAGE": "core:test",
                "ALLURE_HISTORY_S3_URI": "s3://reports/team with spaces", "ALLURE_HISTORY_GROUP_PATH": "project/browser/main",
                "ALLURE_HISTORY_S3_PUBLIC_URL": "https://reports.test/base", "ALLURE_HISTORY_PUBLIC_TITLE": "Team reports",
                "REPORTS_TO_KEEP": "2", "ENV": "dev", "DOCKER_LOG": str(tmp_path / "docker.json"),
                "CLI_LOG": str(tmp_path / "cli.json")})
    result = subprocess.run(["bash", str(ROOT / "s3/run.sh")], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    args = json.loads((tmp_path / "docker.json").read_text())
    for name in ("GITHUB_REPOSITORY", "GITHUB_RUN_ID", "GITHUB_OUTPUT", "GITHUB_TOKEN", "AWS_ACCESS_KEY_ID",
                 "AWS_SECRET_ACCESS_KEY", "ALLURE_HISTORY_GROUP_PATH", "REPORTS_TO_KEEP", "ENV"):
        assert name in args
    assert "synthetic-secret" not in " ".join(args)
    assert "synthetic-github-token" not in " ".join(args)
    assert f"{output}:{output}" in args
    assert json.loads((tmp_path / "cli.json").read_text()) == [
        "publish-job", "--provider", "github", "--s3-uri", "s3://reports/team with spaces",
        "--public-url", "https://reports.test/base", "--public-title", "Team reports",
    ]
    assert "report-url=https://reports.test/run/" in output.read_text()


def test_s3_publisher_is_a_separate_action_with_generation_inputs():
    action = (ROOT / "s3/action.yml").read_text()
    for name in ("results-dir", "group-path", "reports-to-keep", "job-id", "comment-pr", "report-url"):
        assert f"  {name}:" in action
    assert "pages-branch:" not in action
    assert 'bash "$GITHUB_ACTION_PATH/run.sh"' in action
