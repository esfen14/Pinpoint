#!/usr/bin/env python3
"""Build the Word style template (reference.docx) used by export_manuals.sh.

Starts from Pandoc's default template and sets: A4 page, 2 cm margins, Arial 11 pt,
10 pt table and list text with borders, a new page before each chapter (Heading 2) and before
the contents list, and a centred page-number footer. Standard library plus `pandoc`.

Usage: make_reference.py OUTPUT.docx
"""
import re
import subprocess
import sys
import tempfile
import zipfile

FOOTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
          '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
          '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
          '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
          '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')
SECT = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter1"/>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
        'w:header="567" w:footer="567" w:gutter="0"/></w:sectPr>')
BORDERS = '<w:tblBorders>'
for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
    BORDERS += f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
BORDERS += '</w:tblBorders>'


def patch_styles(xml):
    theme_fonts = (r'w:asciiTheme="(?:major|minor)HAnsi" w:eastAsiaTheme="(?:major|minor)EastAsia" '
                   r'w:hAnsiTheme="(?:major|minor)HAnsi" w:cstheme="(?:major|minor)Bidi"')
    xml = re.sub(theme_fonts, 'w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"', xml)
    xml = xml.replace('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" />',
                      '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New" />\n'
                      '<w:sz w:val="18" /><w:szCs w:val="18" />')
    xml = re.sub(r'<w:sz w:val="24" />(\s*)<w:szCs w:val="24" />',
                 r'<w:sz w:val="22" />\1<w:szCs w:val="22" />', xml, count=1)

    def in_style(text, style_id, edit):
        pattern = re.compile(r'(<w:style [^>]*w:styleId="%s".*?)(</w:style>)' % style_id, re.S)
        if not pattern.search(text):
            sys.exit(f"style {style_id} not found in the Pandoc template")
        return pattern.sub(lambda m: edit(m.group(1)) + m.group(2), text, count=1)

    # Pandoc's own 11 pt size for code would override the 9 pt added above.
    xml = in_style(xml, "VerbatimChar", lambda s: s.replace('<w:sz w:val="22" />', ""))
    xml = in_style(xml, "Compact", lambda s: s.replace(
        "</w:pPr>", '</w:pPr><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'))
    xml = in_style(xml, "Table", lambda s: s.replace("<w:tblPr>", "<w:tblPr>" + BORDERS, 1))
    for style_id in ("Heading2", "TOCHeading"):
        xml = in_style(xml, style_id,
                       lambda s: s.replace("<w:pPr>", "<w:pPr><w:pageBreakBefore/>", 1))
    return xml


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    output = sys.argv[1]
    default = subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                             capture_output=True, check=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".docx") as temporary:
        temporary.write(default)
        temporary.flush()
        with zipfile.ZipFile(temporary.name) as zin:
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "word/theme/theme1.xml":
                        data = data.decode().replace('<a:latin typeface="Cambria" />',
                                                     '<a:latin typeface="Arial" />').replace(
                            '<a:latin typeface="Calibri" />', '<a:latin typeface="Arial" />').encode()
                    elif item.filename == "word/styles.xml":
                        data = patch_styles(data.decode()).encode()
                    elif item.filename == "word/document.xml":
                        data = data.decode().replace("<w:sectPr />", SECT).encode()
                    elif item.filename == "word/_rels/document.xml.rels":
                        footer_rel = ('<Relationship Id="rIdFooter1" Type="http://schemas.openxmlformats.org/'
                                      'officeDocument/2006/relationships/footer" Target="footer1.xml"/>')
                        data = data.decode().replace("</Relationships>", footer_rel + "</Relationships>").encode()
                    elif item.filename == "[Content_Types].xml":
                        footer_type = ('<Override PartName="/word/footer1.xml" ContentType="application/vnd.'
                                       'openxmlformats-officedocument.wordprocessingml.footer+xml"/>')
                        data = data.decode().replace("</Types>", footer_type + "</Types>").encode()
                    zout.writestr(item, data)
                zout.writestr("word/footer1.xml", FOOTER)
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
