---
name: ewa-analyzer
description: Analyse an SAP EarlyWatch Alert (EWA) report and produce a prioritised Excel action register plus a 2-slide management dashboard. Use when the user attaches or mentions an EWA report (.DOC, .docx) and wants analysis, findings, health score, action items, or a management summary. Optional month-on-month comparison when a previous analysis is supplied.
---

# EWA analyzer

Turns an SAP EarlyWatch Alert report into:
1. an Excel workbook: Executive Summary, Action Items register, detail sheets, optional "Change vs previous" sheet;
2. a 2-slide PowerPoint dashboard for management.

You (the AI) do the analysis. Fixed scripts build the files, so the layout is identical every time.

## Ground rules
- Every number, date, SAP Note and system name must come from the report. Do not invent values. If something is an inference (for example "about 5 months until 90%"), say so in the text.
- Health scores are the analyst's illustrative scoring, not an SAP metric. The files already say this; never present them as official.
- Do not send report content to any other service, and do not paste it into other chats. Output files stay in the user's folder.
- If the user wants a shareable sample, replace customer name, system IDs, host names and user names with placeholders before writing the findings.
- Read `references/rubric.md` before rating anything. Read `references/findings_schema.md` before writing findings.json.

## Step 0: check what you can run
Run `python --version` (or `python3 --version`) and `pip install -r requirements.txt` from this skill folder.
- Python works: follow Steps 1 to 7 (full output).
- Python or packages cannot be installed: use "Level 1" at the bottom (analysis as tables, no files).

## Step 1: extract the report
```
python scripts/parse_ewa.py "<path to EWA file>" --out ewa_extract
```
This writes `ewa_text.md` (the whole report as text, with rating icons turned into [R] red, [Y] yellow, [G] green, [i] info), `ewa_index.json` (headings with line numbers), `ewa_meta.json` (system id, period) and `ewa_key.md` (the Service Summary). It prints how many rating icons were read. If it prints 0 for a .DOC, tell the user ratings could not be read and rely on the alert wording.

The full text is long (hundreds of KB). Never load it whole. Use `ewa_key.md` and read other sections one at a time:
```
python scripts/section.py ewa_extract --list                 # all headings
python scripts/section.py ewa_extract "Program Errors"       # one section
```

## Step 2: read the summary first
Read `ewa_key.md` completely. Note: overall rating, "Alerts Decisive For Red Report", every [R] and [Y] in "Alert Overview", and the "Check Overview" topic list.

## Step 3: read the detail for every red and yellow item
For each [R] alert read its section; for each [Y] read the section if it affects security, recoverability, capacity, support status or business operations. Always also read these if present: performance indicators, hardware/capacity, workload and performance, availability, program errors (ABAP dumps), number ranges, security, transport management, RFC/qRFC, HANA sections (backup, memory, disk, alerts, parameters), upgrade planning, trend analysis. Add area-specific sections (for example EWM, BW, Gateway/Fiori) when the report has them.

Collect: the finding, the evidence (numbers, dates, SAP Notes), the business impact, the recommendation, a suggested owner.

## Step 4: previous analysis (optional)
Ask the user once: "Do you have last cycle's findings file (the `*_findings.json` from the last run) or last cycle's EWA?" 
- If a previous findings.json is given: build the `previous` block (see schema) by comparing KPIs, counts, versions and key detail values, 15 to 30 indicators. Mark trend as Improved, Worse, Slightly worse, Unchanged or Increased.
- If only the previous EWA is given: run Step 1 on it too, read the same sections, then compare.
- If neither is given: leave `previous` out. Do not guess a comparison. The workbook then has no comparison sheet.

## Step 5: write findings.json
Follow `references/findings_schema.md` exactly (keys, limits, wording length). Order action items by priority, then by importance. Use `references/rubric.md` for priority, owner, scores and thresholds. Save as `findings.json` in the user's working folder.

## Step 6: build the files
```
python scripts/build_all.py findings.json --out outputs
```
If it reports problems with findings.json, fix them and rerun. If the pptx step prints "text may overflow", shorten that text.

## Step 7: check and hand over
- Open the results (or render them) and check: counts on the Executive Summary match the action items; no text is cut off on the slides; every figure traces to the report.
- Tell the user: where the files are; the overall rating and score; the top 3 findings; assumptions and inferences you made; anything you could not read; and that `outputs/*_findings.json` must be kept for next month's comparison.
- Do not claim the analysis is complete if sections were skipped. List what you did not read.

## Level 1: no Python available
Do Steps 2 to 4 by reading the report directly (attach file, or paste sections). Then reply with, in this order:
1. Overall rating, decisive alerts, illustrative score (rubric).
2. Findings table: `# | Priority | Category | Finding | Technical detail | Business impact | Recommendation | Owner`.
3. KPI table: `KPI | This period | Threshold | Status`.
4. Top 6 immediate actions and a 6 to 8 sentence conclusion.
5. If a previous analysis exists: change table `Indicator | Previous | Current | Trend`.
Tell the user to paste the findings table into `templates/EWA_Analysis_Template.xlsx` (the counts on its summary sheet use formulas) and the summary into `templates/EWA_Dashboard_Template.pptx`. Say clearly that rating icons may be missed without the parser, so a consultant should review the ratings.

## Limits
Built and tested on an S/4HANA 2021 EWA (HANA database, EWM) saved as a Word 2003 XML .DOC. Other system types (BW, ECC, BTP, other databases) use the same method, but sections and thresholds differ: say so, and check categories and detail sheets by hand. PDF EWA reports have no readable rating icons.
