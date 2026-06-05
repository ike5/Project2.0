#!/usr/bin/env bash
# Verify the Swift/Xcode toolchain and that the course's Swift package builds & tests.
set -uo pipefail
fail=0

echo "🔧 Checking Xcode / Swift toolchain..."
if command -v xcodebuild >/dev/null 2>&1; then
  echo "  ✅ $(xcodebuild -version | head -1)"
else
  echo "  ❌ xcodebuild not found — install Xcode from the App Store, then 'xcode-select --install'"
  fail=1
fi

if command -v swift >/dev/null 2>&1; then
  echo "  ✅ $(swift --version 2>/dev/null | head -1)"
else
  echo "  ❌ swift not found — install Xcode / command-line tools"
  fail=1
fi

echo
echo "📱 Available iOS simulators (first few):"
if command -v xcrun >/dev/null 2>&1; then
  xcrun simctl list devices available 2>/dev/null | grep -i iphone | head -3 || echo "  (none listed — install an iOS runtime in Xcode ▸ Settings ▸ Platforms)"
else
  echo "  ℹ️  xcrun not available"
fi

echo
echo "🧪 Building & testing FoundationKata..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KATA="${SCRIPT_DIR}/../../apps/FoundationKata"
if command -v swift >/dev/null 2>&1; then
  if ( cd "$KATA" && swift test >/tmp/kata-test.log 2>&1 ); then
    echo "  ✅ swift test passed"
  else
    echo "  ❌ swift test failed — see /tmp/kata-test.log"
    tail -5 /tmp/kata-test.log
    fail=1
  fi
else
  echo "  ⏭  skipped (no swift toolchain)"
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "🎉 Ready. Create a SwiftUI app (README step 3), then head to Module 01."
else
  echo "❗ Setup incomplete — see messages above and 00-setup/README.md."
  exit 1
fi
