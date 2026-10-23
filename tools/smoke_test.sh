#!/usr/bin/env bash
# Smoke test for the us-sleep-regulatory skill.
#
# Default mode also checks the seven upstream sources and runs a network
# refresh. Use --offline in CI, on a plane, or when an FDA endpoint is down:
# syntax, version consistency, the registry, the local KB, the MCP handshake,
# the installer, and the unit tests all run without network access.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REG="$DIR/../scripts/reg.py"
MCP="$DIR/../scripts/mcp_server.py"
INSTALL="$DIR/../install.sh"
PY="${PYTHON:-python3}"

OFFLINE=0
for arg in "$@"; do
  case "$arg" in
    --offline) OFFLINE=1 ;;
    -h|--help)
      echo "usage: smoke_test.sh [--offline]"
      exit 0
      ;;
    *)
      echo "unknown option: $arg (try --help)" >&2
      exit 2
      ;;
  esac
done

echo "== syntax =="
"$PY" -m py_compile "$REG" "$MCP" "$DIR/build_catalog.py" "$DIR/validate_registry.py" "$DIR/check_freshness.py" "$DIR/eval_retrieval.py"

echo "== unit tests (offline) =="
"$PY" -m unittest discover -s "$DIR/../tests" -q

echo "== version consistency =="
VERSION_FILE="$(cat "$DIR/../VERSION")"
DEFAULT_VERSION="$(grep -oE 'DEFAULT_VERSION="[^"]+"' "$INSTALL" | head -1 | cut -d'"' -f2)"
PS_DEFAULT_VERSION="$(grep -oE '\$DefaultVersion = "[^"]+"' "$DIR/../install.ps1" | head -1 | cut -d'"' -f2)"
PY_VERSION="$(grep -oE '^VERSION = "[^"]+"' "$REG" | head -1 | cut -d'"' -f2)"
if [[ "$VERSION_FILE" != "$DEFAULT_VERSION" ]]; then
  echo "VERSION ($VERSION_FILE) != install.sh DEFAULT_VERSION ($DEFAULT_VERSION)" >&2
  exit 1
fi
if [[ "$VERSION_FILE" != "$PS_DEFAULT_VERSION" ]]; then
  echo "VERSION ($VERSION_FILE) != install.ps1 DefaultVersion ($PS_DEFAULT_VERSION)" >&2
  exit 1
fi
if [[ "$VERSION_FILE" != "$PY_VERSION" ]]; then
  echo "VERSION ($VERSION_FILE) != scripts/reg.py VERSION ($PY_VERSION)" >&2
  exit 1
fi
echo "VERSION $VERSION_FILE"

echo "== guidance registry =="
"$PY" "$DIR/validate_registry.py" "$DIR/../references/guidance-registry.json"
"$PY" "$REG" guidance --topic device --format md >/dev/null

echo "== reference freshness =="
"$PY" "$DIR/check_freshness.py"

if [[ "$OFFLINE" == 0 ]]; then
  echo "== source health =="
  "$PY" "$REG" doctor --format md
else
  echo "== source health: skipped (--offline) =="
fi

echo "== local knowledge base (offline) =="
KBDIR="$(mktemp -d)"
export US_REG_KB="$KBDIR/kb.sqlite"
"$PY" "$REG" kb init --format md >/dev/null
HITS="$("$PY" "$REG" kb search "QVO" --format json | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["count"])')"
[[ "$HITS" -gt 0 ]] || { echo "KB search returned no hits" >&2; exit 1; }
"$PY" "$REG" kb get cfr-21-882.5801 --format md >/dev/null
"$PY" "$REG" kb note add "test note" --title "Test note" --tags test --format json >/dev/null
"$PY" "$REG" kb export --jsonl --out "$KBDIR/export.jsonl"
test -s "$KBDIR/export.jsonl"
unset US_REG_KB
rm -rf "$KBDIR"
echo "KB OK: $HITS hits"

if [[ "$OFFLINE" == 0 ]]; then
  echo "== parallel kb refresh =="
  KBDIR2="$(mktemp -d)"
  US_REG_KB="$KBDIR2/kb.sqlite" "$PY" "$REG" kb refresh --jobs 4 --format md >/dev/null
  COUNT2="$(US_REG_KB="$KBDIR2/kb.sqlite" "$PY" "$REG" kb stats --format json | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["documents"])')"
  [[ "$COUNT2" -ge 50 ]] || { echo "parallel refresh produced only $COUNT2 docs" >&2; exit 1; }
  rm -rf "$KBDIR2"
  echo "parallel refresh OK: $COUNT2 docs"
else
  echo "== parallel kb refresh: skipped (--offline) =="
fi

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

echo "== retrieval eval =="
"$PY" "$DIR/eval_retrieval.py"

echo "== installer checksum =="
PKG_TMP="$(mktemp -d)"
tar -czf "$PKG_TMP/skill.tar.gz" -C "$DIR/.." \
  --exclude='.git' --exclude='dist' --exclude='__pycache__' --exclude='.idea' .
if command -v sha256sum >/dev/null 2>&1; then
  SHA256="$(sha256sum "$PKG_TMP/skill.tar.gz" | awk '{print $1}')"
else
  SHA256="$(shasum -a 256 "$PKG_TMP/skill.tar.gz" | awk '{print $1}')"
fi
CHECK_HOME="$(mktemp -d)"
HOME="$CHECK_HOME" bash "$INSTALL" --from "$PKG_TMP/skill.tar.gz" --sha256 "$SHA256" --target codex --no-doctor >/dev/null
test -f "$CHECK_HOME/.agents/skills/us-sleep-regulatory/SKILL.md" || {
  echo "checksum-verified install produced no skill" >&2
  exit 1
}
CHECK_HOME2="$(mktemp -d)"
if HOME="$CHECK_HOME2" bash "$INSTALL" --from "$PKG_TMP/skill.tar.gz" \
  --sha256 0000000000000000000000000000000000000000000000000000000000000000 \
  --target codex --no-doctor >/dev/null 2>&1; then
  echo "installer accepted a bad checksum" >&2
  exit 1
fi
rm -rf "$PKG_TMP" "$CHECK_HOME" "$CHECK_HOME2"
echo "installer checksum OK"

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
HOME="$TMPHOME" bash "$INSTALL" --target all --verify >/dev/null
mkdir -p "$TMPHOME/.cache/us-sleep-regulatory"
touch "$TMPHOME/.cache/us-sleep-regulatory/kb.sqlite"
HOME="$TMPHOME" US_REG_CACHE="$TMPHOME/.cache/us-sleep-regulatory" \
  US_REG_KB="$TMPHOME/.cache/us-sleep-regulatory/kb.sqlite" \
  bash "$INSTALL" --target all --uninstall --purge --yes >/dev/null
test ! -e "$TMPHOME/.agents/skills/us-sleep-regulatory"
test ! -e "$TMPHOME/.claude/skills/us-sleep-regulatory"
test ! -e "$TMPHOME/.config/opencode/skills/us-sleep-regulatory"
test ! -e "$TMPHOME/.config/opencode/commands/us-sleep-regulatory.md"
test ! -e "$TMPHOME/.cache/us-sleep-regulatory"
echo "installer OK: Codex + Claude + OpenCode (verify, purge)"

echo "SMOKE OK"
