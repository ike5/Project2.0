#!/usr/bin/env bash
# Challenge 12, task 4: idempotent user+group setup. Safe to re-run.
set -euo pipefail

user="${1:?usage: $0 <username>}"
group="devs"

# Create the group only if missing.
if getent group "$group" >/dev/null; then
  echo "group '$group' already exists"
else
  groupadd "$group"
  echo "created group '$group'"
fi

# Create the user only if missing.
if id "$user" >/dev/null 2>&1; then
  echo "user '$user' already exists"
else
  useradd -m -s /bin/bash "$user"
  echo "created user '$user'"
fi

# Ensure membership (adding an existing member is a harmless no-op).
usermod -aG "$group" "$user"
echo "ensured '$user' is in '$group'"
