#!/usr/bin/env bash
set -euo pipefail
umask 077

APP_DIR="${APP_DIR:-/opt/prisoners}"
AWS_REGION="${AWS_REGION:-us-east-2}"
BACKUP_BUCKET="${BACKUP_BUCKET:?Set BACKUP_BUCKET}"

mkdir -p "$APP_DIR/backups"
case "${1:-}" in
  "")
    exec 9> "$APP_DIR/.maintenance.lock"
    flock -w 300 9
    ;;
  --lock-held)
    # deploy.sh passes its already-locked file descriptor to avoid a nested lock.
    [[ "$(readlink /proc/self/fd/9)" == "$APP_DIR/.maintenance.lock" ]]
    flock -n 9
    ;;
  *)
    printf 'Usage: %s [--lock-held]\n' "$0" >&2
    exit 2
    ;;
esac

compose=(
  sudo -n docker compose
  --project-name prisoners-production
  --env-file "$APP_DIR/production.env"
  --file "$APP_DIR/compose.release.yaml"
)

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$(mktemp "$APP_DIR/backups/.backup-XXXXXX.dump")"
success_file=""
cleanup() {
  rm -f -- "$archive"
  if [[ -n "$success_file" ]]; then
    rm -f -- "$success_file"
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

"${compose[@]}" exec -T db \
  pg_dump -U prisoners -d prisoners_dilemma -Fc > "$archive"
test -s "$archive"
"${compose[@]}" exec -T db pg_restore --list < "$archive" > /dev/null

destination="s3://$BACKUP_BUCKET/production/prisoners-$timestamp.dump"
aws s3 cp "$archive" "$destination" --region "$AWS_REGION" --only-show-errors

success_file="$(mktemp "$APP_DIR/backups/.last-success-XXXXXX")"
printf '%s\n%s\n' "$timestamp" "$destination" > "$success_file"
mv -- "$success_file" "$APP_DIR/backups/last-success.txt"
success_file=""
printf 'Backup uploaded successfully: %s\n' "$destination"
