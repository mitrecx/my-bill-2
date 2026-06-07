#!/bin/sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

chmod +x .githooks/commit-msg .githooks/prepare-commit-msg
git config core.hooksPath .githooks

echo "Git hooks 已启用: core.hooksPath=.githooks"
echo "将自动移除 commit 中的 Cursor Co-authored-by / Made-with 行。"
