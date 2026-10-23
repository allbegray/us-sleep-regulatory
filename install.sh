#!/usr/bin/env bash
# Install the US Sleep Regulatory skill for Codex, Claude Code, and OpenCode.
#
# Shared install (recommended):
#   ./install.sh
#   -> real files in ~/.agents/skills/us-sleep-regulatory
#   -> symlinks in ~/.claude/skills and ~/.config/opencode/skills
#
# Individual clients:
#   ./install.sh --target codex
#   ./install.sh --target claude
#   ./install.sh --target opencode
#
# Project-local:
#   ./install.sh --target project
#   -> .agents/skills (Codex) + .claude/skills + .opencode/skills symlinks
#
# From a release tarball or URL:
#   ./install.sh --from ./us-sleep-regulatory-v1.0.0.tar.gz --target all
#   curl -fsSL https://example.com/install.sh \
#     | US_SLEEP_REG_REPO=org/repo bash -s -- --target all
#
# Uninstall:
#   ./install.sh --target all --uninstall
set -euo pipefail

SKILL_NAME="us-sleep-regulatory"
SKILL_DISPLAY="US Sleep Regulatory"
DEFAULT_VERSION="1.1.0"
REPO_SLUG="${US_SLEEP_REG_REPO:-}"
VERSION="${US_SLEEP_REG_VERSION:-$DEFAULT_VERSION}"
if [[ -n "${US_SLEEP_REG_TARBALL:-}" ]]; then
  RELEASE_TARBALL="$US_SLEEP_REG_TARBALL"
elif [[ -n "$REPO_SLUG" ]]; then
  RELEASE_TARBALL="https://github.com/${REPO_SLUG}/archive/refs/tags/v${VERSION}.tar.gz"
else
  RELEASE_TARBALL=""
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
SRC_DIR=""
REAL_DEST=""
LINKS=()
TMP_DIRS=()
SNAPSHOT_BACKUP=""
TARGET="all"
FROM=""
FORCE=0
RUN_DOCTOR=1
UNINSTALL=0

cleanup() {
  local dir
  for dir in "${TMP_DIRS[@]:-}"; do
    [[ -n "$dir" ]] && rm -rf "$dir"
  done
  return 0
}
trap cleanup EXIT

usage() {
  cat <<EOF
US Sleep Regulatory installer v${VERSION}

Usage:
  install.sh [options]

Targets:
  all         Shared install for Codex, Claude Code, and OpenCode. Default.
  auto        Shared install; link Claude/OpenCode only when their config
              directories already exist.
  codex       ~/.agents/skills/us-sleep-regulatory
  claude      ~/.claude/skills/us-sleep-regulatory
  opencode    ~/.config/opencode/skills/us-sleep-regulatory
  project     ./.opencode/skills + ./.agents/skills + ./.claude/skills links
  codex-legacy  ~/.codex/skills/us-sleep-regulatory (older Codex builds)
  PATH        An explicit directory (no symlinks)

Options:
  --target TARGET       See above. Default: all.
  --from PATH_OR_URL    Install from a local directory or a .tar.gz URL.
  --force               Overwrite an existing installation or link.
  --no-doctor           Skip the post-install source health check.
  --uninstall           Remove the installed skill from the selected target.
  -h, --help            Show this help.

Environment:
  US_SLEEP_REG_REPO     GitHub org/repo for the release tarball. Required when
                        the script is piped and no local SKILL.md exists.
  US_SLEEP_REG_VERSION  Version to download (default ${DEFAULT_VERSION}).
  US_SLEEP_REG_TARBALL  Explicit tarball URL (overrides repo/version).

Examples:
  ./install.sh
  ./install.sh --target all --force
  ./install.sh --target project
  ./install.sh --from ./dist/us-sleep-regulatory-v1.0.0.tar.gz --target claude
  ./install.sh --target all --uninstall
EOF
}

die() { echo "ERROR: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || die "--target needs a value"
      TARGET="$2"; shift 2 ;;
    --target=*) TARGET="${1#*=}"; shift ;;
    --from)
      [[ $# -ge 2 ]] || die "--from needs a value"
      FROM="$2"; shift 2 ;;
    --from=*) FROM="${1#*=}"; shift ;;
    --force) FORCE=1; shift ;;
    --no-doctor) RUN_DOCTOR=0; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

check_python() {
  command -v python3 >/dev/null 2>&1 || die "python3 is required (3.9+)"
  python3 - <<'PY' || die "Python 3.9+ is required"
import sys
if sys.version_info < (3, 9):
    raise SystemExit(1)
PY
}

pick_src_dir() {
  local base="$1"
  if [[ -f "$base/skills/us-sleep-regulatory/SKILL.md" ]]; then
    printf '%s\n' "$base/skills/us-sleep-regulatory"
  elif [[ -f "$base/SKILL.md" ]]; then
    printf '%s\n' "$base"
  fi
}

resolve_src() {
  if [[ -n "$FROM" ]]; then
    if [[ -d "$FROM" ]]; then
      local resolved
      resolved="$(pick_src_dir "$(cd "$FROM" && pwd)")"
      [[ -n "$resolved" ]] || die "SKILL.md not found under $FROM"
      SRC_DIR="$resolved"
    elif [[ -f "$FROM" ]]; then
      local tmp found
      tmp="$(mktemp -d)"
      TMP_DIRS+=("$tmp")
      tar -xzf "$FROM" -C "$tmp"
      found="$(find "$tmp" -maxdepth 4 -name SKILL.md -print -quit)"
      [[ -n "$found" ]] || die "SKILL.md not found in $FROM"
      SRC_DIR="$(dirname "$found")"
    else
      local tmp found
      tmp="$(mktemp -d)"
      TMP_DIRS+=("$tmp")
      echo "Downloading $FROM ..."
      curl -fsSL "$FROM" | tar -xz -C "$tmp"
      found="$(find "$tmp" -maxdepth 4 -name SKILL.md -print -quit)"
      [[ -n "$found" ]] || die "SKILL.md not found in $FROM"
      SRC_DIR="$(dirname "$found")"
    fi
  else
    local resolved=""
    [[ -n "$SCRIPT_DIR" ]] && resolved="$(pick_src_dir "$SCRIPT_DIR")"
    if [[ -n "$resolved" ]]; then
      SRC_DIR="$resolved"
    else
      [[ -n "$RELEASE_TARBALL" ]] || die "no local SKILL.md found. Set US_SLEEP_REG_REPO=org/repo, set US_SLEEP_REG_TARBALL=url, or use --from."
      local tmp found
      tmp="$(mktemp -d)"
      TMP_DIRS+=("$tmp")
      echo "Downloading $RELEASE_TARBALL ..."
      curl -fsSL "$RELEASE_TARBALL" | tar -xz -C "$tmp" || die "download failed: $RELEASE_TARBALL"
      found="$(find "$tmp" -maxdepth 4 -name SKILL.md -print -quit)"
      [[ -n "$found" ]] || die "SKILL.md not found in the downloaded archive"
      SRC_DIR="$(dirname "$found")"
    fi
  fi
  [[ -f "$SRC_DIR/SKILL.md" ]] || die "SKILL.md not found in $SRC_DIR"
}

resolve_paths() {
  local claude_dir="$HOME/.claude"
  local opencode_dir="$HOME/.config/opencode"

  case "$TARGET" in
    auto)
      REAL_DEST="$HOME/.agents/skills/$SKILL_NAME"
      LINKS=()
      [[ -d "$claude_dir" ]] && LINKS+=("$claude_dir/skills/$SKILL_NAME")
      [[ -d "$opencode_dir" ]] && LINKS+=("$opencode_dir/skills/$SKILL_NAME")
      ;;
    all)
      REAL_DEST="$HOME/.agents/skills/$SKILL_NAME"
      LINKS=(
        "$claude_dir/skills/$SKILL_NAME"
        "$opencode_dir/skills/$SKILL_NAME"
      )
      ;;
    codex)
      REAL_DEST="$HOME/.agents/skills/$SKILL_NAME"
      LINKS=()
      ;;
    codex-legacy)
      REAL_DEST="$HOME/.codex/skills/$SKILL_NAME"
      LINKS=()
      ;;
    claude)
      REAL_DEST="$claude_dir/skills/$SKILL_NAME"
      LINKS=()
      ;;
    opencode)
      REAL_DEST="$opencode_dir/skills/$SKILL_NAME"
      LINKS=()
      ;;
    project)
      REAL_DEST="$PWD/.opencode/skills/$SKILL_NAME"
      LINKS=(
        "$PWD/.agents/skills/$SKILL_NAME"
        "$PWD/.claude/skills/$SKILL_NAME"
      )
      ;;
    *)
      REAL_DEST="$TARGET"
      LINKS=()
      ;;
  esac

  case "$REAL_DEST" in
    ""|"/"|"$HOME"|"$HOME/") die "refusing to use an unsafe destination: $REAL_DEST" ;;
  esac
}

copy_tree() {
  local src="$1" dest="$2"
  mkdir -p "$dest"
  tar -C "$src" \
    --exclude='.git' \
    --exclude='.github' \
    --exclude='dist' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='snapshots/*.json' \
    --exclude='snapshots/*.md' \
    -cf - . | tar -C "$dest" -xf -
}

copy_dist_files() {
  local dest="$1" file
  for file in README.md README.ko.md LICENSE CHANGELOG.md VERSION install.sh; do
    if [[ -f "$SRC_DIR/$file" ]]; then
      cp -f "$SRC_DIR/$file" "$dest/$file"
    elif [[ -f "$SCRIPT_DIR/$file" ]]; then
      cp -f "$SCRIPT_DIR/$file" "$dest/$file"
    fi
  done
}

relative_link() {
  python3 - "$1" "$2" <<'PY'
import os
import sys
target, link = sys.argv[1], sys.argv[2]
print(os.path.relpath(target, os.path.dirname(link)))
PY
}

make_link() {
  local link="$1" target="$2" rel
  if [[ "$link" == "$SRC_DIR" ]]; then
    echo "  = $link (source checkout; left untouched)"
    return 0
  fi
  if [[ -L "$link" ]]; then
    rm -f "$link"
  elif [[ -e "$link" ]]; then
    if [[ "$FORCE" != 1 ]]; then
      echo "  ! $link exists and is not a symlink; skipped (use --force)" >&2
      return 0
    fi
    rm -rf "$link"
  fi
  mkdir -p "$(dirname "$link")"
  rel="$(relative_link "$target" "$link")"
  if ln -s "$rel" "$link" 2>/dev/null; then
    echo "  -> $link -> $rel"
  else
    echo "  ! symlink failed for $link; copying instead" >&2
    copy_tree "$target" "$link"
  fi
}

resolve_src
resolve_paths

if [[ "$UNINSTALL" == 1 ]]; then
  removed=0
  for path in "$REAL_DEST" "${LINKS[@]:-}"; do
    [[ -n "$path" ]] || continue
    if [[ "$path" == "$SRC_DIR" ]]; then
      echo "  = $path (source checkout; left untouched)"
      continue
    fi
    if [[ -f "$path/SKILL.md" ]] && grep -q "US Sleep Regulatory" "$path/SKILL.md"; then
      rm -rf "$path"
      echo "Removed: $path"
      removed=1
    elif [[ -L "$path" ]]; then
      rm -f "$path"
      echo "Removed symlink: $path"
      removed=1
    fi
  done
  [[ "$removed" == 1 ]] || die "no installed US Sleep Regulatory skill found for target '$TARGET'"
  exit 0
fi

check_python
VERSION="$(cat "$SRC_DIR/VERSION" 2>/dev/null || cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "$DEFAULT_VERSION")"

echo "Installing $SKILL_DISPLAY v$VERSION"
echo "  from: $SRC_DIR"
echo "  real: $REAL_DEST"

if [[ "$REAL_DEST" == "$SRC_DIR" ]]; then
  echo "  = already in place"
else
  if [[ -e "$REAL_DEST" && "$FORCE" != 1 ]]; then
    die "already installed at $REAL_DEST (use --force to overwrite)"
  fi
  if [[ "$FORCE" == 1 && -e "$REAL_DEST" ]]; then
    if [[ -d "$REAL_DEST/snapshots" ]]; then
      SNAPSHOT_BACKUP="$(mktemp -d)"
      TMP_DIRS+=("$SNAPSHOT_BACKUP")
      cp -R "$REAL_DEST/snapshots/." "$SNAPSHOT_BACKUP/"
      echo "  preserving snapshots"
    fi
    rm -rf "$REAL_DEST"
  fi
  copy_tree "$SRC_DIR" "$REAL_DEST"
  copy_dist_files "$REAL_DEST"
  if [[ -n "$SNAPSHOT_BACKUP" ]]; then
    mkdir -p "$REAL_DEST/snapshots"
    cp -R "$SNAPSHOT_BACKUP/." "$REAL_DEST/snapshots/"
    echo "  restored snapshots"
  fi
  echo "  copied $(find "$REAL_DEST" -type f | wc -l | tr -d ' ') files"
fi

for link in "${LINKS[@]:-}"; do
  [[ -n "$link" ]] && make_link "$link" "$REAL_DEST"
done

chmod +x "$REAL_DEST/scripts/reg.py" "$REAL_DEST/scripts/mcp_server.py" "$REAL_DEST/install.sh" 2>/dev/null || true

if [[ "$RUN_DOCTOR" == 1 ]]; then
  echo
  echo "== source health check =="
  if ! python3 "$REAL_DEST/scripts/reg.py" doctor --format md; then
    echo
    echo "WARNING: the health check failed. The skill is installed; retry when" >&2
    echo "network access to openFDA/eCFR/Federal Register is available:" >&2
    echo "  python3 \"$REAL_DEST/scripts/reg.py\" doctor" >&2
  fi
fi

cat <<EOF

Installed: $SKILL_DISPLAY v$VERSION
Real path: $REAL_DEST
$(for l in "${LINKS[@]:-}"; do [[ -n "$l" ]] && echo "Link:      $l"; done)

How to invoke:
  Codex CLI     restart Codex, then use \$us-sleep-regulatory or /skills
  Claude Code   restart Claude Code, then use @us-sleep-regulatory
  OpenCode      restart OpenCode, then ask or use @us-sleep-regulatory
  CLI           python3 "$REAL_DEST/scripts/reg.py" --help

First commands:
  python3 "$REAL_DEST/scripts/reg.py" predicates --product-code QVO --format md
  python3 "$REAL_DEST/scripts/reg.py" cfr 21 882.5801 --format md
  python3 "$REAL_DEST/scripts/reg.py" snapshot

MCP config (optional, for any MCP client):
  {
    "mcp": {
      "servers": {
        "us-sleep-reg": {
          "type": "local",
          "command": ["python3", "$REAL_DEST/scripts/mcp_server.py"],
          "cwd": "."
        }
      }
    }
  }

Update:    re-run with --force
Uninstall: ./install.sh --target $TARGET --uninstall
EOF

exit 0
