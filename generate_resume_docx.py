"""Generate a styled Word resume from the repository's 简历.md.

This intentionally uses only Python's standard library so it works in the
project's minimal environment without pandoc, LibreOffice or python-docx.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "简历.md"
OUTPUT_DIR = ROOT / "artifacts"
OUTPUT = OUTPUT_DIR / "数据分析师_Python数据开发_简历.docx"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def run_xml(text: str, *, bold: bool = False, color: str = "25342F", size: int = 19) -> str:
    properties = [
        '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Microsoft YaHei"/>',
        f'<w:color w:val="{color}"/>',
        f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>',
    ]
    if bold:
        properties.append("<w:b/><w:bCs/>")
    preserve = ' xml:space="preserve"' if text.startswith(" ") or text.endswith(" ") else ""
    return f"<w:r><w:rPr>{''.join(properties)}</w:rPr><w:t{preserve}>{escape(text)}</w:t></w:r>"


def inline_runs(text: str, *, color: str = "25342F", size: int = 19, default_bold: bool = False) -> str:
    parts = re.split(r"(\*\*.*?\*\*)", text)
    runs = []
    for part in parts:
        if not part:
            continue
        is_bold = part.startswith("**") and part.endswith("**")
        value = part[2:-2] if is_bold else part
        runs.append(run_xml(value, bold=default_bold or is_bold, color=color, size=size))
    return "".join(runs)


def paragraph(
    text: str,
    *,
    kind: str = "body",
) -> str:
    if kind == "title":
        ppr = (
            '<w:jc w:val="center"/><w:spacing w:before="0" w:after="70" w:line="300" w:lineRule="auto"/>'
            '<w:keepNext/>'
        )
        runs = inline_runs(text, color="173E35", size=42, default_bold=True)
    elif kind == "contact":
        ppr = '<w:jc w:val="center"/><w:spacing w:after="130" w:line="230" w:lineRule="auto"/>'
        runs = inline_runs(text, color="53645E", size=18)
    elif kind == "section":
        ppr = (
            '<w:spacing w:before="130" w:after="65"/><w:keepNext/>'
            '<w:shd w:val="clear" w:color="auto" w:fill="E1EEE9"/>'
            '<w:ind w:left="90" w:right="70"/>'
            '<w:pBdr><w:bottom w:val="single" w:sz="10" w:space="1" w:color="2F6A5B"/></w:pBdr>'
        )
        runs = inline_runs(text, color="173E35", size=23, default_bold=True)
    elif kind == "subsection":
        ppr = '<w:spacing w:before="90" w:after="30"/><w:keepNext/>'
        runs = inline_runs(text, color="204F43", size=21, default_bold=True)
    elif kind == "meta":
        ppr = '<w:spacing w:after="45" w:line="230" w:lineRule="auto"/><w:keepNext/>'
        runs = inline_runs(text, color="5E6E68", size=18)
    elif kind == "bullet":
        ppr = (
            '<w:spacing w:after="45" w:line="245" w:lineRule="auto"/>'
            '<w:ind w:left="360" w:hanging="240"/><w:jc w:val="both"/>'
        )
        runs = run_xml("•  ", bold=True, color="2F6A5B", size=19) + inline_runs(text, size=18)
    else:
        ppr = '<w:spacing w:after="55" w:line="245" w:lineRule="auto"/><w:jc w:val="both"/>'
        runs = inline_runs(text, size=19)
    return f"<w:p><w:pPr>{ppr}</w:pPr>{runs}</w:p>"


def markdown_to_document(markdown: str) -> str:
    paragraphs = []
    lines = markdown.splitlines()
    first_body_after_title = True
    previous_kind = ""
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            paragraphs.append(paragraph(line[2:], kind="title"))
            previous_kind = "title"
        elif line.startswith("## "):
            paragraphs.append(paragraph(line[3:], kind="section"))
            previous_kind = "section"
        elif line.startswith("### "):
            paragraphs.append(paragraph(line[4:], kind="subsection"))
            previous_kind = "subsection"
        elif line.startswith("- "):
            paragraphs.append(paragraph(line[2:], kind="bullet"))
            previous_kind = "bullet"
        else:
            kind = "body"
            if first_body_after_title or previous_kind == "subsection" and ("｜" in line or line.startswith("**技术栈")):
                kind = "contact" if first_body_after_title else "meta"
            paragraphs.append(paragraph(line.rstrip("  "), kind=kind))
            first_body_after_title = False
            previous_kind = kind

    section = (
        '<w:sectPr>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="850" w:right="900" w:bottom="800" w:left="900" w:header="420" w:footer="420" w:gutter="0"/>'
        '<w:cols w:space="720"/>'
        '<w:docGrid w:linePitch="312"/>'
        '</w:sectPr>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}"><w:body>{"".join(paragraphs)}{section}</w:body></w:document>'
    )


def write_docx(document_xml: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""
    package_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""
    document_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""
    styles = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
  <w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Microsoft YaHei"/><w:sz w:val="19"/><w:szCs w:val="19"/><w:lang w:val="zh-CN" w:eastAsia="zh-CN"/></w:rPr></w:rPrDefault></w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
</w:styles>"""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    core = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>数据分析师 / Python 数据开发简历</dc:title><dc:creator>懂单儿 RODAS 项目</dc:creator><dc:subject>求职简历</dc:subject>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>"""
    app = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Microsoft Office Word</Application><AppVersion>16.0000</AppVersion></Properties>"""

    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", package_rels)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", styles)
        archive.writestr("word/_rels/document.xml.rels", document_rels)
        archive.writestr("docProps/core.xml", core)
        archive.writestr("docProps/app.xml", app)


if __name__ == "__main__":
    write_docx(markdown_to_document(SOURCE.read_text(encoding="utf-8")))
    print(OUTPUT)
