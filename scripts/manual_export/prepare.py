#!/usr/bin/env python3
"""Prepare one manual (Markdown) for printing.

Reads a manual, writes a print-ready copy with a Pandoc metadata header:
  * removes the manual's own contents list (Pandoc adds a real one with page numbers);
  * turns the title block into Pandoc metadata (title page);
  * renders ```mermaid blocks to PNG with mermaid-cli and links the images;
  * makes image paths absolute;
  * rewrites links to other repository files as printed repo-path notes, because a
    printed copy cannot follow a relative link. Web links and in-document anchors stay.

Usage: prepare.py SOURCE.md OUTPUT.md WORKDIR [--no-mermaid]
Standard library only.
"""
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

MERMAID_CLI = "@mermaid-js/mermaid-cli@11.4.2"
FENCE = re.compile(r"(^```.*?^```[ \t]*\n)", re.S | re.M)
MERMAID = re.compile(r"^```mermaid\n(.*?)^```[ \t]*\n", re.S | re.M)
LINK = re.compile(r"(?<!\!)\[((?:[^\[\]]|\[[^\]]*\])+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")


def find_chrome():
    """A Chromium for mermaid-cli: MERMAID_CHROME, else a Playwright one, else None."""
    env = os.environ.get("MERMAID_CHROME")
    if env:
        return env
    found = sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome")))
    if found:
        return found[-1]
    return None


def render_mermaid(code, number, workdir):
    mmd = workdir / f"diagram-{number}.mmd"
    png = workdir / f"diagram-{number}.png"
    mmd.write_text(code)
    config = {"args": ["--no-sandbox"]}
    chrome = find_chrome()
    if chrome:
        config["executablePath"] = chrome
    puppeteer = workdir / "puppeteer.json"
    puppeteer.write_text(json.dumps(config))
    env = dict(os.environ)
    if chrome:
        env["PUPPETEER_SKIP_DOWNLOAD"] = "1"
    command = ["npx", "-y", MERMAID_CLI, "-i", str(mmd), "-o", str(png),
               "-p", str(puppeteer), "-s", "2", "-b", "white"]
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    if result.returncode != 0 or not png.exists():
        sys.exit(f"mermaid-cli failed for diagram {number}:\n{result.stderr[-800:]}")
    return png


def rewrite_outside_fences(text, function):
    parts = FENCE.split(text)
    for index in range(0, len(parts), 2):
        parts[index] = function(parts[index])
    return "".join(parts)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    if len(args) != 3:
        sys.exit(__doc__)
    source, output, workdir = Path(args[0]).resolve(), Path(args[1]), Path(args[2])
    workdir.mkdir(parents=True, exist_ok=True)
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=source.parent,
                         capture_output=True, text=True, check=True).stdout.strip()
    repo = Path(top)
    text = source.read_text()

    # Title block: "# Product" and "## Manual name" become Pandoc metadata.
    match = re.match(r"# (.+)\n\n## (.+)\n", text)
    if not match:
        sys.exit("Expected a '# title' and '## subtitle' at the top of the manual")
    title, subtitle = match.group(1).strip(), match.group(2).strip()
    text = text[match.end():]

    # The manual's own contents list is replaced by Pandoc's.
    text = re.sub(r"^## Table of contents\n.*?^---\n", "", text, count=1, flags=re.S | re.M)

    # Mermaid diagrams to images.
    counter = [0]

    def diagram(found):
        counter[0] += 1
        if "--no-mermaid" in flags:
            return "*(diagram omitted)*\n"
        code = found.group(1)
        # A wide left-to-right diagram prints too small on a portrait page: stack it top to bottom.
        code = re.sub(r"^(\s*(?:flowchart|graph)) LR\b", r"\1 TB", code, count=1)
        png = render_mermaid(code, counter[0], workdir)
        return f"![Diagram {counter[0]}]({png.resolve()})\n"

    text = MERMAID.sub(diagram, text)

    # Images: absolute paths.
    def absolute(found):
        target = found.group(2)
        if re.match(r"^(https?:|/)", target):
            return found.group(0)
        return f"![{found.group(1)}]({(source.parent / unquote(target)).resolve()})"

    # Links: repo-path notes.
    def note(found):
        label, target = found.group(1), found.group(2)
        if re.match(r"^(https?:|mailto:|#)", target):
            return found.group(0)
        path, _, anchor = target.partition("#")
        resolved = (source.parent / unquote(path)).resolve()
        try:
            relative = resolved.relative_to(repo)
        except ValueError:
            return label
        suffix = f" section `{anchor}`" if anchor else ""
        return f"{label} (repository file `{relative}`{suffix})"

    def links_and_images(chunk):
        return LINK.sub(note, IMAGE.sub(absolute, chunk))

    text = rewrite_outside_fences(text, links_and_images)

    # Contents list after the front matter (title block, document table, notices), before
    # the first chapter. LibreOffice refreshes it during the PDF step.
    contents = (
        "```{=openxml}\n"
        '<w:p><w:pPr><w:pStyle w:val="TOCHeading"/></w:pPr><w:r><w:t>Contents</w:t></w:r></w:p>\n'
        '<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        "<w:r><w:t>Update this field to build the contents list.</w:t></w:r>"
        '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>\n'
        "```\n\n"
    )
    first_chapter = re.search(r"^## ", text, re.M)
    if not first_chapter:
        sys.exit("No chapter heading found")
    text = text[:first_chapter.start()] + contents + text[first_chapter.start():]

    header = f'---\ntitle: "{title}"\nsubtitle: "{subtitle}"\n---\n\n'
    Path(output).write_text(header + text)
    print(f"{source.name}: {counter[0]} diagram(s) rendered")


if __name__ == "__main__":
    main()
