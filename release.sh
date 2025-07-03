#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# release.sh  –  Bump project version, commit, tag, and push.
#
# Usage:
#   ./release.sh                # auto‑increment PATCH        (e.g. 1.4.2 → 1.4.3)
#   ./release.sh 2.0.0          # set explicit version
#
# Environment variables:
#   VERSION_FILE   Path to file holding the version   (default: VERSION)
#   REMOTE         Git remote to push to              (default: origin)
# ---------------------------------------------------------------------------
set -euo pipefail

VERSION_FILE="${VERSION_FILE:-VERSION}"
REMOTE="${REMOTE:-origin}"

# -------- helpers -----------------------------------------------------------
current_version() {
  [[ -f "$VERSION_FILE" ]] && cat "$VERSION_FILE" || echo "0.0.0"
}

increment_patch() {
  local v="$1"
  IFS='.' read -r major minor patch <<<"$v"
  echo "${major}.${minor}.$((patch + 1))"
}

semver_regex='^[0-9]+\.[0-9]+\.[0-9]+$'

# -------- determine new version --------------------------------------------
if [[ $# -eq 0 ]]; then
  new_version=$(increment_patch "$(current_version)")
else
  new_version="$1"
  if [[ ! "$new_version" =~ $semver_regex ]]; then
    echo "✖ Invalid version: '$new_version'  (expected MAJOR.MINOR.PATCH)" >&2
    exit 1
  fi
fi

tag="v${new_version}"

# -------- abort if tag already exists --------------------------------------
git fetch --tags "$REMOTE" >/dev/null
if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
  echo "✖ Tag '$tag' already exists. Choose a different version." >&2
  exit 1
fi

# -------- write, commit, tag, push -----------------------------------------
echo "$new_version" > "$VERSION_FILE"
git add "$VERSION_FILE"
git commit -m "chore(release): bump version to $new_version"
git tag -a "$tag" -m "Release $new_version"
git push "$REMOTE" HEAD --tags

echo "✔ Released $tag"