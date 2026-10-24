# findings.json schema

One JSON file drives both output files. The builders check it and print plain-language problems.
A complete working example is in `examples/example_findings.json` (customer data replaced by placeholders). Copy its structure.

## Top-level keys

| Key | Required | What it is |
|---|---|---|
| `meta` | yes | customer, system and period text |
| `overall` | yes | overall rating, score, decisive alert |
| `system_facts` | no | rows `[label, value]` for the Executive Summary (product, database, OS, users, size, availability) |
| `scores` | no | exactly 6 `{area, score}` for the health bars (see rubric); leave out to hide the bars |
| `snapshot` | yes | up to 8 `{area, status, comment}` for slide 1 |
| `top_risks` | yes | up to 4 `{severity, title, detail}` for slide 1 |
| `kpis` | yes | exactly 8 cards `{value, label, target, status}` |
| `banner` | yes | one-line red banner on slide 1 |
| `kpi_table` | yes | up to 10 `{kpi, value, threshold, status}` for slide 2 |
| `kpi_note` | no | one italic line above the KPI table (what changed vs previous) |
| `actions` | yes | `{immediate: [...], high: [...], medium: [...]}` each item `{text, owner}`, max 3 per group |
| `conclusion` | yes | the closing paragraph on slide 2 |
| `action_items` | yes | the full register (any number) |
| `top_actions` | no | 4 to 6 numbered sentences for the Executive Summary sheet |
| `risk_areas` | no | override text per priority; otherwise built from the categories used |
| `detail_sheets` | no | extra sheets, see below |
| `previous` | no | comparison with last cycle, see below. Leave out when there is no previous analysis |

## meta
```json
{"customer": "Example Customer", "system_id": "ABC", "product": "SAP S/4HANA 2021, Productive",
 "landscape": "Example Landscape", "landscape_short": "ABC - SAP S/4HANA 2021 + HANA",
 "period": "12.10.2026 - 18.10.2026", "period_short": "12 Oct - 18 Oct 2026",
 "report_date": "19/10/2026", "month_label": "October 2026",
 "prepared_by": "Your Name, SAP Basis Consultant"}  (use the name the user gives you; if unknown, ask once, do not invent one)
```
`system_id`, `period`, `report_date`, `prepared_by` are required. `ewa_meta.json` from the parser helps; confirm against the report.

## overall
```json
{"label": "CRITICAL", "score": 46, "rating_text": "RED - Severe issues detected that may cause business impact",
 "decisive_alert": "text of the alerts decisive for the red rating", "rating_sub": "RED-rated EWA report"}
```
`label` is CRITICAL (EWA red), ATTENTION (yellow) or HEALTHY (green). `score` = rounded average of the six `scores`.

## action_items (each)
```json
{"priority": "Critical", "category": "HANA Backup", "finding": "short headline",
 "technical": "evidence: numbers, dates, SAP Notes", "impact": "business impact",
 "recommendation": "what to do", "owner": "Basis", "status": "Open"}
```
`priority` is Critical, High, Medium or Low. `status` is Open, Open - New, In progress, Closed.

## detail_sheets (each, optional)
```json
{"name": "HANA Deep Dive", "title": "SAP HANA Database - Technical Detail",
 "columns": ["Metric", "Value", "Threshold / Note"], "widths": [42, 52, 55],
 "rows": [["Row store size", "73 GB", "Keep optimised (Note 2388483)"]], "hidden": false}
```
Use one sheet per major area (HANA, security, RFC/queues, ABAP dumps, business process, plus system-specific areas). Sheet name up to 31 characters. Set `hidden: true` for long reference sheets.

## previous (optional)
```json
{"short_label": "Sept", "period": "07.09 - 13.09.2026",
 "rows": [{"indicator": "ABAP dumps (period)", "previous": "486", "current": "411", "trend": "Improved", "comment": "..."}],
 "closed": ["Items reported last cycle and gone now"], "new": ["Items new this cycle"]}
```
`trend` is one of Improved, Worse, Slightly worse, Unchanged, Increased.

## Status and severity words
- `snapshot.status` and `kpi_table.status`: Good, Watch, Warning, Critical, Info.
- `kpis.status`: good, warn, crit, info.
- `top_risks.severity`: CRITICAL, HIGH, MEDIUM, LOW.
Capitalisation is forgiven.

## Text length (so slides do not overflow)
| Field | Max characters |
|---|---|
| snapshot comment | about 90 |
| top risk title | about 80 |
| top risk detail | about 170 |
| kpi value | about 10 |
| kpi label | about 24 |
| kpi_table kpi | about 40 |
| actions text | about 75 |
| banner | about 200 |
| conclusion | about 1,000 |
Action item cells in Excel can be longer; keep each under 500 characters.
