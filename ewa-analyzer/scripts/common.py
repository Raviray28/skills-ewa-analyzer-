"""Shared helpers: load and check findings.json, small utilities. Standard library only."""
import json, re, sys

PRIORITIES = ["Critical", "High", "Medium", "Low"]
STATUS_OK = {"Good", "Watch", "Warning", "Critical", "Info"}


class FindingsError(Exception):
    pass


def load_findings(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise FindingsError("findings.json is not valid JSON: %s" % e)
    normalise(data)
    problems = check(data)
    if problems:
        raise FindingsError("findings.json needs fixing:\n - " + "\n - ".join(problems))
    return data


def _fix_text(x):
    """Repair dashes that turned into '?' when the file was written through a non-UTF-8 console."""
    if isinstance(x, str):
        x = re.sub(r"(?<=[0-9A-Za-z\.]) \? (?=[0-9A-Za-z])", " \u2013 ", x)
        x = re.sub(r"^(RED|YELLOW|GREEN|CRITICAL|ATTENTION|HEALTHY) \? ", lambda m: m.group(1) + " \u2014 ", x)
        return x
    if isinstance(x, list):
        return [_fix_text(i) for i in x]
    if isinstance(x, dict):
        return {k: _fix_text(v) for k, v in x.items()}
    return x


def coverage_warnings(d):
    """Soft checks: tell the analyst when the analysis looks thinner than a full review."""
    w = []
    n = len(d.get("action_items", []))
    if n < 15:
        w.append("only %d action items. A full EWA review usually has 20 to 50: add one item per red or yellow check, "
                 "and one per SAP Note, expiring support date, threshold breach or security finding." % n)
    if not d.get("detail_sheets"):
        w.append("no detail_sheets. Add one sheet per area that is red or yellow (HANA/database, security, "
                 "RFC/queues, ABAP dumps, business process, system-specific areas).")
    if any("?" in str(v) for v in (d.get("meta") or {}).values()):
        w.append("a '?' in meta, probably a lost dash: write findings.json with a UTF-8 file tool, not a console command.")
    return w


def normalise(d):
    """Forgive capitalisation differences (CRITICAL, critical) in status and priority words."""
    for k in list(d.keys()):
        d[k] = _fix_text(d[k])
    for key in ("snapshot", "kpi_table"):
        for x in d.get(key, []) or []:
            if isinstance(x.get("status"), str):
                x["status"] = x["status"].strip().capitalize()
    for x in d.get("action_items", []) or []:
        if isinstance(x.get("priority"), str):
            x["priority"] = x["priority"].strip().capitalize()
    for x in d.get("kpis", []) or []:
        if isinstance(x.get("status"), str):
            x["status"] = x["status"].strip().lower()
    for x in d.get("top_risks", []) or []:
        if isinstance(x.get("severity"), str):
            x["severity"] = x["severity"].strip().upper()


def check(d):
    """Return a list of plain-language problems. Empty list = fine."""
    p = []
    for key in ("meta", "overall", "action_items", "snapshot", "top_risks", "kpis", "kpi_table", "actions", "conclusion"):
        if key not in d:
            p.append("missing section '%s'" % key)
    if p:
        return p
    m = d["meta"]
    for k in ("system_id", "report_date", "period", "prepared_by"):
        if not m.get(k):
            p.append("meta.%s is empty" % k)
    o = d["overall"]
    for k in ("label", "score", "decisive_alert"):
        if k not in o or o[k] in ("", None):
            p.append("overall.%s is empty" % k)
    if not isinstance(o.get("score", 0), (int, float)):
        p.append("overall.score must be a number")
    for i, a in enumerate(d["action_items"], 1):
        if a.get("priority") not in PRIORITIES:
            p.append("action_items[%d].priority must be one of %s" % (i, PRIORITIES))
        for k in ("category", "finding", "recommendation"):
            if not a.get(k):
                p.append("action_items[%d].%s is empty" % (i, k))
    if not d["action_items"]:
        p.append("action_items is empty")
    for i, s in enumerate(d["snapshot"], 1):
        if s.get("status") not in STATUS_OK:
            p.append("snapshot[%d].status must be one of %s" % (i, sorted(STATUS_OK)))
    for i, s in enumerate(d["kpi_table"], 1):
        if s.get("status") not in STATUS_OK:
            p.append("kpi_table[%d].status must be one of %s" % (i, sorted(STATUS_OK)))
    for i, k in enumerate(d["kpis"], 1):
        if k.get("status") not in ("good", "warn", "crit", "info"):
            p.append("kpis[%d].status must be good, warn, crit or info" % i)
    if len(d["kpis"]) != 8:
        p.append("kpis must have exactly 8 entries (found %d)" % len(d["kpis"]))
    if len(d["snapshot"]) > 8:
        p.append("snapshot has %d rows; the slide fits 8" % len(d["snapshot"]))
    if len(d["top_risks"]) > 4:
        p.append("top_risks has %d entries; the slide fits 4" % len(d["top_risks"]))
    if len(d["kpi_table"]) > 10:
        p.append("kpi_table has %d rows; the slide fits 10" % len(d["kpi_table"]))
    for g in ("immediate", "high", "medium"):
        if len(d["actions"].get(g, [])) > 3:
            p.append("actions.%s has more than 3 entries; the slide fits 3 per group" % g)
    if len(d.get("scores", [])) not in (0, 6):
        p.append("scores must have 6 entries (or be left out)")
    return p


def est_lines(text, width_chars):
    n = 0
    for para in str(text).split("\n"):
        n += max(1, -(-len(para) // max(1, int(width_chars))))
    return n


def risk_areas(d):
    """Primary risk area per priority, from the categories used in the action items."""
    out = {}
    for pr in PRIORITIES:
        seen = []
        for a in d["action_items"]:
            if a["priority"] == pr and a["category"] not in seen:
                seen.append(a["category"])
        out[pr] = ", ".join(seen) if seen else "-"
    manual = d.get("risk_areas") or {}
    out.update({k: v for k, v in manual.items() if v})
    return out
