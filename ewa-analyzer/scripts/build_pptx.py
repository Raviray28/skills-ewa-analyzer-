#!/usr/bin/env python3
"""Build the 2-slide EWA management dashboard from findings.json.   python build_pptx.py findings.json out.pptx
Needs: pip install python-pptx"""
import sys
try:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.oxml.ns import qn
    from pptx.util import Inches, Pt
except ImportError:
    sys.exit("python-pptx is not installed. Run: pip install python-pptx")
from common import load_findings, FindingsError

DARK, RED, GREEN, ORANGE, AMBER, NAVY, GREYTXT = "1A1A2E", "C62828", "388E3C", "F57C00", "F9A825", "1A2F55", "666666"
SEV = {"CRITICAL": RED, "HIGH": ORANGE, "ATTENTION": ORANGE, "WARNING": ORANGE, "MEDIUM": AMBER, "LOW": GREEN, "HEALTHY": GREEN}
STATUS_TXT = {"Good": GREEN, "Watch": AMBER, "Warning": ORANGE, "Critical": RED, "Info": NAVY}
KPI_COL = {"good": GREEN, "warn": ORANGE, "crit": RED, "info": NAVY}
WARN = []


def rgb(h):
    return RGBColor.from_string(h)


def shape(slide, x, y, w, h, fill=None, line=None, rounded=False):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        s.adjustments[0] = 0.08
    if fill:
        s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line); s.line.width = Pt(1)
    else:
        s.line.fill.background()
    st = s._element.find(qn('p:style'))
    if st is not None:
        s._element.remove(st)  # drop the theme style so no shadow or outline is inherited
    return s


def fit_pt(text, w, h, max_pt, min_pt=6, bold=False):
    """Largest font size (pt) whose estimated wrapped text fits the box; warns if even min does not."""
    for pt in [x / 2 for x in range(int(max_pt * 2), int(min_pt * 2) - 1, -1)]:
        cpl = max(1, w * 72 / (pt * (0.56 if bold else 0.5)))
        lines = sum(max(1, -(-len(p) // int(cpl))) for p in str(text).split("\n"))
        if lines * pt * 1.2 / 72 <= h:
            return pt
    WARN.append("text may overflow its box: %r" % str(text)[:60])
    return min_pt


def text(slide, x, y, w, h, t, pt=9, bold=False, color="000000", align="l", italic=False, anchor="top", fit=True, runs=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "mid": MSO_ANCHOR.MIDDLE}[anchor]
    plain = t if runs is None else "".join(r[0] for r in runs)
    size = fit_pt(plain, w, h, pt, 6, bold) if fit else pt
    p = tf.paragraphs[0]
    p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
    for rt, rbold, rcolor in (runs or [(t, bold, color)]):
        r = p.add_run(); r.text = rt
        r.font.name, r.font.size, r.font.bold, r.font.italic = "Arial", Pt(size), rbold, italic
        r.font.color.rgb = rgb(rcolor)
    return tb


def frame(slide, d, title, page):
    m, o = d["meta"], d["overall"]
    shape(slide, 0, 0, 13.333, 1.05, DARK)
    shape(slide, 0, 1.05, 13.333, 0.06, RED)
    text(slide, 0.3, 0.12, 5.4, 0.32, title, 16, True, "FFFFFF", fit=False)
    text(slide, 0.3, 0.46, 5.4, 0.25, "EarlyWatch Alert Report — %s" % m["report_date"], 9, False, "B0B7C3", fit=False)
    for x, w, lab, val in ((5.3, 1.7, "CUSTOMER", m.get("customer", "")), (7.15, 2.1, "LANDSCAPE", m.get("landscape_short") or m["system_id"]), (9.45, 1.5, "REPORTING PERIOD", m.get("period_short") or m["period"])):
        text(slide, x, 0.14, w, 0.2, lab, 7, True, "9FA8DA", fit=False)
        text(slide, x, 0.36, w, 0.5, val, 10, True, "FFFFFF")
    col = SEV.get(o["label"].upper(), RED)
    shape(slide, 11.05, 0.14, 2.0, 0.78, col, rounded=True)
    text(slide, 11.15, 0.18, 1.8, 0.18, "OVERALL HEALTH", 7, False, "FFFFFF", fit=False)
    text(slide, 11.15, 0.38, 1.85, 0.3, "%s — %d/100" % (o["label"].upper(), o["score"]), 12, True, "FFFFFF")
    text(slide, 11.15, 0.68, 1.8, 0.2, o.get("rating_sub", ""), 7, False, "FFFFFF")
    shape(slide, 0, 7.28, 13.333, 0.22, DARK)
    text(slide, 0.3, 7.31, 12.7, 0.18, "CONFIDENTIAL  |  %s  ·  %s  ·  %s  |  Page %d of 2" % (m.get("customer", ""), m["system_id"], m.get("month_label", ""), page), 7, False, "FFFFFF", fit=False)


def section(slide, x, y, w, t):
    text(slide, x, y, w, 0.3, t, 11, True, "1A1A1A", fit=False)


def bar_color(score):
    return RED if score <= 20 else ORANGE if score < 50 else AMBER if score < 80 else GREEN


def borders(cell, color="D0D0D0"):
    from lxml import etree
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        ln = etree.SubElement(tcPr, qn(tag), w="6350", cap="flat", cmpd="sng", algn="ctr")
        sf = etree.SubElement(ln, qn("a:solidFill"))
        etree.SubElement(sf, qn("a:srgbClr"), val=color)
        etree.SubElement(ln, qn("a:prstDash"), val="solid")
    # schema order: borders must come before the cell fill
    fills = [c for c in tcPr if c.tag in (qn("a:solidFill"), qn("a:noFill"))]
    for f in fills:
        tcPr.remove(f); tcPr.append(f)


def table(slide, x, y, widths, rows, row_h, status_col=None, font_pt=8):
    gt = slide.shapes.add_table(len(rows), len(widths), Inches(x), Inches(y), Inches(sum(widths)), Inches(row_h * len(rows)))
    tbl = gt.table
    tblPr = gt._element.graphic.graphicData.tbl.tblPr
    tblPr.set("firstRow", "0"); tblPr.set("bandRow", "0")
    for i, w in enumerate(widths):
        tbl.columns[i].width = Inches(w)
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(row_h)
        for c, v in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid(); cell.fill.fore_color.rgb = rgb(NAVY if r == 0 else "FFFFFF")
            borders(cell)
            tf = cell.text_frame; tf.word_wrap = True
            run = tf.paragraphs[0].add_run(); run.text = str(v)
            run.font.name = "Arial"
            run.font.size = Pt(font_pt if r else font_pt)
            if r == 0:
                run.font.bold, run.font.color.rgb = True, rgb("FFFFFF")
            elif status_col is not None and c == status_col:
                run.font.bold, run.font.color.rgb = True, rgb(STATUS_TXT.get(str(v), NAVY))
            else:
                run.font.color.rgb = rgb("222222")
            # table cell text: shrink if it would not fit
            if r and c == len(row) - 1 and status_col != c:
                pass
    return tbl


def slide_one(prs, d):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    frame(s, d, "SAP EWA  SUMMARY", 1)
    section(s, 0.3, 1.28, 5.6, "1.  OVERALL SYSTEM HEALTH SCORE")
    scores = d.get("scores") or []
    for i, sc in enumerate(scores):
        y = 1.66 + i * 0.335
        text(s, 0.3, y, 1.35, 0.3, sc["area"], 9, False, "222222", fit=False)
        shape(s, 1.7, y + 0.03, 3.35, 0.22, "E0E0E0")
        c = bar_color(sc["score"])
        shape(s, 1.7, y + 0.03, max(0.02, 3.35 * sc["score"] / 100), 0.22, c)
        text(s, 5.15, y, 0.75, 0.3, "%d/100" % sc["score"], 9, True, c, fit=False)
    text(s, 0.3, 3.7, 5.6, 0.25, d.get("score_note", "Illustrative Basis-team scoring derived from EWA finding severity — not an official SAP metric."), 7, False, GREYTXT, italic=True)
    section(s, 6.05, 1.28, 6.9, "2.  KEY SNAPSHOT")
    rows = [["Area", "Status", "Comment"]] + [[x["area"], x["status"], x["comment"]] for x in d["snapshot"]]
    table(s, 6.05, 1.62, [1.6, 0.95, 4.43], rows, 3.55 / max(len(rows), 9) if len(rows) <= 9 else 0.39, status_col=1, font_pt=8)
    section(s, 0.3, 4.05, 5.6, "3.  TOP RISKS — Business Impact")
    for i, rk in enumerate(d["top_risks"]):
        y = 4.4 + i * 0.64
        shape(s, 0.3, y, 0.85, 0.56, SEV.get(rk["severity"].upper(), RED), rounded=True)
        text(s, 0.3, y, 0.85, 0.56, rk["severity"].upper(), 8, True, "FFFFFF", "c", anchor="mid")
        text(s, 1.25, y - 0.02, 4.65, 0.28, rk["title"], 9, True, "111111")
        text(s, 1.25, y + 0.26, 4.65, 0.32, rk["detail"], 7.5, False, GREYTXT)
    section(s, 6.05, 5.28, 6.9, "4.  KEY KPI DASHBOARD — This Period")
    for i, k in enumerate(d["kpis"]):
        x, y = 6.05 + (i % 4) * 1.735, 5.6 + (i // 4) * 0.65
        c = KPI_COL[k["status"]]
        shape(s, x, y, 1.69, 0.6, "F5F5F5")
        shape(s, x, y, 0.06, 0.6, c)
        text(s, x + 0.08, y + 0.04, 1.58, 0.28, k["value"], 14, True, c, "c", fit=True)
        text(s, x + 0.04, y + 0.33, 1.62, 0.14, k["label"].upper(), 6.5, True, "444444", "c")
        text(s, x + 0.04, y + 0.46, 1.62, 0.13, k.get("target", ""), 6, False, GREYTXT, "c")
    shape(s, 0.3, 6.97, 12.73, 0.27, "FFEBEE")
    text(s, 0.4, 6.99, 12.5, 0.24, d.get("banner", ""), 8, True, "B71C1C", anchor="mid")


def slide_two(prs, d):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    frame(s, d, "SAP EWA EXECUTIVE SUMMARY", 2)
    section(s, 0.3, 1.28, 5.9, "5.  KPI SNAPSHOT vs. SAP-RECOMMENDED THRESHOLDS")
    text(s, 0.3, 1.55, 5.9, 0.3, d.get("kpi_note", ""), 7, False, GREYTXT, italic=True)
    rows = [["KPI", "This Period", "Threshold", "Status"]] + [[k["kpi"], k["value"], k["threshold"], k["status"]] for k in d["kpi_table"]]
    table(s, 0.3, 1.9, [2.3, 1.3, 1.2, 1.1], rows, 0.327, status_col=3, font_pt=8)
    section(s, 6.35, 1.28, 6.7, "6.  RECOMMENDED ACTIONS")
    y = 1.62
    for key, label, bg, dot in (("immediate", "Immediate Decisions Required", "FFEBEE", RED), ("high", "High Priority Actions", "FFF3E0", ORANGE), ("medium", "Medium Priority", "E8F5E9", AMBER)):
        items = d["actions"].get(key, [])
        if not items:
            continue
        shape(s, 6.35, y, 6.68, 0.3, bg)
        dotshape = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(6.45), Inches(y + 0.07), Inches(0.16), Inches(0.16))
        dotshape.fill.solid(); dotshape.fill.fore_color.rgb = rgb(dot); dotshape.line.fill.background()
        text(s, 6.7, y + 0.04, 6.2, 0.24, label, 9.5, True, "B71C1C" if key == "immediate" else "E65100" if key == "high" else "8D6E00", fit=False)
        for j, it in enumerate(items):
            yy = y + 0.36 + j * 0.3
            text(s, 6.45, yy, 4.4, 0.27, it["text"], 8, False, "222222")
            text(s, 10.9, yy, 2.05, 0.27, it.get("owner", ""), 7.5, False, GREYTXT, "r", italic=True)
        y += 0.36 + len(items) * 0.3 + 0.1
    section(s, 0.3, 5.85, 12.7, "7.  CONCLUSION")
    shape(s, 0.3, 6.1, 12.73, 1.15, "FFEBEE", "C62828")
    shape(s, 0.42, 6.22, 0.9, 0.9, RED, rounded=True)
    text(s, 0.42, 6.27, 0.9, 0.4, "!", 24, True, "FFFFFF", "c", fit=False)
    text(s, 0.42, 6.7, 0.9, 0.4, d.get("conclusion_tag", "Action Required"), 6.5, True, "FFFFFF", "c")
    text(s, 1.5, 6.16, 11.4, 1.03, d["conclusion"], 8.5, False, "222222")


def build(findings_path, out_path):
    d = load_findings(findings_path)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    slide_one(prs, d)
    slide_two(prs, d)
    prs.core_properties.title = "SAP EWA dashboard %s %s" % (d["meta"]["system_id"], d["meta"]["period"])
    prs.core_properties.author = d["meta"]["prepared_by"]
    prs.save(out_path)
    for w in WARN:
        print("WARNING:", w)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    try:
        print("wrote", build(sys.argv[1], sys.argv[2]))
    except FindingsError as e:
        sys.exit(str(e))
