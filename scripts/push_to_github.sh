#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: ./scripts/push_to_github.sh https://github.com/YOUR_USERNAME/ecorevive-os.git"
  exit 1
fi

REMOTE="$1"

git config user.name >/dev/null 2>&1 || git config user.name "Jaiwal Patel"
git config user.email >/dev/null 2>&1 || git config user.email "ujaiwal@outlook.com"

if [[ ! -d .git ]]; then
  git init
  git branch -M main
fi

git add .
git commit -m "Initial EcoRevive OS operational MVP" || true
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE"
git push -u origin main
