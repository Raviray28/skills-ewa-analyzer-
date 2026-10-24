# Rating rubric

Use this so two analysts (or two runs) give the same ratings. Where the report states its own threshold, use the report's. These defaults are the method used for the reference analyses; the customer may override them.

## 1. Priority of an action item
| Priority | Use when |
|---|---|
| **Critical** | The report rates it RED, or it threatens recoverability (failed or irregular log/data backups), security exposure in production (SAP_ALL, debug/replace, unrestricted table access, no audit), loss of vendor support (maintenance end date within about 12 months, support packages outside the security-note window), or a capacity limit about to be hit (memory near allocation limit, data volume above 90%). |
| **High** | YELLOW with a clear operational or business effect: capacity 80 to 90% used, high ABAP dump counts, failing or backed-up RFC/qRFC/IDoc, number ranges above about 80%, replication problems, long-pending queues, inconsistent data. |
| **Medium** | YELLOW or hygiene items without immediate impact: parameter recommendations, consistency-check scheduling, side-effect notes, data quality, housekeeping that is not yet urgent. |
| **Low** | Information, deprecations, strategic or roadmap items. |

One finding per action item. Merge duplicates (same cause, same fix). Split items with different owners.

## 2. Category words (keep consistent)
HANA Backup, HANA HotNews, HANA Memory, HANA Disk Capacity, HANA Replication, HANA Stability, HANA Configuration, HANA Growth, Security, Maintenance, Upgrade Planning, ABAP Dumps, RFC / qRFC, RFC / bgRFC / IDoc, Number Ranges, Transport Management, Database Housekeeping, Data Quality, Performance, Gateway / Fiori, Business Process, Side-effect Notes, Strategic / ALM. Add system-specific ones (EWM, BW, and so on) when needed.

## 3. Owner
Basis, HANA DBA, Security Team, ABAP / Functional, Infra, Management, plus functional teams named in the report's business areas. Use the customer's own team names if the user gives them. When unsure write the team most likely to do the first step, usually Basis.

## 4. Health scores (illustrative)
Six areas: Security, Performance, Capacity, Availability, Operations, Maintenance. Score 0 to 100 from the alerts in each area:
| Situation in the area | Score band |
|---|---|
| No alerts, all green | 90 to 100 |
| Information only | 80 to 89 |
| Yellow alerts only, no operational effect | 55 to 79 |
| Several yellows, or one red with a mitigation | 35 to 54 |
| Red alerts with business or security exposure | 20 to 34 |
| Multiple reds including a decisive red alert | 0 to 19 |
Overall score = the average of the six, rounded. Overall label: CRITICAL if the EWA overall rating is RED, ATTENTION if YELLOW, HEALTHY if GREEN. The files carry the note that this is not an SAP metric; keep it.

## 5. Status words for snapshot and KPI tables
- **Good**: within threshold. **Watch**: within threshold but trending the wrong way. **Warning**: threshold crossed, no immediate risk. **Critical**: red in the report or a risk to recovery, security or support. **Info**: a figure with no threshold.

## 6. Default KPI thresholds
Use the report's own threshold if shown. Otherwise:
| KPI | Default threshold |
|---|---|
| Availability | above 99.9% |
| Average dialog response time | below 1,000 ms |
| DB request time in dialog | below 100 ms |
| CPU on database server | below 80% |
| ABAP dumps per week | below 50 (the EWA alerts above 30) |
| HANA data volume used | below 80% |
| HANA log volume used | below 80% |
| Database growth per month | below 15 GB (internal guideline, adjust per customer) |
Always show the previous value in `kpi_note` when a previous analysis exists.

## 7. What to look for (checklist by area)
- **Recoverability:** log backup counts per day and failures, data backup frequency and success, backup volume free space.
- **HANA:** critical revisions and HotNews notes for the installed revision, memory against allocation limit, table memory above 50% of the limit, data and log volume, replication state, delta merge failures, deadlocks, consistency checks, audit policies (tenant and system database).
- **Security:** SAP_ALL users per client, debug/replace authorisation, S_TABU_DIS with full access, default passwords of standard users, TMSADM, RFC with stored credentials, age of support packages against the 24-month security-note window.
- **Maintenance:** end of mainstream maintenance for the product, kernel age, database and OS maintenance, SAPUI5 / Fiori front-end server maintenance.
- **Performance and workload:** dialog and DB response times, peak times, top transactions, UI technology response.
- **Operations:** availability, ABAP dumps by runtime error, update errors, number ranges near exhaustion, transport overtakers and sequencing, table reorganisation, recommended background jobs.
- **Integration:** qRFC/tRFC/bgRFC errors and backlog, IDocs in error.
- **Data volume:** largest tables, growth drivers, archiving and housekeeping.
- **Business key figures:** overdue and backlog documents, only when the report includes them. These are often collected quarterly, so say when the figures are unchanged.

## 8. Writing style
- Findings: one headline, then evidence in "technical", then impact, then the action. Use report wording for SAP Notes and checks.
- Recommendations start with a verb (Review, Apply, Schedule, Restrict, Approve) and name the SAP Note or transaction where the report does.
- Plain business language in `impact`, `top_risks.detail` and `conclusion`.
- No invented numbers. Mark inferences ("estimated", "if the trend continues").
