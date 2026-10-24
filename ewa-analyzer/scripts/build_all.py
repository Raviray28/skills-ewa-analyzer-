#!/usr/bin/env python3
"""Build the Excel analysis and the 2-slide dashboard from one findings.json.

    python build_all.py findings.json --out outputs --prefix ABC_EWA_Oct2026

Writes  outputs/<prefix>_Analysis.xlsx, outputs/<prefix>_Dashboard.pptx and a copy of the findings
(outputs/<prefix>_findings.json). Keep that copy: next month it is the "previous analysis" input.
"""
import argparse, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
missing = []
for mod, pkg in (("openpyxl", "openpyxl"), ("pptx", "python-pptx")):
    try:
        __import__(mod)
    except ImportError:
        missing.append(pkg)
if missing:
    sys.exit("Missing Python packages: %s\nInstall with:  pip install %s" % (", ".join(missing), " ".join(missing)))

from common import load_findings, coverage_warnings, FindingsError
import build_xlsx, build_pptx

ap = argparse.ArgumentParser()
ap.add_argument("findings")
ap.add_argument("--out", default="outputs")
ap.add_argument("--prefix", default=None)
a = ap.parse_args()
try:
    d = load_findings(a.findings)
except FindingsError as e:
    sys.exit(str(e))
m = d["meta"]
prefix = a.prefix or "%s_EWA_%s" % (m["system_id"], (m.get("month_label") or m["report_date"]).replace(" ", "").replace("/", "-"))
os.makedirs(a.out, exist_ok=True)
x = build_xlsx.build(a.findings, os.path.join(a.out, prefix + "_Analysis.xlsx"))
p = build_pptx.build(a.findings, os.path.join(a.out, prefix + "_Dashboard.pptx"))
shutil.copyfile(a.findings, os.path.join(a.out, prefix + "_findings.json"))
counts = {}
for it in d["action_items"]:
    counts[it["priority"]] = counts.get(it["priority"], 0) + 1
print("Action items:", ", ".join("%s %d" % (k, counts.get(k, 0)) for k in ("Critical", "High", "Medium", "Low")))
print("Detail sheets:", len(d.get("detail_sheets", [])), "| comparison sheet:", "yes" if d.get("previous") else "no (no previous analysis given)")
for w in coverage_warnings(d):
    print("COVERAGE WARNING:", w)
print("Wrote:\n ", x, "\n ", p)
