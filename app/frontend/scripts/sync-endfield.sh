#!/usr/bin/env bash
# Re-vendor src/styles/endfield.css from the design-system source.
#
# The Endfield design system is maintained separately; this repo keeps a vendored
# copy under src/styles/ so a fresh clone builds offline. Point EF_SRC at your
# checkout (a path) or a raw URL and re-run after the design system changes.
#
#   EF_SRC=../../../endfield-design/endfield.css scripts/sync-endfield.sh
#   EF_SRC=https://example.com/endfield.css      scripts/sync-endfield.sh
set -euo pipefail
cd "$(dirname "$0")/.."

DEST="src/styles/endfield.css"
SRC="${EF_SRC:-}"

if [ -z "$SRC" ]; then
  echo "set EF_SRC to the design system's endfield.css (path or URL)" >&2
  exit 1
fi

if [ -f "$SRC" ]; then
  cp "$SRC" "$DEST"
else
  curl -fsSL "$SRC" -o "$DEST"
fi

echo "synced $DEST  (<- $SRC, $(wc -l < "$DEST") lines)"
