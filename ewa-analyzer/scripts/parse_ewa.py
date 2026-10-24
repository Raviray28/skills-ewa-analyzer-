#!/usr/bin/env python3
"""Turn an SAP EarlyWatch Alert report (.DOC saved as Word 2003 XML, or .docx) into plain text
that a language model can read section by section, keeping the red/yellow/green rating icons.

Usage:
    python parse_ewa.py <ewa-file> [--out ewa_extract]

Writes into the output folder:
    ewa_text.md     headings (#), paragraphs, tables (pipe rows) with rating tokens [R] [Y] [G] [i] [-]
    ewa_index.json  list of headings with line numbers, so a section can be read on its own
    ewa_meta.json   best-effort header facts (system id, period, product hint)
    ewa_key.md      the Service Summary block only (a few hundred lines): read this first

Rating tokens:  [R]=red  [Y]=yellow  [G]=green  [i]=information  [-]=not rated / grey
Only the standard library and Pillow (optional, for the icons) are used.
"""
import argparse, base64, html, io, json, os, re, sys, zipfile
from xml.etree import ElementTree as ET

W2003 = "http://schemas.microsoft.com/office/word/2003/wordml"
W2006 = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
VML = "urn:schemas-microsoft-com:vml"


def classify_icon(raw):
    """Return R, Y, G, i, - or None (ignore) for a small rating icon, by its average colour."""
    try:
        from PIL import Image
    except ImportError:
        return "?"
    try:
        im = Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception:
        return None
    if im.width > 60 or im.height > 60:
        return None  # a chart or picture, not a rating icon
    px = [p for p in im.getdata() if p[3] > 128 and not (p[0] > 230 and p[1] > 230 and p[2] > 230)]
    if not px:
        return None
    r = sum(p[0] for p in px) / len(px)
    g = sum(p[1] for p in px) / len(px)
    b = sum(p[2] for p in px) / len(px)
    if r < 25 and g < 25 and b < 25:
        return None  # black separator glyph
    if r > 110 and g < 70 and b < 110:
        return "R"
    if r > 110 and g > 100 and b < 90:
        return "Y"
    if g > r + 20 and g > b + 20:
        return "G"
    if b > r + 80 and b > g + 80:
        return "i"
    return "-"


class Extractor:
    def __init__(self, ns, icons):
        self.ns = ns
        self.W = "{%s}" % ns
        self.icons = icons  # name -> rating letter
        self.lines = []
        self.index = []

    def text_of(self, p):
        W = self.W
        out = []
        for el in p.iter():
            if el.tag == W + "t":
                out.append(el.text or "")
            elif el.tag == W + "tab":
                out.append(" ")
            elif el.tag == "{%s}imagedata" % VML:
                k = self.icons.get(el.get("src"))
                if k:
                    out.append("[%s]" % k)
        return re.sub(r"\s+", " ", html.unescape(html.unescape("".join(out)))).strip()

    def style_of(self, p):
        W = self.W
        st = p.find(W + "pPr/" + W + "pStyle")
        return st.get(W + "val") if st is not None else ""

    def walk(self, el):
        W = self.W
        for ch in el:
            if ch.tag == W + "p":
                tx = self.text_of(ch)
                if not tx:
                    continue
                st = self.style_of(ch)
                m = re.match(r"(?i)heading\s*([1-6])", st or "")
                if m:
                    n = int(m.group(1))
                    self.index.append({"level": n, "title": tx, "line": len(self.lines) + 1})
                    self.lines.append("#" * n + " " + tx)
                else:
                    self.lines.append(tx)
            elif ch.tag == W + "tbl":
                self.table(ch)
            else:
                self.walk(ch)

    def table(self, tbl):
        W = self.W
        rows = []
        for tr in tbl.findall(W + "tr"):
            cells = []
            for tc in tr.findall(W + "tc"):
                parts = [self.text_of(p) for p in tc.iter(W + "p")]
                cells.append(" / ".join(x for x in parts if x))
            if any(cells):
                rows.append("| " + " | ".join(cells) + " |")
        if rows:
            self.lines.extend(["<table>"] + rows + ["</table>"])


def parse_wordml2003(data):
    s = data.decode("utf-8", errors="replace")
    icons = {}
    for name, b64 in re.findall(r'<w:binData w:name="(wordml://[0-9A-Fa-f]+)"[^>]*>(.*?)</w:binData>', s, re.S):
        try:
            icons[name] = classify_icon(base64.b64decode(b64))
        except Exception:
            icons[name] = None
    root = ET.fromstring(data)
    ex = Extractor(W2003, icons)
    body = root.find(".//{%s}body" % W2003)
    ex.walk(body)
    return ex


def parse_docx(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("word/document.xml"))
    ex = Extractor(W2006, {})
    ex.walk(root.find("{%s}body" % W2006))
    ex.lines.insert(0, "NOTE: .docx input, rating icons are not read; use the alert text to decide ratings.")
    return ex


def meta_from(lines, index):
    """Best-effort header facts. Always confirm them against the report text."""
    meta = {}
    head = "\n".join(lines[:3])
    m = re.search(r"(\d{2}\.\d{2}\.\d{4})\s*(\d{2}\.\d{2}\.\d{4})", head)
    if m:
        meta["period_from"], meta["period_to"] = m.group(1), m.group(2)
    for h in index:
        m = re.search(r"(?:Performance Indicators for|Workload of System|Overview System|Performance Overview)\s+([A-Z0-9]{3})\b", h["title"])
        if m:
            meta["system_id"] = m.group(1)
            break
    m = re.search(r"(SAP S/4HANA \d{4}|SAP BW/4HANA[ \d.]*|SAP NetWeaver[ \d.]*|SAP ERP[ \d.]*|SAP BW[ \d.]*)", head)
    if m:
        meta["product_hint"] = m.group(1).strip()
    m = re.search(r"(Productive|Non-productive|Test|Development)", head)
    if m:
        meta["status_hint"] = m.group(1)
    return meta


def key_section(ex):
    """Service Summary block: alerts decisive for the rating, alert overview, check overview."""
    heads = [h for h in ex.index if h["level"] == 1]
    if not heads:
        return []
    start = heads[0]["line"] - 1
    end = len(ex.lines)
    for h in heads[1:]:
        if h["title"].lower().startswith(("service data quality", "software configuration")):
            end = h["line"] - 1
            break
    return ex.lines[start:end]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--out", default="ewa_extract")
    a = ap.parse_args()
    with open(a.file, "rb") as f:
        data = f.read()
    if data[:2] == b"PK":
        ex = parse_docx(a.file)
    elif b"wordDocument" in data[:500] or b"WordML" in data[:500] or data.lstrip()[:5] == b"<?xml":
        ex = parse_wordml2003(data)
    else:
        sys.exit("Unsupported file. Save the EWA as Word (.doc/.docx) or ask for the .DOC download from SolMan.")
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "ewa_text.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(ex.lines))
    with open(os.path.join(a.out, "ewa_index.json"), "w", encoding="utf-8") as f:
        json.dump(ex.index, f, indent=1, ensure_ascii=False)
    with open(os.path.join(a.out, "ewa_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta_from(ex.lines, ex.index), f, indent=1, ensure_ascii=False)
    with open(os.path.join(a.out, "ewa_key.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(key_section(ex)))
    rated = sum(len(re.findall(r"\[[RYGi-]\]", l)) for l in ex.lines)
    print("lines: %d  headings: %d  rating icons read: %d" % (len(ex.lines), len(ex.index), rated))
    print("wrote", os.path.join(a.out, "ewa_text.md"))


if __name__ == "__main__":
    main()
