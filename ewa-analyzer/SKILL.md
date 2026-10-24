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

### Coverage rules (do not skip)
A thin analysis is the most common failure. Work through the report like a checklist, not like a summary:
1. Run `python scripts/section.py ewa_extract --list` and go through the headings area by area. Every heading marked [R] or [Y] needs at least one action item, or a written reason in the final message why it does not.
2. One finding per action item. Do not merge a SAP Note, an expiring support date, a threshold breach, a failed job and a security finding into one row. A full EWA normally gives 20 to 50 items. If you have fewer than 15, you have merged or skipped too much: go back to the report.
3. Cover every area that has a section in the report: HANA/database (backup, memory, disk, alerts, parameters, HotNews), security, performance, ABAP dumps, RFC/qRFC, transports, number ranges, upgrade and maintenance dates, capacity and growth, plus system-specific areas (for example EWM, BW, Gateway, Fiori).
4. Write one detail sheet for each area that is red or yellow (at least HANA/database, security, ABAP dumps, and any business-process or system-specific area that has findings). A detail sheet is a table of metrics and values copied from the report with the threshold or note next to each.
5. Medium and Low items count too: yellow checks, hygiene items and housekeeping belong in the register, so the management view and the technical view come from the same list.

## Step 4: previous analysis (optional)
Ask the user once: "Do you have last cycle's findings file (the `*_findings.json` from the last run) or last cycle's EWA?" 
- If a previous findings.json is given: build the `previous` block (see schema) by comparing KPIs, counts, versions and key detail values, 15 to 30 indicators. Mark trend as Improved, Worse, Slightly worse, Unchanged or Increased.
- If only the previous EWA is given: run Step 1 on it too, read the same sections, then compare.
- If neither is given: leave `previous` out. Do not guess a comparison. The workbook then has no comparison sheet.

## Step 5: write findings.json
Follow `references/findings_schema.md` exactly (keys, limits, wording length). Order action items by priority, then by importance. Use `references/rubric.md` for priority, owner, scores and thresholds. Save as `findings.json` in the user's working folder. Write the file with the file-creation tool (UTF-8), never with a console command such as echo or Set-Content: a Windows console turns dashes and other symbols into "?".

## Step 6: build the files
```
python scripts/build_all.py findings.json --out outputs
```
If it reports problems with findings.json, fix them and rerun. If the pptx step prints "text may overflow", shorten that text.

## Step 7: check and hand over
- Open the results (or render them) and check: counts on the Executive Summary match the action items; no text is cut off on the slides; every figure traces to the report.
- If `build_all.py` prints a COVERAGE WARNING, go back to Step 3 and fix it before you hand over.
- End your reply in the chat with this block, so the user never has to search for anything:
  1. Overall rating and the six scores as a small table.
  2. The top 3 to 4 risks, one line each.
  3. Counts: action items by priority, detail sheets, comparison sheet yes/no.
  4. The full paths of the two files in `outputs\` (the .xlsx and the .pptx).
  5. Assumptions and inferences you made, and anything you did not read.
  6. A reminder to keep `outputs/*_findings.json` for next month's comparison.
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
