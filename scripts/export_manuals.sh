#!/usr/bin/env bash
# Export the User Manual and Technical Manual to DOCX and PDF (issue #181 section G).
# Usage: scripts/export_manuals.sh [user|technical|all]   (default: all)
# Output: build/manuals/<name>.docx and <name>.pdf  (build/ is git-ignored)
# Needs: pandoc, soffice (LibreOffice), node/npx (mermaid-cli, fetched on first use),
#        python3. Set MERMAID_CHROME to a Chromium binary to avoid a browser download.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
tools="$root/scripts/manual_export"
out="$root/build/manuals"
which_manual="${1:-all}"

case "$which_manual" in user|technical|all) ;; *) echo "usage: $0 [user|technical|all]" >&2; exit 2 ;; esac

for tool in pandoc soffice npx python3; do
  command -v "$tool" >/dev/null || { echo "export_manuals: $tool is required" >&2; exit 1; }
done

mkdir -p "$out"
reference="$tools/reference.docx"
if [ ! -f "$reference" ]; then
  python3 -I "$tools/make_reference.py" "$reference"
fi

# LibreOffice crashes (std::bad_alloc) under some inherited environments, so run it clean.
# A private profile carries the macro that refreshes the contents list before the PDF save.
profile="$out/lo-profile"
run_soffice() {
  env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/local/bin \
    soffice -env:UserInstallation="file://$profile" --headless --norestore "$@" 2>&1 \
    | grep -v -E "dconf|javaldx" || true
}
if [ ! -d "$profile/user/basic/Standard" ]; then
  # First run creates the profile; the throw-away conversion is only for that.
  printf 'x\n' > "$out/profile-init.txt"
  run_soffice --convert-to pdf --outdir "$out" "$out/profile-init.txt" >/dev/null
fi
cp "$tools/ToPdf.xba" "$profile/user/basic/Standard/Module1.xba"

export_one() {
  local name="$1" source="$2"
  local work="${out:?}/work-${name:?}"
  mkdir -p "$work"
  # An open copy would be overwritten, and LibreOffice then waits on its lock file.
  local extension
  for extension in docx pdf; do
    if [ -e "$out/.~lock.$name.$extension#" ]; then
      echo "export_manuals: close $out/$name.$extension first (it is open in LibreOffice)" >&2
      exit 1
    fi
  done
  python3 -I "$tools/prepare.py" "$source" "$work/$name.md" "$work"
  pandoc "$work/$name.md" -f gfm+yaml_metadata_block+raw_attribute -o "$out/$name.docx" \
    --reference-doc="$reference" --resource-path="$work"
  python3 -I "$tools/center_tables.py" "$out/$name.docx"
  run_soffice "macro:///Standard.Module1.ToPdf($out/$name.docx,$out/$name.pdf)" >/dev/null
  [ -s "$out/$name.pdf" ] || { echo "export_manuals: PDF for $name was not produced" >&2; exit 1; }
  echo "wrote $out/$name.docx and $out/$name.pdf"
}

case "$which_manual" in
  user|all) export_one User_Manual "$root/docs/User_Manual/User_Manual.md" ;;
esac
case "$which_manual" in
  technical|all) export_one Technical_Manual "$root/docs/Technical_Manual/Technical_Manual.md" ;;
esac
