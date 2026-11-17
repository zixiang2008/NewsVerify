#!/usr/bin/env bash
# Publish the sanitised NewsVerify source and tri-language docs to GitHub.
# The version is read from app/version.py so every release is traceable.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_URL="https://github.com/zixiang2008/NewsVerify.git"
BRANCH="main"
cd "$ROOT"

python3 - <<'PY' > /tmp/newsverify_version.txt
from app.version import VERSION
print(VERSION)
PY
VERSION="$(tr -d '\n' < /tmp/newsverify_version.txt)"
rm -f /tmp/newsverify_version.txt

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  git init -b "$BRANCH"
fi

# Safety: never publish secrets.
if [ -f .env ] && ! git check-ignore -q .env 2>/dev/null; then
  echo "ERROR: .env is not ignored by git. Add it to .gitignore before syncing." >&2
  exit 1
fi

if ! git config user.name >/dev/null 2>&1; then
  git config user.name "zixiang2008"
fi
if ! git config user.email >/dev/null 2>&1; then
  git config user.email "zixiang2008@users.noreply.github.com"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
fi

# Commit local changes first so a rebase never fails on a dirty tree.
git add -A
if git diff --cached --quiet; then
  echo "No local changes to publish (version $VERSION already staged)."
else
  git commit -m "release: v${VERSION} - sync website and tri-language docs"
fi

# Rebase on the remote state when it exists; tolerate an empty new repository.
git fetch origin "$BRANCH" >/dev/null 2>&1 || true
if git rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1; then
  git rebase "origin/$BRANCH" || {
    echo "ERROR: rebase failed. Resolve conflicts manually, then rerun." >&2
    exit 1
  }
fi

git push -u origin "HEAD:${BRANCH}"
echo "Published NewsVerify v${VERSION} to ${REPO_URL} (${BRANCH})."
