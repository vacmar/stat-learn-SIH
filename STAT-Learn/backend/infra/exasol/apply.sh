#!/usr/bin/env bash
# Apply MANTHAINO schema + seed to the local Exasol (starter-kit profile).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PROFILE="${EXAPUMP_PROFILE:-starter-kit}"

echo "==> Ensuring schema MANTHAINO"
exapump sql -p "$PROFILE" "CREATE SCHEMA IF NOT EXISTS MANTHAINO;"

run_file() {
  local file="$1"
  python3 - "$file" "$PROFILE" <<'PY'
import subprocess, sys
from pathlib import Path
path, profile = sys.argv[1], sys.argv[2]
lines = [ln for ln in Path(path).read_text().splitlines() if not ln.strip().startswith('--')]
stmts = [s.strip() for s in '\n'.join(lines).split(';') if s.strip()]
ok = fail = 0
for stmt in stmts:
    full = f"OPEN SCHEMA MANTHAINO;\n{stmt}"
    r = subprocess.run(['exapump', 'sql', '-p', profile, full], capture_output=True, text=True)
    out = r.stdout + r.stderr
    if r.returncode != 0 or (' failed' in out.lower() and '0 failed' not in out):
        if 'already exists' in out.lower() or 'unique constraint' in out.lower() or 'duplicate' in out.lower():
            ok += 1
            continue
        print(f"FAIL: {stmt[:80]}...")
        print(out[-400:])
        fail += 1
    else:
        ok += 1
print(f"{path}: {ok} ok, {fail} fail / {len(stmts)}")
sys.exit(1 if fail else 0)
PY
}

echo "==> Applying schema.sql"
run_file "$ROOT/schema.sql"
echo "==> Applying seed.sql"
run_file "$ROOT/seed.sql"
echo "==> Done. Demo gap query example:"
echo "  exapump sql -p $PROFILE \"OPEN SCHEMA MANTHAINO; SELECT COUNT(*) FROM skills;\""
