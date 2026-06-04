#!/usr/bin/env bash
# Verify the .NET toolchain is installed and can build/run a trivial app.
set -uo pipefail
fail=0

echo "🔧 Checking the .NET SDK..."
if command -v dotnet >/dev/null 2>&1; then
  ver="$(dotnet --version 2>/dev/null)"
  echo "  ✅ dotnet $ver"
  case "$ver" in
    8.*) : ;;
    *)   echo "  ⚠️  Expected an 8.x SDK; you have $ver. Most labs target net8.0." ;;
  esac
else
  echo "  ❌ 'dotnet' not found. Install the .NET 8 SDK (see README), open a new terminal."
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo
  echo "🛠  Building & running a throwaway console app..."
  tmp="$(mktemp -d)"
  if dotnet new console -o "$tmp/Hello" >/dev/null 2>&1 \
     && out="$(dotnet run --project "$tmp/Hello" 2>/dev/null)"; then
    echo "  ✅ ran: $out"
    [ "$out" = "Hello, World!" ] || echo "  ⚠️  unexpected output (still fine)"
  else
    echo "  ❌ could not create/run a console app — check 'dotnet --info'"
    fail=1
  fi
  rm -rf "$tmp"
fi

echo
echo "📝 Editor (informational):"
command -v code  >/dev/null 2>&1 && echo "  ✅ VS Code CLI 'code' found" || echo "  ℹ️  VS Code 'code' CLI not on PATH (optional)"

echo
if [ "$fail" -eq 0 ]; then
  echo "🎉 .NET is ready. Proceed to Module 01."
else
  echo "❗ Setup incomplete — see messages above and 00-setup/README.md."
  exit 1
fi
