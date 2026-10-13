#!/usr/bin/env bash
# File the planned development issues in docs/issues/ on GitHub, one GitHub issue per plan number.
#
#   scripts/file_plan_issues.sh                 dry run: print what would be filed (default)
#   scripts/file_plan_issues.sh --create        file them with the GitHub CLI (gh must be installed and logged in)
#   scripts/file_plan_issues.sh --create 7 8 22 file only these plan numbers
#
# The title comes from the "### Issue #N — <title>" heading, the body is the whole file, and the
# labels are "enhancement" plus the priority label from the **Priority:** line (High -> Top Priority).
# Issues waiting on a decision also get "needs-decision". The script never edits the issue files;
# it prints "Issue #N -> <url>" so you can record the GitHub number next to the plan number in
# docs/issues/README.md (branches are issue-<GitHub number>-<slug>).
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
create=0
numbers=()
for arg in "$@"; do
  case "$arg" in
    --create) create=1 ;;
    *[!0-9]*) echo "unknown argument: $arg" >&2; exit 2 ;;
    *) numbers+=("$arg") ;;
  esac
done

# Plan numbers that wait on a product or scope decision.
needs_decision=" 4 5 17 21 25 "

if [ "$create" = 1 ]; then
  command -v gh >/dev/null || { echo "gh (GitHub CLI) is not installed; run without --create for a dry run" >&2; exit 1; }
  gh auth status >/dev/null 2>&1 || { echo "gh is not logged in: run 'gh auth login'" >&2; exit 1; }
fi

shopt -s nullglob
for file in "$root"/docs/issues/issue-[0-9][0-9][0-9].md; do
  n="$((10#$(basename "$file" .md | sed 's/issue-//')))"
  if [ "${#numbers[@]}" -gt 0 ]; then
    keep=0; for want in "${numbers[@]}"; do [ "$want" = "$n" ] && keep=1; done
    [ "$keep" = 1 ] || continue
  fi

  title="$(sed -n '1s/^### Issue #[0-9]* — //p' "$file" | tr -d '\r')"
  priority="$(sed -n 's/^\*\*Priority:\*\* *//p' "$file" | head -n1 | tr -d '\r')"
  case "$priority" in
    High) label="Top Priority" ;;
    Medium) label="Medium Priority" ;;
    Low) label="Low Priority" ;;
    *) echo "issue $n: cannot read the priority ('$priority')" >&2; exit 1 ;;
  esac
  [ -n "$title" ] || { echo "issue $n: cannot read the title" >&2; exit 1; }
  labels="enhancement,$label"
  case "$needs_decision" in *" $n "*) labels="$labels,needs-decision" ;; esac

  if [ "$create" = 1 ]; then
    url="$(gh issue create --title "$title" --body-file "$file" --label "$labels")"
    echo "Issue #$n -> $url"
  else
    printf 'Issue #%s | %s | labels: %s\n' "$n" "$title" "$labels"
  fi
done
