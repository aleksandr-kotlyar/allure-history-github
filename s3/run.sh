#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_WORKSPACE:?Missing GitHub workspace}"
: "${ALLURE_HISTORY_CORE_IMAGE:?Select a Core runtime with S3 publish-job}"
cd "$GITHUB_WORKSPACE"

docker_args=(run --rm --user "$(id -u):$(id -g)"
  --volume "$GITHUB_WORKSPACE:$GITHUB_WORKSPACE"
  --workdir "$GITHUB_WORKSPACE" --env "HOME=$HOME")

# Forward credentials by name and preserve standard SDK/CI configuration paths.
while IFS= read -r name; do
  case "$name" in
    AWS_*|ALLURE_HISTORY_*|GITHUB_*|ENV|REPORTS_TO_KEEP) docker_args+=(--env "$name") ;;
  esac
done < <(compgen -e)
if [ -d "$HOME/.aws" ]; then
  docker_args+=(--volume "$HOME/.aws:$HOME/.aws:ro")
fi
for name in AWS_CONFIG_FILE AWS_SHARED_CREDENTIALS_FILE AWS_WEB_IDENTITY_TOKEN_FILE AWS_CA_BUNDLE GITHUB_EVENT_PATH; do
  file="${!name:-}"
  if [[ "$file" = /* && -f "$file" ]]; then
    docker_args+=(--volume "$file:$file:ro")
  fi
done
if [[ "${GITHUB_OUTPUT:-}" = /* ]]; then
  docker_args+=(--volume "$GITHUB_OUTPUT:$GITHUB_OUTPUT")
fi

docker "${docker_args[@]}" --entrypoint sh "$ALLURE_HISTORY_CORE_IMAGE" -ec '
  allure-history-s3 publish-job --provider github \
    --s3-uri "$ALLURE_HISTORY_S3_URI" \
    --public-url "$ALLURE_HISTORY_S3_PUBLIC_URL" \
    --public-title "$ALLURE_HISTORY_PUBLIC_TITLE"
'
