# DocReview — Development Plan

Based on [intent.md](intent.md). Nine phases, following intent.md §12. Each phase ends with something you can run and test, plus a git commit. I stop after each phase and wait for your go-ahead.

**Status:** Plan approved 2026-10-16. Check in with the product owner at the end of every phase.

**Revised 2026-10-19:** scoring simplified (High/Medium/Low weights, no N/A), about 10 rules per type, and rulebooks made editable in the UI. Phase 8 is now "Rulebook editor and custom types", and the Guidelines screen becomes the Rulebooks screen.

**Progress (2026-10-21):** No API key yet, so the product owner asked for everything else to be built first. Done: Phases 1–6 and 8, plus from Phase 9 the suggestion status toggles, dark mode, and empty/error states. Without a key the app runs in **demo mode** (keyword-matching reviewer, clearly labelled). Remaining:
- **Phase 7 Dashboard:** waiting for the product owner to try the SQL first.
- **Phase 9 PDF report:** needs `fpdf2` (ask before installing).
- **With the API key:** run real reviews on both samples, run `scripts/consistency_check.py` (±3 target), and try prompt-based rule drafting.

Acceptance criteria (AC) are numbered in the order they appear in intent.md §14:

| # | Acceptance criterion (short) |
|---|---|
| AC1 | Upload .docx/.pdf/.md/.txt, choose a type, get a completed review |
| AC2 | Score 0–100, Pass/Fail, a result for every rule, suggestions grouped Add/Change/Delete |
| AC3 | A Not Met critical rule forces Fail even at ≥ 80, and the reason is shown |
| AC4 | Same unchanged document reviewed 3 times → scores within ±3 |
| AC5 | Revised version links to the same document and shows the score change; fail → pass = Corrected |
| AC6 | Dashboard counts match the data and respond to filters |
| AC7 | Rulebooks editable in the UI (edit/add/delete rules, new types); `.md` upload and AI prompt changes are previewed before saving; custom type from free text, optionally saved |
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

**Brainstorm done (2026-10-19):** see "Scoring decisions" and "Rulebook editing decisions" in CLAUDE.md. Rulebook content for the five types is agreed as tables in chat before the files are written.

**What gets built:**
- All five rulebooks as `.md` files, about 10 rules each, with High/Medium/Low weights.
- A parser that turns a `.md` rulebook into structured rules and rejects bad files with a specific message (for example: "BRD-07: weight must be high, medium or low" or "Duplicate rule ID BRD-04").
- An exporter that turns stored rules back into `.md`.
- Database tables `document_types` and `rulebook_versions`. Each save is a new version with its rules, who changed it, when, and a note. The five files are loaded into the database on first run.
- Endpoints: `GET /api/document-types`, `GET /api/document-types/{key}`, `GET /api/document-types/{key}/export`.

**Files:** `rulebooks/brd.md`, `frd.md`, `process_as_is.md`, `process_to_be.md`, `roadmap.md`. Rule ID prefixes: `BRD-`, `FRD-`, `ASIS-`, `TOBE-`, `RDM-`. Also `backend/app/db.py`, `backend/app/models.py`, `backend/app/services/rulebooks.py` (parse, validate, export, load), `backend/app/schemas.py`, `backend/app/routes/document_types.py`, `backend/tests/test_rulebooks.py`, and `backend/tests/fixtures/` (deliberately broken rulebooks).

**How you test it:** `pytest` passes. In `/docs`, call `GET /api/document-types/brd` and see 10 rules, then call the export endpoint and get the `.md` back. Break a copy of a rulebook (bad weight, duplicate ID) and confirm the clear error.

**AC:** AC8 (malformed rulebooks).

---

## Phase 3 — Upload and extraction

**What gets built:** The remaining database tables (documents, versions, reviews, rule results, suggestions), text extraction for all four formats that keeps headings and numbering, scanned-PDF detection (pages with almost no extractable text), and file type and 10 MB size checks. `POST /api/documents` reads the file in memory, saves only its extracted text, and creates the Document and Version 1. The original file is never written to disk. In this phase the Review record is created as `queued`; nothing evaluates it yet.

**Files:** `backend/app/models.py` (extended), `backend/app/services/extraction.py`, `backend/app/services/documents.py`, `backend/app/routes/documents.py`, `backend/tests/test_extraction.py`, `backend/tests/fixtures/` (small .docx/.pdf/.md/.txt files plus a scanned-style PDF), `samples/brd_strong.md`, `samples/brd_weak.md` (also as .docx).

**How you test it:** In `/docs`, upload each sample file and see the extracted text in the response. Upload a `.png` or a scanned PDF and get a friendly error. `pytest` passes.

**AC:** AC8 (unsupported files, scanned PDFs). Part of AC1.

---

## Phase 4 — Review engine

**What gets built:**
- `scoring.py`: the pure scoring function. It takes rule results and the rules and returns the score, pass/fail, critical failures, and a per-category breakdown. It is fully unit-tested (High/Medium/Low points, half points for Partially Met, critical override, rounding, a critical rule Partially Met does not force a Fail).
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
- `POST /api/documents/{id}/versions`, which reviews the revised version against the **latest** rulebook. If the rulebook changed since the previous version, the results page shows "Rules updated since v1" next to the score change.
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

## Phase 8 — Rulebook editor and custom types

**What gets built:**
- A **Rulebooks** screen (replaces Guidelines): list of document types; open one to see its rules, version and history.
- **New document type**, three ways: **manually** (form for name, description and pass threshold, then add rules one by one), **upload `.md`**, or **describe it in a prompt** ("A Data Migration Plan must cover source/target mapping, data quality checks, reconciliation and rollback") and the AI drafts the rules.
- **Change an existing rulebook**, the same three ways: **manually** (edit any rule's text, category, weight, critical flag; add rules; delete rules), **upload `.md`**, or **prompt** ("Add a rule requiring a data retention section", "Make the risks rule critical").
- Upload and prompt results always show a **preview** (added / changed / removed rules) to edit or confirm before saving. Every save asks for your name and an optional note, and creates a new version.
- **Download `.md`** for any rulebook.
- **Custom type on the New Review screen:** describe the type in free text, the AI drafts the rules, you adjust them, then run the review. A "Save as reusable type" checkbox controls whether it appears in the type picker afterwards (unsaved ones are kept but hidden, so revised versions still work).

**Files:** `prompts/edit_rules_v1.txt`, `prompts/generate_custom_rules_v1.txt`, `backend/app/services/rulebook_editor.py`, `backend/app/routes/document_types.py` (extended), `backend/tests/test_rulebook_editor.py`, `frontend/src/pages/Rulebooks.jsx`, `pages/RulebookDetail.jsx`, `components/RuleEditor.jsx`, `components/ChangePreview.jsx`, updates to `NewReview.jsx`.

**How you test it:**
1. Create three new types: one by hand, one by uploading a `.md`, one from a prompt. All three appear in the New Review type picker.
2. Open Rulebooks → BRD, change a rule's weight, save; the version number goes up and the history shows your name.
3. Prompt "Add a rule that requires a data retention section"; check the preview, then confirm.
4. Download the BRD `.md`, edit it in VS Code, upload it back; check the preview.
5. Run a review on a sample BRD and confirm it uses the new rules, while an older review still shows its original rules.
6. New Review → Custom → "Data Migration Plan" with a paragraph of instructions; adjust the rules, run, and save it as a reusable type.

**AC:** AC7.

---

## Phase 9 — Polish

**What gets built:** The PDF report download (includes the rulebook version used), Open/Done/Dismissed toggles on suggestions (`PATCH /api/suggestions/{id}`), a dark mode toggle, a pass over every empty and error state, and a final UX review against §8.

**New dependency (I'll ask first):** a PDF library. I recommend `fpdf2`: pure Python, small, and it installs cleanly on Windows. WeasyPrint looks nicer but needs extra system libraries on Windows.

**Files:** `backend/app/services/report_pdf.py`, `backend/app/routes/suggestions.py`, theme toggle component.

**How you test it:** A walkthrough checklist I'll provide covering every screen in light and dark mode, plus downloading a report.

**AC:** AC8 (no blank screens); final check of all ACs.
