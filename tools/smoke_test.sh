#!/usr/bin/env bash
# Smoke test for the us-sleep-regulatory skill.
# Requires network access to openFDA, eCFR, Federal Register, ClinicalTrials.gov,
# PubMed, and accessdata.fda.gov.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REG="$DIR/../scripts/reg.py"
MCP="$DIR/../scripts/mcp_server.py"
INSTALL="$DIR/../install.sh"
PY="${PYTHON:-python3}"

echo "== syntax =="
"$PY" -m py_compile "$REG" "$MCP" "$DIR/build_catalog.py"

echo "== version consistency =="
VERSION_FILE="$(cat "$DIR/../VERSION")"
DEFAULT_VERSION="$(grep -oE 'DEFAULT_VERSION="[^"]+"' "$INSTALL" | head -1 | cut -d'"' -f2)"
if [[ "$VERSION_FILE" != "$DEFAULT_VERSION" ]]; then
  echo "VERSION ($VERSION_FILE) != install.sh DEFAULT_VERSION ($DEFAULT_VERSION)" >&2
  exit 1
fi
echo "VERSION $VERSION_FILE"

echo "== source health =="
"$PY" "$REG" doctor --format md

echo "== guidance registry =="
"$PY" "$REG" guidance --topic device --format md >/dev/null

echo "== MCP handshake =="
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | "$PY" "$MCP" \
  | "$PY" -c '
import json, sys
ids = {}
for line in sys.stdin:
    msg = json.loads(line)
    ids[msg.get("id")] = msg
assert ids[1]["result"]["serverInfo"]["name"] == "us-sleep-regulatory"
assert len(ids[2]["result"]["tools"]) == 10
print("MCP OK: 10 tools")
'

echo "== installer (temp HOME, all clients) =="
TMPHOME="$(mktemp -d)"
trap 'rm -rf "$TMPHOME"' EXIT
HOME="$TMPHOME" bash "$INSTALL" --target all --no-doctor >/dev/null
test -f "$TMPHOME/.agents/skills/us-sleep-regulatory/SKILL.md"
test -L "$TMPHOME/.claude/skills/us-sleep-regulatory"
test -L "$TMPHOME/.config/opencode/skills/us-sleep-regulatory"
"$PY" "$TMPHOME/.claude/skills/us-sleep-regulatory/scripts/reg.py" guidance --topic device --format md >/dev/null
HOME="$TMPHOME" bash "$INSTALL" --target all --uninstall >/dev/null
test ! -e "$TMPHOME/.agents/skills/us-sleep-regulatory"
test ! -e "$TMPHOME/.claude/skills/us-sleep-regulatory"
test ! -e "$TMPHOME/.config/opencode/skills/us-sleep-regulatory"
echo "installer OK: Codex + Claude + OpenCode"

echo "SMOKE OK"
