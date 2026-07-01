#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-/opt/anaconda3/bin/python3}"
[ -x "$PYTHON" ] || PYTHON=python3

git diff --check

if git log --format='%an <%ae>%n%cn <%ce>%n%s%n%b' | grep -Eiq 'co-authored-by:|generated with|claude|codex'; then
  echo "FAIL: git history contains disallowed assisted-author attribution"
  exit 1
fi

if command -v rg >/dev/null 2>&1; then
  if rg -n --hidden --glob '!.git/**' --glob '!*.pyc' --glob '!dist/**' --glob '!build/**' \
    '(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|api[_-]?key\s*[:=]\s*["'\'']?[A-Za-z0-9_./+=-]{16,})' .; then
    echo "FAIL: possible secret found"
    exit 1
  fi
fi

"$PYTHON" - <<'PY'
from pathlib import Path
import py_compile
import sys

bad = []
for path in Path(".").rglob("*.py"):
    if any(part in {".git", ".venv", "venv", "__pycache__", "build", "dist"} for part in path.parts):
        continue
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        bad.append(f"{path}: {exc}")
if bad:
    print("FAIL: python compile errors")
    print("\n".join(bad))
    sys.exit(1)
PY

if [ -d tests ]; then
  "$PYTHON" -m pytest -q
fi

if "$PYTHON" -c 'import importlib.util, sys; sys.exit(0 if importlib.util.find_spec("ruff") else 1)' 2>/dev/null; then
  "$PYTHON" -m ruff check .
fi

if [ -f scripts/check_links.py ]; then
  "$PYTHON" scripts/check_links.py
fi

echo "OK: pr review gate passed"
