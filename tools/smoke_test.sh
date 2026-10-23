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
PS_DEFAULT_VERSION="$(grep -oE '\$DefaultVersion = "[^"]+"' "$DIR/../install.ps1" | head -1 | cut -d'"' -f2)"
if [[ "$VERSION_FILE" != "$DEFAULT_VERSION" ]]; then
  echo "VERSION ($VERSION_FILE) != install.sh DEFAULT_VERSION ($DEFAULT_VERSION)" >&2
  exit 1
fi
if [[ "$VERSION_FILE" != "$PS_DEFAULT_VERSION" ]]; then
  echo "VERSION ($VERSION_FILE) != install.ps1 DefaultVersion ($PS_DEFAULT_VERSION)" >&2
  exit 1
fi
echo "VERSION $VERSION_FILE"

echo "== source health =="
"$PY" "$REG" doctor --format md

echo "== guidance registry =="
"$PY" "$REG" guidance --topic device --format md >/dev/null

echo "== local knowledge base (offline) =="
KBDIR="$(mktemp -d)"
export US_REG_KB="$KBDIR/kb.sqlite"
"$PY" "$REG" kb init --format md >/dev/null
HITS="$("$PY" "$REG" kb search "QVO predicate" --format json | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["count"])')"
[[ "$HITS" -gt 0 ]] || { echo "KB search returned no hits" >&2; exit 1; }
"$PY" "$REG" kb get cfr-21-882.5801 --format md >/dev/null
"$PY" "$REG" kb note add "test note" --title "Test note" --tags test --format json >/dev/null
"$PY" "$REG" kb export --jsonl --out "$KBDIR/export.jsonl"
test -s "$KBDIR/export.jsonl"
unset US_REG_KB
rm -rf "$KBDIR"
echo "KB OK: $HITS hits"

echo "== parallel kb refresh =="
KBDIR2="$(mktemp -d)"
US_REG_KB="$KBDIR2/kb.sqlite" "$PY" "$REG" kb refresh --jobs 4 --format md >/dev/null
COUNT2="$(US_REG_KB="$KBDIR2/kb.sqlite" "$PY" "$REG" kb stats --format json | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["documents"])')"
[[ "$COUNT2" -ge 50 ]] || { echo "parallel refresh produced only $COUNT2 docs" >&2; exit 1; }
rm -rf "$KBDIR2"
echo "parallel refresh OK: $COUNT2 docs"

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
assert len(ids[2]["result"]["tools"]) == 16
print("MCP OK: 16 tools")
'

echo "== installer (temp HOME, all clients) =="
TMPHOME="$(mktemp -d)"
trap 'rm -rf "$TMPHOME"' EXIT
HOME="$TMPHOME" bash "$INSTALL" --target all --no-doctor >/dev/null
test -f "$TMPHOME/.agents/skills/us-sleep-regulatory/SKILL.md"
test -f "$TMPHOME/.agents/skills/us-sleep-regulatory/README.ko.md"
test -f "$TMPHOME/.agents/skills/us-sleep-regulatory/install.ps1"
test -f "$TMPHOME/.agents/skills/us-sleep-regulatory/knowledge/seed/cfr-21-882.5801.md"
test -L "$TMPHOME/.claude/skills/us-sleep-regulatory"
test -L "$TMPHOME/.config/opencode/skills/us-sleep-regulatory"
test -f "$TMPHOME/.config/opencode/commands/us-sleep-regulatory.md"
"$PY" "$TMPHOME/.claude/skills/us-sleep-regulatory/scripts/reg.py" guidance --topic device --format md >/dev/null
US_REG_KB="$TMPHOME/kb.sqlite" "$PY" "$TMPHOME/.claude/skills/us-sleep-regulatory/scripts/reg.py" kb search "QVO" --format md >/dev/null
HOME="$TMPHOME" bash "$INSTALL" --target all --uninstall >/dev/null
test ! -e "$TMPHOME/.agents/skills/us-sleep-regulatory"
test ! -e "$TMPHOME/.claude/skills/us-sleep-regulatory"
test ! -e "$TMPHOME/.config/opencode/skills/us-sleep-regulatory"
test ! -e "$TMPHOME/.config/opencode/commands/us-sleep-regulatory.md"
echo "installer OK: Codex + Claude + OpenCode"

echo "SMOKE OK"
