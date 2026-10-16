#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="pd-test-$(date +%s)-$$"
REPORTS_DIR="$ROOT_DIR/reports"

LOCAL_UID="$(id -u)"
LOCAL_GID="$(id -g)"
export LOCAL_UID LOCAL_GID

mkdir -p "$REPORTS_DIR"
rm -f \
  "$REPORTS_DIR/backend.xml" \
  "$REPORTS_DIR/frontend-build.log" \
  "$REPORTS_DIR/frontend-checks.log"

compose=(
  docker compose
  --project-name "$PROJECT_NAME"
  --file "$ROOT_DIR/compose.ci.yaml"
)

cleanup() {
  local status=$?
  trap - EXIT

  "${compose[@]}" logs --no-color \
    > "$REPORTS_DIR/backend-containers.log" 2>&1 || true

  if ! "${compose[@]}" down --volumes --remove-orphans; then
    if [ "$status" -eq 0 ]; then
      status=1
    fi
  fi

  exit "$status"
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

"${compose[@]}" up \
  --build \
  --abort-on-container-exit \
  --exit-code-from tests \
  tests

"${compose[@]}" build frontend-checks \
  2>&1 | tee "$REPORTS_DIR/frontend-build.log"

"${compose[@]}" run --rm --no-deps frontend-checks \
  2>&1 | tee "$REPORTS_DIR/frontend-checks.log"
