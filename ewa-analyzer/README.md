# EWA analyzer skill

Turns an SAP EarlyWatch Alert report into a prioritised Excel action register and a 2-slide management dashboard, using your AI assistant (for example GitHub Copilot in VS Code) plus small Python scripts.

## What you get
- `*_Analysis.xlsx`: Executive Summary, Action Items (filterable), detail sheets, and a comparison sheet when a previous analysis is supplied.
- `*_Dashboard.pptx`: health score, snapshot, top risks, KPI cards, recommended actions, conclusion.
- `*_findings.json`: the analysis data. Keep it; next month it is the "previous analysis".

## Install (GitHub Copilot in VS Code)
1. Copy the `ewa-analyzer` folder into your project as `.github/skills/ewa-analyzer/`, or into `~/.copilot/skills/ewa-analyzer/` for all projects.
2. Open a terminal in VS Code and install the packages once: `pip install -r .github/skills/ewa-analyzer/requirements.txt` (Python 3.9 or newer).
3. Put the EWA report (.DOC or .docx) in your project folder.
4. Open Copilot Chat, switch to **Agent** mode, and ask: `/ewa-analyzer analyse the attached EWA report` (or describe the task; the skill loads when it matches). Attach the file with the paperclip or name its path.
5. Approve the commands when VS Code asks. Results appear in the `outputs` folder.
If the skill does not show up, check your VS Code and Copilot versions: agent skills support is recent and may need a setting enabled.

## Month-on-month comparison
Give the assistant last month's `*_findings.json` (or last month's EWA). Without it, the comparison sheet is left out.

## No Python on the machine
The skill falls back to tables in the chat. Paste them into `templates/EWA_Analysis_Template.xlsx` and `templates/EWA_Dashboard_Template.pptx`. Rating icons may be missed without the parser, so review the ratings.

## Data handling
- The report contains customer data. Use only an AI service approved for it.
- Do not commit EWA reports or generated outputs to a repository. The folder `.gitignore` excludes common ones.
- To share a sample, replace customer name, system IDs, hosts and users first.

## Layout
```
SKILL.md                      instructions the AI follows
references/rubric.md          priority, score and threshold rules
references/findings_schema.md findings.json format
scripts/parse_ewa.py          reads the EWA (text + red/yellow/green icons)
scripts/section.py            prints one section of a long report
scripts/build_xlsx.py         Excel builder
scripts/build_pptx.py         PowerPoint builder
scripts/build_all.py          runs both builders
examples/example_findings.json  worked example (placeholders, no customer data)
templates/                    blank Excel and PowerPoint for the no-Python route
```

## Status
First version. Tested on an S/4HANA 2021 EWA (HANA, EWM). Other system types need a check of categories and detail sheets. The analysis quality depends on the AI model used; always review before sending to a customer.
