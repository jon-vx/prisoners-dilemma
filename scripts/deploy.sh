#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

release_tag="${1:?Usage: deploy.sh RELEASE_TAG}"
if [[ ! "$release_tag" =~ ^[0-9a-f]{40}-[0-9]+$ ]]; then
  printf 'Invalid release tag; expected full Git SHA followed by build number.\n' >&2
  exit 2
fi

APP_DIR="${APP_DIR:-/opt/prisoners}"
AWS_REGION="${AWS_REGION:-us-east-2}"
ECR_REGISTRY="${ECR_REGISTRY:-404268098300.dkr.ecr.us-east-2.amazonaws.com}"
BACKUP_BUCKET="${BACKUP_BUCKET:-pd-backups-404268098300}"
FRONTEND_URL="${FRONTEND_URL:-https://3-17-7-24.sslip.io}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
release_dir="$(dirname -- "$script_dir")"

test -f "$APP_DIR/production.env"
test -f "$APP_DIR/compose.release.yaml"
test -f "$release_dir/compose.release.yaml"
test -f "$script_dir/backup.sh"
test -f "$script_dir/deployment_check.py"

exec 9> "$APP_DIR/.maintenance.lock"
flock -w 300 9

docker_config="$(mktemp -d)"
trap 'rm -rf -- "$docker_config"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

compose=(
  sudo -n env "RELEASE_TAG=$release_tag" "ECR_REGISTRY=$ECR_REGISTRY"
  docker --config "$docker_config" compose
  --project-name prisoners-production
  --env-file "$APP_DIR/production.env"
  --file "$release_dir/compose.release.yaml"
)

phase="configuration validation"
on_error() {
  local status=$?
  trap - ERR
  printf 'Deployment failed during %s (exit %s). Inspect logs before recovery; no automatic database downgrade was attempted.\n' "$phase" "$status" >&2
  "${compose[@]}" logs --no-color --tail 60 api frontend >&2 || true
  exit "$status"
}
trap on_error ERR

"${compose[@]}" config --quiet
phase="registry login and image pull"
aws ecr get-login-password --region "$AWS_REGION" |
  sudo -n docker --config "$docker_config" login \
    --username AWS --password-stdin "$ECR_REGISTRY"
"${compose[@]}" pull api frontend

phase="database readiness"
# Preserve the running database container and volume during application releases.
"${compose[@]}" up --no-recreate --wait --wait-timeout 120 db

phase="application drain and backup"
"${compose[@]}" stop --timeout 60 frontend api
APP_DIR="$APP_DIR" AWS_REGION="$AWS_REGION" BACKUP_BUCKET="$BACKUP_BUCKET" \
  bash "$script_dir/backup.sh" --lock-held

phase="database migrations"
timeout 120 "${compose[@]}" run --rm --no-deps api alembic upgrade head

phase="application startup"
"${compose[@]}" up --no-deps --wait --wait-timeout 120 api frontend

phase="deployment check"
python3 "$script_dir/deployment_check.py" \
  --api-url http://127.0.0.1:8000/api/v1 \
  --frontend-url "$FRONTEND_URL"

phase="successful release recording"
# Persist the selected tag for scheduled backups and future operator commands.
python3 - "$APP_DIR" "$release_tag" <<'PY'
from pathlib import Path
import os
import tempfile
import sys

app_dir = Path(sys.argv[1])
path = app_dir / "production.env"
lines = path.read_text().splitlines()
previous = next((line.split("=", 1)[1] for line in lines if line.startswith("RELEASE_TAG=")), "unknown")
lines = [line for line in lines if not line.startswith("RELEASE_TAG=")]
lines.append(f"RELEASE_TAG={sys.argv[2]}")
fd, temp = tempfile.mkstemp(prefix=".production-", dir=app_dir)
try:
    with os.fdopen(fd, "w") as file:
        file.write("\n".join(lines) + "\n")
    (app_dir / "previous-release.txt").write_text(previous + "\n")
    os.replace(temp, path)
finally:
    if os.path.exists(temp):
        os.unlink(temp)
PY
cp -- "$release_dir/compose.release.yaml" "$APP_DIR/.compose.release.yaml.new"
mv -- "$APP_DIR/.compose.release.yaml.new" "$APP_DIR/compose.release.yaml"
printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$release_tag" >> "$APP_DIR/releases.log"
printf 'Deployment verified successfully: %s\n' "$release_tag"
