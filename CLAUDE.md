# CLAUDE.md — DocReview

The full product spec is in [intent.md](intent.md). It is the source of truth; read it before starting any phase. The phased build plan is in [PLAN.md](PLAN.md).

## What we're building

DocReview is an AI-assisted quality checker for business analysis documents (BRD, FRD, As-Is / To-Be process docs, roadmaps, and user-defined custom types). An analyst uploads a document, picks its type, and gets:
- a score out of 100 and a Pass (≥ 80 and no critical rule Not Met) or Fail result
- a result for every rule in that type's rulebook
- suggestions grouped as Add / Change / Delete

BA leads get a dashboard showing volume, pass/fail rates, documents corrected after failing, and the most frequently failed rules.

## Core principles (don't break these)

- **The AI judges each rule; the code calculates the score.** The model never outputs a score. Scoring is a pure, unit-tested Python function (`score = round(earned / applicable_weight × 100)`; Met = 100%, Partially Met = 50%, Not Met = 0, N/A excluded and only allowed when `allow_na: true`).
- **Rulebooks are the source of truth.** They are Markdown files with YAML front matter in `rulebooks/` (format in intent.md §3.2). The parser rejects malformed rulebooks and any rulebook whose weights don't sum to 100.
- **Reproducibility.** Every review stores a snapshot of the rules, the rulebook version, the model name, and the prompt version. Later rulebook edits never change past results.
- **Prompts live in `prompts/`** as versioned text files (`evaluate_rules_v1.txt`, ...). Don't hard-code them in Python.
- **Business logic lives in service functions**, separate from FastAPI route handlers, so a future agent can call them as tools.
- **Privacy:** never log the full document text. Uploaded files are **not** stored: read the upload in memory, extract its text, save only `extracted_text` in the database, then discard the file (product owner decision, overrides intent.md's original §11).

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
├── rulebooks/                brd.md, frd.md, process_as_is.md, process_to_be.md, roadmap.md
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
