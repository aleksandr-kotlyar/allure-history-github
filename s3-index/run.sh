#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_WORKSPACE:?Missing GitHub workspace}"
: "${ALLURE_HISTORY_CORE_IMAGE:?Select a Core image containing allure-history-s3}"

case "${ALLURE_HISTORY_S3_PUBLISH}" in
  true|false) ;;
  *) echo "publish must be true or false" >&2; exit 1 ;;
esac

cd "$GITHUB_WORKSPACE"
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  printf 'public-dir=allure-navigation/public\nplan-path=allure-navigation/plan.json\n' >> "$GITHUB_OUTPUT"
fi

docker_args=(run --rm --user "$(id -u):$(id -g)"
  --volume "$GITHUB_WORKSPACE:$GITHUB_WORKSPACE"
  --workdir "$GITHUB_WORKSPACE" --env "HOME=$HOME")

# Preserve SDK configuration and temporary credentials without putting values in argv.
while IFS= read -r name; do
  case "$name" in
    AWS_*|ALLURE_HISTORY_*) docker_args+=(--env "$name") ;;
  esac
done < <(compgen -e)
if [ -d "$HOME/.aws" ]; then
  docker_args+=(--volume "$HOME/.aws:$HOME/.aws:ro")
fi
for name in AWS_CONFIG_FILE AWS_SHARED_CREDENTIALS_FILE AWS_WEB_IDENTITY_TOKEN_FILE AWS_CA_BUNDLE; do
  file="${!name:-}"
  if [[ "$file" = /* && -f "$file" ]]; then
    docker_args+=(--volume "$file:$file:ro")
  fi
done

docker "${docker_args[@]}" --entrypoint sh "$ALLURE_HISTORY_CORE_IMAGE" -ec '
  allure-history-s3 index \
    --s3-uri "$ALLURE_HISTORY_S3_URI" \
    --public-url "$ALLURE_HISTORY_S3_PUBLIC_URL" \
    --public-title "$ALLURE_HISTORY_PUBLIC_TITLE" \
    --output-dir allure-navigation
  if [ "$ALLURE_HISTORY_S3_PUBLISH" = true ]; then
    allure-history-s3 publish --plan allure-navigation/plan.json
  fi
'
