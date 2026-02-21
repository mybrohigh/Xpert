#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ROOT_DIR="$(cd "$ROOT_DIR" && pwd)"
REPORT_DIR="${ROOT_DIR}/reports"
REPORT_FILE="${REPORT_DIR}/duplicate_audit_$(date +%Y%m%d_%H%M%S).txt"

mkdir -p "$REPORT_DIR"

TMP_ALL="$(mktemp)"
TMP_HASH="$(mktemp)"
TMP_BAK="$(mktemp)"
TMP_NAMES="$(mktemp)"

cleanup() {
  rm -f "$TMP_ALL" "$TMP_HASH" "$TMP_BAK" "$TMP_NAMES"
}
trap cleanup EXIT

find "$ROOT_DIR" \
  -type d \( \
    -name .git -o \
    -name .venv -o \
    -name node_modules -o \
    -name __pycache__ -o \
    -name build -o \
    -name dist -o \
    -name data -o \
    -path "*/xray_api/proto" \
  \) -prune -o \
  -type f -print | sort > "$TMP_ALL"

HASH_CMD=(sha256sum)
if ! command -v sha256sum >/dev/null 2>&1; then
  HASH_CMD=(shasum -a 256)
fi

while IFS= read -r file; do
  hash="$("${HASH_CMD[@]}" "$file" | awk '{print $1}')"
  printf '%s\t%s\n' "$hash" "$file" >> "$TMP_HASH"
done < "$TMP_ALL"

find "$ROOT_DIR" \
  -type d \( -name .git -o -name .venv -o -name node_modules \) -prune -o \
  -type f \( \
    -name "*.bak" -o \
    -name "*.bak.*" -o \
    -name "*.bak_*" -o \
    -name "*.old" -o \
    -name "*.orig" -o \
    -name "*.tmp" -o \
    -name "*~" -o \
    -name "ui_*.tsx" \
  \) -print | sort > "$TMP_BAK"

awk -F'\t' '{print $2}' "$TMP_HASH" \
  | awk -F/ '
      {
        name=$NF
        if (name == "__init__.py") next
        if (name == "index.ts") next
        if (name == "index.tsx") next
        if (name == "index.js") next
        if (name == "README.md") next
        print name "\t" $0
      }
    ' \
  | sort > "$TMP_NAMES"

{
  echo "Xpert duplicate audit"
  echo "Generated (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Root: $ROOT_DIR"
  echo

  echo "=== 1) Root-level source files (often leftovers) ==="
  find "$ROOT_DIR" -maxdepth 1 -type f \
    \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.json" \) \
    | sort
  echo

  echo "=== 2) Backup/temp candidates ==="
  if [[ -s "$TMP_BAK" ]]; then
    cat "$TMP_BAK"
  else
    echo "(none)"
  fi
  echo

  echo "=== 3) Exact duplicate content (sha256 groups) ==="
  awk -F'\t' '
    {
      count[$1]++
      paths[$1]=paths[$1] "\n  - " $2
    }
    END {
      groups=0
      for (h in count) {
        if (count[h] > 1) {
          groups++
          print "hash=" h " files=" count[h] paths[h] "\n"
        }
      }
      if (groups == 0) {
        print "(none)"
      }
    }
  ' "$TMP_HASH"
  echo

  echo "=== 4) Same basename in multiple locations ==="
  awk -F'\t' '
    {
      count[$1]++
      paths[$1]=paths[$1] "\n  - " $2
    }
    END {
      groups=0
      for (n in count) {
        if (count[n] > 1) {
          groups++
          print "name=" n " files=" count[n] paths[n] "\n"
        }
      }
      if (groups == 0) {
        print "(none)"
      }
    }
  ' "$TMP_NAMES"
  echo

  echo "=== 5) Safe next step ==="
  echo "Review this report, then remove only files that are not imported by runtime code."
  echo "Check usage before delete: rg -n \"<name_or_module>\" \"$ROOT_DIR\""
} > "$REPORT_FILE"

echo "Audit report created: $REPORT_FILE"
