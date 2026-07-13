#!/usr/bin/env bash
set -euo pipefail
REPO_NAME="${1:-ecorevive-os}"
if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required. In Codespaces it is preinstalled." >&2
  exit 1
fi
gh auth status >/dev/null
git config user.name >/dev/null 2>&1 || git config user.name "Jaiwal Patel"
git config user.email >/dev/null 2>&1 || git config user.email "ujaiwal@outlook.com"
if [[ ! -d .git ]]; then
  git init
  git branch -M main
fi
git add .
git commit -m "Initial EcoRevive OS operational MVP" || true
if git remote get-url origin >/dev/null 2>&1; then
  echo "An origin remote already exists: $(git remote get-url origin)"
  git push -u origin main
else
  gh repo create "$REPO_NAME" --private --source=. --remote=origin --push
fi
echo "Private repository ready: $(gh repo view --json url -q .url)"
