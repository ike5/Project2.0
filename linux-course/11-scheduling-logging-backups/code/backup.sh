#!/usr/bin/env bash
# A small, safe backup script for the scheduling lab.
# Usage: backup.sh <source-dir> <backup-dir>
set -euo pipefail

SRC="${1:?usage: backup.sh <source-dir> <backup-dir>}"
DEST="${2:?usage: backup.sh <source-dir> <backup-dir>}"

mkdir -p "$DEST"
stamp="$(date +%F_%H%M%S)"
archive="$DEST/backup-$stamp.tgz"

# Create a compressed archive of the source.
tar -czf "$archive" -C "$(dirname "$SRC")" "$(basename "$SRC")"

# Log to syslog so it shows up in the journal / /var/log.
logger -t backup "created $archive ($(du -h "$archive" | cut -f1))"
echo "backup written: $archive"

# Retention: keep only the 7 most recent backups.
ls -1t "$DEST"/backup-*.tgz 2>/dev/null | tail -n +8 | xargs -r rm -f
