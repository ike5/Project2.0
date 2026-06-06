#!/usr/bin/env bash
# Challenge 12, task 1: timestamped archive + retention.
set -euo pipefail

src="${1:?usage: $0 <source-dir> <dest-dir> [keep]}"
dest="${2:?usage: $0 <source-dir> <dest-dir> [keep]}"
keep="${3:-5}"

[[ -d "$src" ]] || { echo "error: '$src' is not a directory" >&2; exit 1; }
mkdir -p "$dest"

archive="$dest/$(basename "$src")-$(date +%F_%H%M%S).tgz"
tar -czf "$archive" -C "$(dirname "$src")" "$(basename "$src")"
echo "created $archive"

# Keep only the newest $keep archives for this source.
prefix="$dest/$(basename "$src")-"
ls -1t "${prefix}"*.tgz 2>/dev/null | tail -n +"$(( keep + 1 ))" | xargs -r rm -f
echo "retained newest $keep archive(s)"
