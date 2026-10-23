#!/usr/bin/env bash
# Build release artifacts:
#   dist/us-sleep-regulatory-v<version>.tar.gz
#   dist/us-sleep-regulatory-v<version>.zip
#   dist/SHA256SUMS
#   dist/catalog/index.json          (OpenCode HTTP catalog)
#   dist/catalog/us-sleep-regulatory/...
#   dist/catalog/checksums.json
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC="$ROOT"
VERSION="$(cat "$ROOT/VERSION" 2>/dev/null || echo "0.0.0")"
NAME="us-sleep-regulatory-v${VERSION}"
DIST="$ROOT/dist"

# Stage outside the skill directory so dist/ cannot copy itself.
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
PAYLOAD="$STAGE/us-sleep-regulatory"
mkdir -p "$PAYLOAD"

rm -rf "$DIST"
echo "Staging $NAME"
tar -C "$SKILL_SRC" \
  --exclude='.git' \
  --exclude='.github' \
  --exclude='.idea' \
  --exclude='dist' \
  --exclude='tools' \
  --exclude='tests' \
  --exclude='.gitignore' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='snapshots/*.json' \
  --exclude='snapshots/*.md' \
  -cf - . | tar -C "$PAYLOAD" -xf -

# Distribution files live at the repo root, not in the skill source.
for file in VERSION LICENSE CHANGELOG.md install.sh; do
  cp "$ROOT/$file" "$PAYLOAD/$file"
done

mkdir -p "$DIST"
tar -C "$STAGE" -czf "$DIST/$NAME.tar.gz" "us-sleep-regulatory"

if command -v zip >/dev/null 2>&1; then
  (cd "$STAGE" && zip -qr "$DIST/$NAME.zip" "us-sleep-regulatory")
else
  echo "WARNING: zip not found; skipping .zip" >&2
fi

# OpenCode HTTP catalog: <base>/index.json + <base>/us-sleep-regulatory/<file>
mkdir -p "$DIST/catalog/us-sleep-regulatory"
tar -C "$PAYLOAD" -cf - . | tar -C "$DIST/catalog/us-sleep-regulatory" -xf -
python3 "$ROOT/tools/build_catalog.py" "$DIST/catalog" "$VERSION"

(
  cd "$DIST"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$NAME.tar.gz" > SHA256SUMS
    [[ -f "$NAME.zip" ]] && sha256sum "$NAME.zip" >> SHA256SUMS
  else
    shasum -a 256 "$NAME.tar.gz" > SHA256SUMS
    [[ -f "$NAME.zip" ]] && shasum -a 256 "$NAME.zip" >> SHA256SUMS
  fi
)

echo
echo "Artifacts:"
ls -lh "$DIST"/"$NAME".* "$DIST"/SHA256SUMS 2>/dev/null || true
echo
echo "Catalog: $DIST/catalog"
echo "Install from the tarball:"
echo "  ./install.sh --from \"$DIST/$NAME.tar.gz\" --target opencode"
echo
echo "Host the catalog at https://your-host/skills/ and add to opencode.json:"
echo '  { "skills": ["https://your-host/skills/"] }'
