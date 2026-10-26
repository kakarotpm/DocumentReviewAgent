# CLAUDE.md — DocReview

The full product spec is in [intent.md](intent.md). It is the source of truth; read it before starting any phase. The phased build plan is in [PLAN.md](PLAN.md).

## What we're building

DocReview is an AI-assisted quality checker for business analysis documents (BRD, FRD, As-Is / To-Be process docs, roadmaps, and user-defined custom types). An analyst uploads a document, picks its type, and gets:
- a score out of 100 and a Pass (≥ 80 and no critical rule Not Met) or Fail result
- a result for every rule in that type's rulebook
- suggestions grouped as Add / Change / Delete

BA leads get a dashboard showing volume, pass/fail rates, documents corrected after failing, and the most frequently failed rules.

## Core principles (don't break these)

- **The AI judges each rule; the code calculates the score.** The model never outputs a score. Scoring is a pure, unit-tested Python function. See "Scoring decisions" below.
- **Rulebooks live in the database and are editable in the UI.** The Markdown files in `rulebooks/` are the starting content, loaded into the database on first run, and Markdown is the import/export format (intent.md §3.2, as amended below). The parser rejects malformed rulebooks with a clear message. See "Rulebook editing decisions" below.
- **Reproducibility.** Every rulebook save creates a new, immutable rulebook version. Every review records the exact rulebook version it used, plus the model name and prompt version. Later rulebook edits never change past results.
- **Prompts live in `prompts/`** as versioned text files (`evaluate_rules_v1.txt`, ...). Don't hard-code them in Python.
- **Business logic lives in service functions**, separate from FastAPI route handlers, so a future agent can call them as tools.
- **Privacy:** never log the full document text. Uploaded files are **not** stored: read the upload in memory, extract its text, save only `extracted_text` in the database, then discard the file (product owner decision, overrides intent.md's original §11).

## Scoring decisions (product owner, 2026-10-19; these override intent.md §3.2, §4, §6)

Keep scoring simple. These replace the spec's version:

- **Three outcomes per rule:** Met (full points), Partially Met (half points), Not Met (0). There is **no Not Applicable** and no `allow_na` field.
- **Weights are levels, not numbers:** each rule has `weight: high | medium | low`, worth 3 / 2 / 1 points. Nobody has to make weights add up to 100.
- **Score** = round(points earned ÷ points possible × 100).
- **Pass** = score ≥ `pass_threshold` (default 80) **and** no critical rule is Not Met. A critical rule that is Partially Met does not force a Fail on its own.
- **Critical rules:** 1–3 per document type, marked `critical: true`.
- **About 10 rules per document type.**
- **No categories** (product owner, 2026-10-21): rules have no category, and there is no "score by category" breakdown on results or reports. Weights show as High/Medium/Low only, never as point numbers, in the rulebook screens.
- **Custom types** use the same High/Medium/Low levels, so the custom-rules editor doesn't need a "weights must total 100" check.

## Rulebook editing decisions (product owner, 2026-10-19; overrides intent.md §15 "in-app editing out of scope")

- Users can **edit, add and delete rules** and **create new document types** in the UI. Editing a rule covers its text, **weight (High/Medium/Low)** and **critical / non-critical flag**; prompt changes and `.md` uploads can change these too (a **Rulebooks** screen, which replaces the read-only Guidelines screen).
- **Three ways to do everything**, both for creating a new document type and for adding or changing rules in an existing one:
  1. **Manually** in a form (new type: name, description, pass threshold, then add rules one by one).
  2. **Upload a `.md` file** in the rulebook format.
  3. **Write a prompt** describing what's needed; the AI drafts the type or the rule changes.
- Any rulebook can be **downloaded** as `.md`.
- Users can **write a prompt** to add or update rules. The AI proposes changes; nothing is applied automatically.
- Upload and prompt changes both show a **preview of the changes** (added / changed / removed rules) that the user must confirm before saving.
- **Anyone can edit** (no login). The editor types their name; every save records who, when, and an optional note in the version history.
- **Revised document versions are reviewed against the latest rulebook.** If the rulebook changed since the previous version, the results page says so next to the score change.
- Custom types are just rulebooks created from a prompt, so they use the same editor.

## Excel workbook decisions (product owner, 2026-10-26)

Many FRDs come with an Excel workbook (source-to-target mappings, transformations, joins, measures) because of data engineering and migration work.

- A rulebook can have two parts: **Part A** rules check the uploaded document; **Part B** rules (under a `# Part B: Excel rules` heading, IDs like `FRD-XL-01`) check an optional Excel workbook. Rules without a part heading are Part A.
- Works for **any document type whose rulebook has a Part B** (not hard-wired to FRD).
- On New Review (and revised-version upload), when the chosen type has Part B rules, show a checkbox **"Also upload the Excel workbook"**. Unticked: only the document is reviewed, against Part A only (Part B is left out, not failed). Ticked: a second upload for the workbook; the document is reviewed against Part A and the workbook against Part B.
- **One score and one Pass/Fail** covering both parts, plus a **subtotal per part**. A critical rule Not Met in either part fails the document.
- Workbooks: **.xlsx only** (openpyxl); old .xls gets a "save as .xlsx" message. Read each sheet's name, headers and **up to 1,000 rows per sheet**.
- The workbook review checks **structure and completeness** (sheet names, column/row headers, required content), **not the correctness of the data values**. The workbook review also sees the document text, for consistency rules.

## Tech stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite (keep it swappable for PostgreSQL through config only), Pydantic, the official `anthropic` Python SDK.
- **AI:** model comes from `ANTHROPIC_MODEL` in `.env`; default is `claude-sonnet-5-5`. Use structured outputs (`client.messages.parse` with Pydantic models) for rule evaluation. Note: current Claude models reject non-default `temperature` values, so we can't set temperature to 0. Consistency comes from structured outputs, precise rule `check` text with examples, and a fixed effort level (see PLAN.md).
- **File parsing:** `python-docx` (.docx), `pdfplumber` (.pdf; detect scanned/image-only PDFs and return a friendly error), plain read (.md, .txt). Max 10 MB.
- **Frontend:** React + Vite, Tailwind CSS, Recharts, React Router. Frontend polls review status; reviews run as background tasks.
- **Tests:** pytest for the scoring function, the rulebook parser, and file extraction.
- **Platform:** Windows, VS Code. Use commands that work in PowerShell, and give the product owner PowerShell commands.

## Folder layout

```
DocumentReviewAgent/          (repo root = app root)
├── intent.md                 product spec (called SPEC.md in the spec itself)
├── CLAUDE.md
├── PLAN.md                   phased delivery plan
├── rulebooks/                starting rulebooks, loaded into the DB on first run
├── prompts/                  evaluate_rules_v1.txt, generate_custom_rules_v1.txt
├── samples/                  sample documents (strong + weak BRD at minimum)
├── backend/
│   ├── app/                  main.py, config.py, db.py, models.py, schemas.py
│   │   ├── routes/           thin FastAPI routers
│   │   └── services/         rulebooks, extraction, review engine, scoring, dashboard SQL
│   └── tests/
└── frontend/                 React app
```

## Secrets and config

- `.env` holds `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `DATABASE_URL`. `.env` is gitignored; `.env.example` is committed with placeholder values.
- Never commit secrets, uploaded files, or the SQLite database file.

## How I want to work (from the product owner)

- Build in small phases. Stop after each one so I can test it. Each phase ends with a git commit.
- Explain changes in plain language a PM would understand. (I can read some code.)
- Keep code simple and readable; no unnecessary abstractions.
- For dashboard numbers, use plain SQL queries that I can read. Before you write them, ask me to try writing the SQL myself first.
- Tell me exactly which commands to run (PowerShell) and what I should see in the browser.
- Never commit secrets. Ask before installing large new dependencies.
- Prefer clear error messages that tell the user what to do next. Never show a blank screen.
