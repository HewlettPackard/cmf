#!/usr/bin/env bash
###
# Copyright (2026) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###
#
# Commit running CMF containers to images, tag them for a Docker Hub
# organisation and push them.
#
#   docker container commit <container> <image>
#   docker tag <image>:<tag> <registry>/<image>:<tag>
#   docker push <registry>/<image>:<tag>

set -euo pipefail

REGISTRY="${DOCKER_REGISTRY:-hpecmf}"
TAG="${IMAGE_TAG:-latest}"
DRY_RUN=0
NO_COMMIT=0

# container name -> image name
declare -A SERVICES=(
  [server]=server
  [ui]=ui
  [mcp]=mcp
  [cmf-nginx]=cmf-nginx
  [postgres]=postgres
  [tensorboard]=tensorboard
)

usage() {
  cat <<EOF
Usage: $(basename "$0") [options] [container ...]

Commits the given running containers to local images, tags them as
<registry>/<image>:<tag> and pushes them to Docker Hub.

With no containers given, all known CMF containers are processed:
  ${!SERVICES[*]}

Options:
  -r, --registry NAME   Docker Hub org/user (default: ${REGISTRY})
  -t, --tag TAG         Image tag (default: ${TAG})
  -n, --dry-run         Print the commands without running them
      --no-commit       Skip 'docker container commit', tag/push existing images
  -h, --help            Show this help

Environment:
  DOCKER_REGISTRY, IMAGE_TAG override the defaults above.

Examples:
  $(basename "$0")
  $(basename "$0") ui-server
  $(basename "$0") -r myorg -t v1.2.0 cmf-server ui-server
EOF
}

run() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "+ $*"
  else
    echo "+ $*"
    "$@"
  fi
}

TARGETS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--registry) REGISTRY="$2"; shift 2 ;;
    -t|--tag)      TAG="$2"; shift 2 ;;
    -n|--dry-run)  DRY_RUN=1; shift ;;
    --no-commit)   NO_COMMIT=1; shift ;;
    -h|--help)     usage; exit 0 ;;
    -*)            echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    *)             TARGETS+=("$1"); shift ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed or not on PATH." >&2
  exit 1
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=("${!SERVICES[@]}")
fi

if ! docker system info --format '{{.ID}}' >/dev/null 2>&1; then
  echo "ERROR: cannot talk to the Docker daemon." >&2
  exit 1
fi

# 'docker push' needs credentials; fail early instead of mid-way through.
if [[ "${DRY_RUN}" -eq 0 ]] && ! docker system info 2>/dev/null | grep -q '^ *Username:'; then
  echo "WARNING: not logged in to a registry. Run 'docker login' if the push fails." >&2
fi

FAILED=()
PUSHED=()

for container in "${TARGETS[@]}"; do
  image_name="${SERVICES[$container]:-$container}"
  local_image="${image_name}:${TAG}"
  remote_image="${REGISTRY}/${image_name}:${TAG}"

  echo
  echo "=== ${container} -> ${remote_image} ==="

  if [[ "${NO_COMMIT}" -eq 0 ]]; then
    if ! docker container inspect "${container}" >/dev/null 2>&1; then
      echo "SKIP: container '${container}' not found (use --no-commit to tag an existing image)." >&2
      FAILED+=("${container}")
      continue
    fi
    if ! run docker container commit "${container}" "${local_image}"; then
      echo "ERROR: commit failed for '${container}'." >&2
      FAILED+=("${container}")
      continue
    fi
  elif ! docker image inspect "${local_image}" >/dev/null 2>&1; then
    echo "SKIP: image '${local_image}' not found locally." >&2
    FAILED+=("${container}")
    continue
  fi

  if ! run docker tag "${local_image}" "${remote_image}"; then
    echo "ERROR: tag failed for '${local_image}'." >&2
    FAILED+=("${container}")
    continue
  fi

  if ! run docker push "${remote_image}"; then
    echo "ERROR: push failed for '${remote_image}'." >&2
    FAILED+=("${container}")
    continue
  fi

  PUSHED+=("${remote_image}")
done

echo
echo "============================================================"
if [[ ${#PUSHED[@]} -gt 0 ]]; then
  echo "Pushed:"
  printf '  %s\n' "${PUSHED[@]}"
fi
if [[ ${#FAILED[@]} -gt 0 ]]; then
  echo "Failed:"
  printf '  %s\n' "${FAILED[@]}"
  echo "============================================================"
  exit 1
fi
echo "============================================================"
