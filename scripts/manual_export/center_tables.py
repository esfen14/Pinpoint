#!/usr/bin/env python3
"""Centre every table in a DOCX written by Pandoc.

Pandoc sets left alignment on each table itself, which overrides the table style in
reference.docx, so the alignment has to be changed in the exported file.

Usage: center_tables.py FILE.docx
Standard library only.
"""
import re
import sys
import zipfile
from pathlib import Path

DOCUMENT = "word/document.xml"
TABLE_PROPERTIES = re.compile(r"<w:tblPr>.*?</w:tblPr>", re.S)
ALIGNMENT = re.compile(r'<w:jc w:val="(?:left|start)"\s*/>')


def center(xml):
    """Return the document XML with centred tables, and how many were changed."""
    changed = 0

    def table(found):
        nonlocal changed
        properties, count = ALIGNMENT.subn('<w:jc w:val="center" />', found.group(0))
        changed += count
        return properties

    return TABLE_PROPERTIES.sub(table, xml), changed


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    temporary = path.with_name(path.name + ".tmp")
    changed = 0
    with zipfile.ZipFile(path) as source:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename == DOCUMENT:
                    xml, changed = center(data.decode("utf-8"))
                    data = xml.encode("utf-8")
                target.writestr(item, data)
    temporary.replace(path)
    print(f"{path.name}: {changed} table(s) centred")


if __name__ == "__main__":
    main()
