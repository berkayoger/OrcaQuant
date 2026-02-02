#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/cleanup_repo.sh [--check]

Removes tracked build/test artifacts and manages a .gitignore block.
  --check   report what would change without modifying files
USAGE
}

check_mode=false
if [[ ${1-} == "--check" ]]; then
  check_mode=true
  shift
fi

if [[ ${1-} == "-h" || ${1-} == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "Unexpected arguments: $*" >&2
  usage >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: this script must be run inside a git repository." >&2
  exit 1
fi

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

artifact_pathspecs=(
  ':(glob)**/dist/**'
  ':(glob)**/build/**'
  ':(glob)**/node_modules/**'
  ':(glob)**/__pycache__/**'
  ':(glob)**/.pytest_cache/**'
  ':(glob)**/htmlcov/**'
  ':(glob)**/logs/**'
  ':(glob)**/.coverage'
  ':(glob)**/pytest.log'
  ':(glob)**/.pytest.log'
  ':(glob)**/.pytest_fail.log'
  ':(glob)**/*.pyc'
  ':(glob)**/*.pyo'
  ':(glob)**/*.pyd'
  ':(glob)**/*.egg-info/**'
  ':(glob)**/*.db'
  ':(glob)**/dump.rdb'
  ':(glob)**/sbom.json'
  ':(glob)**/sbom-*.json'
  ':(glob)**/pip-audit-*.json'
)

mapfile -d '' -t tracked_artifacts < <(git ls-files -z -- "${artifact_pathspecs[@]}")

if (( ${#tracked_artifacts[@]} > 0 )); then
  if $check_mode; then
    echo "Tracked artifacts to remove:"
    printf '  %s\n' "${tracked_artifacts[@]}"
  else
    git rm -r -- "${tracked_artifacts[@]}"
  fi
else
  echo "No tracked artifacts found in the cleanup list."
fi

begin_marker="# BEGIN ORCAQUANT MANAGED CLEANUP"
end_marker="# END ORCAQUANT MANAGED CLEANUP"

managed_block=$(cat <<'BLOCK'
# BEGIN ORCAQUANT MANAGED CLEANUP
# This block is managed by scripts/cleanup_repo.sh. Do not edit by hand.
dist/
build/
node_modules/
__pycache__/
.pytest_cache/
htmlcov/
logs/
.coverage
pytest.log
.pytest.log
.pytest_fail.log
*.py[cod]
*.egg-info/
*.db
dump.rdb
sbom.json
sbom-*.json
pip-audit-*.json
# END ORCAQUANT MANAGED CLEANUP
BLOCK
)

gitignore_path="$repo_root/.gitignore"
tmp_gitignore=$(mktemp)

if [[ -f "$gitignore_path" ]]; then
  if grep -q "$begin_marker" "$gitignore_path"; then
    awk -v begin="$begin_marker" -v end="$end_marker" -v block="$managed_block" '
      $0 == begin {print block; in_block=1; next}
      $0 == end {in_block=0; next}
      !in_block {print}
    ' "$gitignore_path" > "$tmp_gitignore"
  else
    { cat "$gitignore_path"; echo; echo "$managed_block"; } > "$tmp_gitignore"
  fi
else
  printf '%s\n' "$managed_block" > "$tmp_gitignore"
fi

if cmp -s "$gitignore_path" "$tmp_gitignore" 2>/dev/null; then
  rm -f "$tmp_gitignore"
  echo ".gitignore managed block already up to date."
else
  if $check_mode; then
    echo "Would update .gitignore with managed cleanup block."
    rm -f "$tmp_gitignore"
  else
    mv "$tmp_gitignore" "$gitignore_path"
    echo "Updated .gitignore with managed cleanup block."
  fi
fi
