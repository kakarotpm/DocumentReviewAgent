# DocReview — Development Plan

Based on [intent.md](intent.md). Nine phases, following intent.md §12. Each phase ends with something you can run and test, plus a git commit. I stop after each phase and wait for your go-ahead.

**Status:** Plan approved 2026-10-16. Check in with the product owner at the end of every phase.

Acceptance criteria (AC) are numbered in the order they appear in intent.md §14:

| # | Acceptance criterion (short) |
|---|---|
| AC1 | Upload .docx/.pdf/.md/.txt, choose a type, get a completed review |
| AC2 | Score 0–100, Pass/Fail, a result for every rule, suggestions grouped Add/Change/Delete |
| AC3 | A Not Met critical rule forces Fail even at ≥ 80, and the reason is shown |
| AC4 | Same unchanged document reviewed 3 times → scores within ±3 |
| AC5 | Revised version links to the same document and shows the score change; fail → pass = Corrected |
| AC6 | Dashboard counts match the data and respond to filters |
| AC7 | Custom type from free text; rules editable; weights validated to 100; optionally saved |
| AC8 | Friendly errors for malformed rulebooks, unsupported files, scanned PDFs, API failures |

---

## Phase 1 — Setup

**What gets built:** Folder structure, a FastAPI app with a `/api/health` endpoint, a Vite + React + Tailwind app showing a placeholder page that calls the health endpoint, and config loaded from `.env`.

**Files:** `backend/app/main.py`, `backend/app/config.py`, `backend/requirements.txt`, `backend/tests/test_health.py`, `frontend/` (Vite scaffold, `tailwind.config.js`, `src/App.jsx`), `.env.example`, `.gitignore` additions (`node_modules/`, `*.db`), `README.md` run instructions. (`CLAUDE.md` is already written.)

**How you test it:**
1. `cd backend; python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn app.main:app --reload` → open http://localhost:8000/docs.
2. `cd frontend; npm install; npm run dev` → open http://localhost:5173. The page shows "Backend: connected".

**AC:** Foundation only.

---

## Phase 2 — Rulebooks

**Before starting: brainstorm with the product owner** on what the rules should be and how scoring works (statuses, weights, critical rules, N/A). Goal: keep it simple. Decisions get recorded in CLAUDE.md before any rulebook is written.

**What gets built:** All five rulebooks. A parser that turns a rulebook file into structured rules and rejects bad files with a specific message (for example: "brd.md: weights sum to 95, expected 100" or "BRD-07 is missing 'weight'"). Two endpoints: `GET /api/document-types` and `GET /api/document-types/{key}`.

**Files:** `rulebooks/brd.md` (v1.0, from the §3.3 table), `rulebooks/frd.md`, `rulebooks/process_as_is.md`, `rulebooks/process_to_be.md`, `rulebooks/roadmap.md` (all `0.1-draft`). Rule ID prefixes: `BRD-`, `FRD-`, `ASIS-`, `TOBE-`, `RDM-`. Also `backend/app/services/rulebooks.py`, `backend/app/schemas.py` (Rule and Rulebook models), `backend/app/routes/document_types.py`, `backend/tests/test_rulebook_parser.py`, and `backend/tests/fixtures/` (deliberately broken rulebooks).

**How you test it:** `pytest` passes. In `/docs`, call `GET /api/document-types/brd` and see 14 rules. Change a weight in a copy of a rulebook and confirm the clear error.

**AC:** AC8 (malformed rulebooks).

---

## Phase 3 — Upload and extraction

**What gets built:** The database tables (all six from §9), text extraction for all four formats that keeps headings and numbering, scanned-PDF detection (pages with almost no extractable text), and file type and 10 MB size checks. `POST /api/documents` reads the file in memory, saves only its extracted text, and creates the Document and Version 1. The original file is never written to disk. In this phase the Review record is created as `queued`; nothing evaluates it yet.

**Files:** `backend/app/db.py`, `backend/app/models.py`, `backend/app/services/extraction.py`, `backend/app/services/documents.py`, `backend/app/routes/documents.py`, `backend/tests/test_extraction.py`, `backend/tests/fixtures/` (small .docx/.pdf/.md/.txt files plus a scanned-style PDF), `samples/brd_strong.md`, `samples/brd_weak.md` (also as .docx).

**How you test it:** In `/docs`, upload each sample file and see the extracted text in the response. Upload a `.png` or a scanned PDF and get a friendly error. `pytest` passes.

**AC:** AC8 (unsupported files, scanned PDFs). Part of AC1.

---

## Phase 4 — Review engine

**What gets built:**
- `scoring.py`: the pure scoring function. It takes rule results and the rules and returns the score, pass/fail, critical failures, and a per-category breakdown. It is fully unit-tested (N/A exclusion, N/A rejected when `allow_na` is false, critical override, rounding, all-N/A edge case).
- The evaluation prompt, kept as a file.
- A Claude call that uses structured outputs with a Pydantic schema matching §5.2, retries once if the output is invalid, and handles refusals and API errors.
- Background processing (queued → processing → complete / error).
- On startup, any review stuck in `processing` is marked `error`.
- `GET /api/reviews/{id}`.
- A consistency script that reviews one sample N times and reports the score spread.

**Files:** `prompts/evaluate_rules_v1.txt`, `backend/app/services/scoring.py`, `backend/app/services/review_engine.py`, `backend/app/services/llm.py`, `backend/app/routes/reviews.py`, `backend/tests/test_scoring.py`, `backend/tests/test_review_engine.py` (with the Claude call mocked), `backend/scripts/consistency_check.py`.

**How you test it:** Put your API key in `.env`. In `/docs`, upload `samples/brd_strong.md`, then poll `GET /api/reviews/{id}`. Expect Pass, around 85–95. The weak BRD should Fail with a critical-rule banner reason. Run `python scripts/consistency_check.py samples/brd_strong.md --runs 3` and check that the spread is ≤ 3.

**AC:** AC2, AC3, AC4, AC8 (API failures). AC1 is done at the API level.

---

## Phase 5 — Frontend core

**What gets built:**
- App shell with a fixed sidebar and light/dark theme tokens set up from the start, so dark mode in Phase 9 is a toggle rather than a retrofit.
- New Review page: type cards, drag-and-drop upload, details form, privacy notice, Run button.
- In-progress page with step indicators and polling.
- Review Results page: gauge, Pass/Fail badge with icon and text, critical banner, category breakdown, Add/Change/Delete tabs with counts, suggestion cards with copy buttons, rule checklist with a status filter.
- Loading, empty, and error states on every page.

**Files:** `frontend/src/` → `api/client.js`, `components/` (Sidebar, ScoreGauge, StatusBadge, SuggestionCard, RuleChecklist, FileDropzone, ErrorState, …), `pages/NewReview.jsx`, `pages/ReviewProgress.jsx`, `pages/ReviewResults.jsx`, `router.jsx`.

**How you test it:** Run both apps. Do a full review in the browser using both sample BRDs. Navigate away mid-review and come back.

**AC:** AC1, AC2, and AC3 in the UI.

---

## Phase 6 — Documents and versions

**What gets built:**
- `POST /api/documents/{id}/versions`, which reuses the rule snapshot from Version 1 so versions are compared against the same rules.
- Document status logic (Passed / Failed / Corrected, plus "In review" / "Error" when the latest review isn't complete), unit-tested.
- Documents list with search, filters, and sorting.
- Document detail page with a version timeline.
- On the results page: the score change from the previous version and the lists of newly Met / newly Not Met rules.

**Files:** `backend/app/services/documents.py` (extended), `backend/app/services/status.py`, `backend/tests/test_status.py`, `frontend/src/pages/Documents.jsx`, `pages/DocumentDetail.jsx`, `components/VersionDiff.jsx`.

**How you test it:** Upload the weak BRD (Fail), then upload the strong BRD as its revised version. The document shows **Corrected** and the results page shows the score change, for example "+38 from v1".

**AC:** AC5.

---

## Phase 7 — Dashboard

**What gets built:** The four dashboard endpoints, written as plain SQL in one file with comments. Summary cards, four Recharts charts, filters (date range, type, project), and a recent reviews table. Clicking a top-failed rule shows the affected documents.

**Before I write the SQL**, I'll describe each query in plain English and the tables involved, so you can try writing it first. Then we compare.

**Files:** `backend/app/services/dashboard_queries.sql` (or `dashboard.py` with SQL strings), `backend/app/routes/dashboard.py`, `backend/tests/test_dashboard.py` (seeds known data and checks the counts), `frontend/src/pages/Dashboard.jsx`, `components/charts/*`.

**How you test it:** Use `backend/scripts/seed_demo_data.py` (fake reviews, no API cost) and compare the cards with the seeded numbers. Change the filters and watch the numbers update.

**AC:** AC6.

---

## Phase 8 — Custom document type

**What gets built:** The rule-generation prompt, `POST /api/document-types/custom/preview`, an editable rules table with a running weight total (submission blocked until it reaches 100), and a "Save as reusable custom type" option. Unsaved custom types are still stored, but hidden from the type picker, so revised versions keep working.

**Files:** `prompts/generate_custom_rules_v1.txt`, `backend/app/services/custom_types.py`, `backend/tests/test_custom_types.py`, `frontend/src/components/CustomRulesEditor.jsx`, updates to `NewReview.jsx`.

**How you test it:** Pick Custom, type "Data Migration Plan" and a paragraph of instructions, edit the generated rules until the total reaches 100, run the review, and save the type. It then appears in the type picker.

**AC:** AC7.

---

## Phase 9 — Polish

**What gets built:** The Guidelines page (renders each rulebook and shows a draft badge), the PDF report download, Open/Done/Dismissed toggles on suggestions (`PATCH /api/suggestions/{id}`), a dark mode toggle, a pass over every empty and error state, and a final UX review against §8.

**New dependency (I'll ask first):** a PDF library. I recommend `fpdf2`: pure Python, small, and it installs cleanly on Windows. WeasyPrint looks nicer but needs extra system libraries on Windows.

**Files:** `frontend/src/pages/Guidelines.jsx`, `backend/app/services/report_pdf.py`, `backend/app/routes/suggestions.py`, theme toggle component.

**How you test it:** A walkthrough checklist I'll provide covering every screen in light and dark mode, plus downloading a report.

**AC:** AC8 (no blank screens); final check of all ACs.
