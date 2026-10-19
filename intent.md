# DocReview: Product Specification

**Product:** DocReview, an AI-assisted quality checker for business analysis documents
**Owner:** Product Manager
**Status:** Draft v1.0, ready for development planning
**Audience:** Claude Code (to produce a development plan) and the product owner

---

## 0. Instructions for Claude Code

1. Read this entire spec before doing anything else.
2. Do NOT write application code yet. First create a `CLAUDE.md` file summarising the project context, tech stack, folder layout, and the working preferences in section 13.
3. Then produce a phased development plan that follows section 12, listing for each phase: what will be built, files created, how the product owner can test it, and the acceptance criteria it satisfies.
4. List any questions or assumptions, and confirm or challenge the open questions in section 14.
5. Wait for the product owner's approval before starting Phase 1.

---

## 1. Problem and Goal

Business analysts produce BRDs, FRDs, process documents (As-Is, To-Be), and roadmaps. Quality varies widely: sections go missing, requirements are vague or untestable, scope is unclear, and reviews depend on whichever senior reviewer is available. Reviews are slow, inconsistent, and leave no data on recurring quality problems.

**Goal:** Give analysts a self-service tool that reviews a document against an agreed, written set of rules for its type, produces a quality score out of 100, flags it as Pass (80 or above) or Fail (below 80), and gives specific, actionable suggestions on what to add, change, or delete. Give leads a dashboard showing review volume, pass/fail rates, how many failed documents were corrected, and which rules fail most often.

### Success metrics

- 80% of submitted documents receive a completed review in under 2 minutes.
- Re-reviewing the same unchanged document produces a score within ±3 points.
- At least 60% of failed documents are re-submitted and pass within 2 versions.
- Analysts rate suggestions as "useful" at least 4 out of 5 on average (future feedback feature).

---

## 2. Users

- **Business Analyst (primary):** uploads documents, reads the score and suggestions, fixes the document, re-uploads a revised version.
- **BA Lead / Reviewer (secondary):** uses the dashboard to monitor quality trends and recurring gaps; owns the rulebooks.

MVP has no login. Users type their name when uploading (see open questions).

---

## 3. Core Concept: Rulebooks

Every document type has a **rulebook**: a Markdown file in the `rulebooks/` folder that defines what a good document of that type contains. Rulebooks are the single source of truth for scoring. They are human-readable so BA leads can review and edit them without touching code.

### 3.1 Built-in document types (MVP)

| Key | Display name | Rulebook file |
|---|---|---|
| `brd` | Business Requirements Document | `rulebooks/brd.md` |
| `frd` | Functional Requirements Document | `rulebooks/frd.md` |
| `process_as_is` | As-Is Process Document | `rulebooks/process_as_is.md` |
| `process_to_be` | To-Be Process Document | `rulebooks/process_to_be.md` |
| `roadmap` | Product / Project Roadmap | `rulebooks/roadmap.md` |
| `custom` | Custom (user-defined) | generated at upload time |

### 3.2 Rulebook file format

> **Amended 2026-10-19 by the product owner:** `weight` is `high | medium | low` (3 / 2 / 1 points), not a number that must total 100; `allow_na` is removed; about 10 rules per type. See CLAUDE.md, "Scoring decisions".

Each rulebook has YAML front matter followed by one section per rule. The app must parse this format into structured rules and reject a rulebook (with a clear error) if it is malformed or its weights do not sum to 100.

```markdown
---
doc_type: brd
display_name: Business Requirements Document
version: 1.0
pass_threshold: 80
description: Captures the business need, objectives, scope and high-level requirements.
---

## BRD-03: Measurable business objectives
- category: Objectives
- weight: 10
- critical: true
- allow_na: false
- check: The document states business objectives that are specific and measurable
  (a target value and timeframe, e.g. "reduce onboarding time from 10 days to 3 by Q2").
- pass_example: "Reduce invoice processing cost by 20% within 12 months of go-live."
- fail_example: "Improve the invoicing process."
```

Field definitions:

- **Rule ID** (in the heading): unique within the rulebook, format `<TYPE>-<NN>`.
- **category:** grouping used for the score breakdown (e.g. Structure, Scope, Requirements Quality, Governance).
- **weight:** points this rule is worth. All weights in a rulebook must sum to 100.
- **critical:** if `true` and the rule is Not Met, the document fails regardless of score.
- **allow_na:** if `true`, the evaluator may mark the rule Not Applicable.
- **check:** the precise instruction the evaluator uses to judge the rule.
- **pass_example / fail_example:** optional, improve evaluation accuracy.

### 3.3 Sample rulebook: BRD (complete; use as the reference for the others)

| ID | Rule | Category | Weight | Critical |
|---|---|---|---|---|
| BRD-01 | Document control: title, version, author, date, revision history | Structure | 5 | No |
| BRD-02 | Executive summary and business context explaining why the project exists | Context | 8 | No |
| BRD-03 | Business objectives are specific and measurable (target + timeframe) | Objectives | 10 | Yes |
| BRD-04 | Scope explicitly lists both in-scope and out-of-scope items | Scope | 10 | Yes |
| BRD-05 | Stakeholders identified with roles and responsibilities (e.g. RACI) | Stakeholders | 6 | No |
| BRD-06 | Summary of the current state and the business problem | Context | 5 | No |
| BRD-07 | Each business requirement has a unique ID | Requirements Quality | 8 | No |
| BRD-08 | Requirements are business-level (not solution design), unambiguous, and testable; no vague terms like "fast", "user-friendly", "etc." without definition | Requirements Quality | 12 | No |
| BRD-09 | Requirements are prioritised (e.g. MoSCoW) | Requirements Quality | 6 | No |
| BRD-10 | Assumptions, constraints, and dependencies are listed | Governance | 8 | No |
| BRD-11 | Risks are identified with a mitigation for each | Governance | 5 | No |
| BRD-12 | Success metrics / KPIs define how the outcome will be measured | Objectives | 8 | No |
| BRD-13 | Glossary of terms and acronyms | Structure | 3 | No |
| BRD-14 | Approval / sign-off section with named approvers | Governance | 6 | No |
| | **Total** | | **100** | |

Claude Code should write `rulebooks/brd.md` in the format from 3.2 using this table, adding clear `check` text and examples for each rule.

### 3.4 Other rulebooks: areas to cover

Claude Code should draft these four rulebooks in the same format (weights summing to 100, 10 to 15 rules each, 1 to 3 critical rules). Each must be marked `version: 0.1-draft` until a BA lead approves it.

- **FRD:** document control; traceability of each functional requirement to a BRD requirement ID; uniquely identified functional requirements; use cases or user stories with acceptance criteria; business rules; data requirements (fields, validations); interfaces and integrations; UI / reporting requirements; error and exception handling; non-functional requirements (performance, security, availability) with measurable targets; assumptions and dependencies; sign-off.
- **As-Is Process:** process scope and boundaries (start and end trigger); actors and roles; process map or swimlane diagram referenced; step-by-step descriptions; inputs and outputs per step; systems and tools used; exceptions and workarounds; pain points with evidence or quantification; baseline metrics (volume, cycle time, error rate); document control.
- **To-Be Process:** reference to the As-Is process; future-state process map; clear description of what changes from As-Is and why; how each As-Is pain point is addressed; roles and responsibility changes; system changes; controls and compliance checkpoints; target KPIs compared with the baseline; change impact and transition considerations; document control.
- **Roadmap:** vision and strategic objectives; time horizon with phases or quarters; initiatives linked to objectives; milestones with dates; owners per initiative; dependencies between initiatives; key assumptions and resource needs; risks; success measures per phase; version and last-updated date.

---

## 4. Scoring Model

> **Amended 2026-10-19 by the product owner:** no Not Applicable outcome; weights are High/Medium/Low levels; score = earned ÷ possible × 100. Pass/Fail rule (§4.3) unchanged. See CLAUDE.md, "Scoring decisions".

Scoring must be deterministic and transparent. **The AI judges each rule; the code calculates the score.** The language model never outputs the final score.

### 4.1 Rule outcomes

| Status | Points earned |
|---|---|
| Met | 100% of rule weight |
| Partially Met | 50% of rule weight |
| Not Met | 0 |
| Not Applicable | Rule excluded from scoring (only allowed if `allow_na: true`) |

### 4.2 Formula

```
score = round( sum(points earned) / sum(weights of applicable rules) × 100 )
```

### 4.3 Pass / Fail

- **Pass:** score ≥ `pass_threshold` (default 80) AND no critical rule is Not Met.
- **Fail:** score < threshold, OR any critical rule is Not Met (show a "Critical rule failed" banner explaining which one).

### 4.4 Consistency requirements

- Use temperature 0 for evaluation calls.
- Store the rulebook version, model name, and prompt version with every review so results are reproducible and auditable.
- The scoring function must be a pure, unit-tested Python function.

---

## 5. AI Review Engine

### 5.1 Flow

1. Extract plain text from the uploaded file, preserving headings and section numbers where possible.
2. Load the rulebook for the selected type (or the generated rules for a custom type).
3. Send the document text and the rules to the Claude API, asking for one structured JSON result per rule.
4. Validate the JSON against a schema (Pydantic). If invalid, retry once; if still invalid, mark the review as Error with a friendly message.
5. Compute the score in code (section 4), save everything, and mark the review Complete.

### 5.2 Per-rule output schema (from the model)

```json
{
  "rule_id": "BRD-04",
  "status": "partially_met",
  "evidence": "Section 3.1 lists in-scope items; no out-of-scope list found.",
  "location": "Section 3.1 Scope",
  "explanation": "Scope lists what is included but never states exclusions, which invites scope creep.",
  "suggestions": [
    {
      "type": "add",
      "location": "After Section 3.1",
      "current_text": null,
      "proposed_text": "3.2 Out of Scope: (a) Migration of historical data before 2022; (b) Mobile app changes.",
      "rationale": "Explicit exclusions prevent scope disputes later."
    }
  ]
}
```

### 5.3 Suggestion types

- **Add (Missing):** content that should exist but does not.
- **Change:** content that exists but is vague, incorrect, or poorly structured, with the current text and a proposed rewrite.
- **Delete:** content that should be removed (e.g. solution design inside a BRD, duplicated sections, outdated information).

### 5.4 Technical notes

- Use the official Anthropic Python SDK. API key and model name come from a `.env` file (`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`); default to a current Claude Sonnet model. `.env` must be in `.gitignore`.
- Keep prompts in a separate `prompts/` folder as versioned text files, not hard-coded in Python.
- Reviews run as a background task. The frontend polls the review status.
- Evidence quotes from the document should be short (one or two sentences) so the results page stays readable.

---

## 6. Custom Document Type

When the user selects **Custom**:

1. User enters a **document type name** (e.g. "Data Migration Plan") and **instructions** in a large text box describing what a good document of this type must contain. Optional: pass threshold (default 80).
2. The app sends the instructions to the AI, which converts them into structured rules in the rulebook format (IDs `CUS-01`, `CUS-02`, ..., weights summing to 100).
3. The user sees a **rules preview** table and can edit rule text, adjust weights, mark rules critical, or delete rules. The app shows the running weight total and blocks submission until it equals 100.
4. The user runs the review. Results look identical to built-in types.
5. Checkbox: **"Save as a reusable custom type"**. Saved custom types appear in the type selector for future uploads, labelled "Custom".

---

## 7. Document Versions and "Corrected" Tracking

- Each upload creates a **Document** with **Version 1**.
- From the results page, the user can click **"Upload revised version"**, which adds Version 2, 3, etc. to the same Document and runs a new review with the same document type and rules.
- **Document status** (based on its versions):
  - **Passed:** latest version passed and no earlier version failed.
  - **Failed:** latest version failed.
  - **Corrected:** at least one earlier version failed and the latest version passed.
- The results page for Version 2+ shows the score change versus the previous version and lists rules that are newly Met or newly Not Met.

---

## 8. Screens and UX

### 8.1 Design direction

Professional, calm, enterprise-grade. Clean layout with a fixed left sidebar navigation, generous white space, one accent colour, and a neutral palette. Clear typographic hierarchy. Pass/Fail always shown with text and an icon, never colour alone. Responsive down to tablet width. Every screen has proper loading, empty, and error states. Support light and dark mode.

Sidebar items: **Dashboard**, **New Review**, **Documents**, **Guidelines**.

### 8.2 Dashboard (home)

- **Summary cards:** Total documents uploaded; Total reviews completed; Passed (≥80); Failed (<80); Corrected; Pass rate %; Average score.
- **Charts:**
  - Pass vs Fail count by document type (grouped bar).
  - Reviews over time (line, by week), with pass rate overlay.
  - Score distribution (histogram, buckets of 10, with the 80 threshold marked).
  - Top 10 most frequently failed rules (horizontal bar), each clickable to see affected documents.
- **Filters:** date range, document type, project.
- **Recent reviews** table: last 10 reviews with score, status, and link.

### 8.3 New Review (upload)

Step-by-step, single page:

1. **Choose document type:** selectable cards for BRD, FRD, As-Is Process, To-Be Process, Roadmap, saved custom types, and "Custom". Each card shows a one-line description and a "View guidelines" link.
2. **Upload file:** drag-and-drop area plus file picker. Accepted: `.docx`, `.pdf` (text-based), `.md`, `.txt`. Max 10 MB. Show file name and size after selection with an option to remove it.
3. **Details:** Document title (pre-filled from file name), Project name, Your name.
4. **Custom only:** type name, instructions, generated rules preview (section 6).
5. **Run review** button, disabled until required fields are complete.

### 8.4 Review in progress

Progress view with steps ("Reading document", "Checking 14 rules", "Calculating score"). User can navigate away; the review continues and appears in Documents.

### 8.5 Review Results

- **Header:** document title, type, version number, reviewed date.
- **Score panel:** large score out of 100 shown as a gauge, threshold marker at 80, Pass/Fail badge. Critical-failure banner if applicable. Score change vs previous version (Version 2+).
- **Category breakdown:** points earned vs available per category (bar or compact table).
- **Suggestions** in three tabs, each with a count: **Missing (Add)**, **Change**, **Delete**. Each suggestion card shows rule ID and title, location, current text (for Change/Delete), proposed text, rationale, a copy button, and a status toggle: Open / Done / Dismissed.
- **Rule checklist:** table of every rule with status icon, weight, points earned, evidence, explanation. Filter by status.
- **Actions:** Upload revised version; Download report (PDF); Back to Documents.

### 8.6 Documents

- Table: Title, Type, Project, Uploaded by, Latest score, Status (Passed / Failed / Corrected), Versions, Last updated.
- Search by title; filter by type, status, project, date range; sort by any column.
- Clicking a row opens **Document detail**: version timeline with score per version, and links to each version's results.

### 8.7 Guidelines

- List of all document types. Selecting one renders its rulebook in a readable format (rules table plus details), showing version and draft status. Read-only in MVP.

---

## 9. Data Model

- **DocumentType:** id, key, display_name, description, is_custom, rules_json (for custom types), rulebook_version, pass_threshold, created_at.
- **Document:** id, title, document_type_id, project_name, uploaded_by, created_at, updated_at.
- **DocumentVersion:** id, document_id, version_number, original_filename, file_type, extracted_text, uploaded_at. *(Amended: no stored_file_path; see Storage in §11.)*
- **Review:** id, document_version_id, status (queued / processing / complete / error), score, passed, critical_failure, rulebook_version, rules_snapshot_json, model_name, prompt_version, error_message, started_at, completed_at.
- **RuleResult:** id, review_id, rule_id, rule_title, category, weight, critical, status, points_earned, evidence, location, explanation.
- **Suggestion:** id, rule_result_id, type (add / change / delete), location, current_text, proposed_text, rationale, user_state (open / done / dismissed).

Store a snapshot of the rules used in each review so later rulebook edits do not change historical results.

---

## 10. API (FastAPI)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/document-types` | List built-in and saved custom types |
| GET | `/api/document-types/{key}` | Get a type with its parsed rules |
| POST | `/api/document-types/custom/preview` | Convert custom instructions into draft rules |
| POST | `/api/document-types/custom` | Save a custom type |
| POST | `/api/documents` | Upload file + metadata; create Document, Version 1, and start a Review |
| POST | `/api/documents/{id}/versions` | Upload a revised version and start a Review |
| GET | `/api/documents` | List documents with filters |
| GET | `/api/documents/{id}` | Document detail with version history |
| GET | `/api/reviews/{id}` | Review status and full results |
| GET | `/api/reviews/{id}/report` | Download PDF report |
| PATCH | `/api/suggestions/{id}` | Update suggestion state (open / done / dismissed) |
| GET | `/api/dashboard/summary` | Summary card metrics (filters: from, to, type, project) |
| GET | `/api/dashboard/trends` | Reviews and pass rate over time |
| GET | `/api/dashboard/score-distribution` | Histogram data |
| GET | `/api/dashboard/top-failed-rules` | Most frequently failed rules |

Keep business logic in service functions separate from route handlers, so a future AI agent can call the same functions as tools.

---

## 11. Technical Stack and Constraints

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite (design so PostgreSQL can replace it later with a config change), Pydantic, Anthropic Python SDK.
- **File parsing:** `python-docx` for .docx, `pdfplumber` for .pdf, plain read for .md/.txt. Scanned (image-only) PDFs are out of scope; detect them and show a friendly error.
- **Frontend:** React with Vite, Tailwind CSS, Recharts, React Router.
- **Storage:** *(Amended by product owner, 2026-10-16.)* The uploaded file is read in memory, its text is extracted and saved in the database, and the original file is not kept. Only `extracted_text` is retained.
- **Dashboard queries:** written as plain, readable SQL so the product owner can learn from them.
- **Testing:** pytest for the scoring function, rulebook parser, and file extraction. Include a `samples/` folder with at least one strong BRD and one weak BRD (generated by Claude Code) to test the end-to-end review.
- **Privacy:** documents are sent to the Anthropic API for evaluation. Show a one-line notice on the upload screen. Do not log full document text.
- **Platform:** developed on Windows in VS Code.

### Folder layout

```
doc-review-app/
├── SPEC.md
├── CLAUDE.md
├── rulebooks/        brd.md, frd.md, process_as_is.md, process_to_be.md, roadmap.md
├── prompts/          evaluate_rules_v1.txt, generate_custom_rules_v1.txt
├── samples/          sample documents for testing
├── backend/          FastAPI app, models, services, tests
└── frontend/         React app
```

---

## 12. Delivery Phases

Each phase ends with a working, testable result and a git commit.

1. **Setup:** project scaffolding, `CLAUDE.md`, `.env.example`, `.gitignore`, both apps running with a placeholder page.
2. **Rulebooks:** write all five rulebooks; build and unit-test the rulebook parser and weight validation.
3. **Upload and extraction:** upload endpoint, text extraction for all four formats, with tests. Testable via FastAPI `/docs`.
4. **Review engine:** prompts, Claude API integration, JSON validation, scoring function with tests, background processing. Test end-to-end with the sample documents via `/docs`.
5. **Frontend core:** app shell with sidebar, New Review screen, in-progress screen, Review Results screen.
6. **Documents and versions:** Documents list, Document detail, revised-version upload, status logic including Corrected, version comparison.
7. **Dashboard:** summary cards, charts, filters, recent reviews.
8. **Custom document type:** instructions entry, rules generation, editable preview, save as reusable type.
9. **Polish:** Guidelines screen, PDF report export, suggestion state toggles, empty/error states, dark mode, final UX review.

---

## 13. Working Preferences (copy into CLAUDE.md)

- The product owner is a PM who can read some code. Explain each change in plain language.
- Build one phase at a time; stop after each and say exactly how to run and test it.
- Keep code simple and readable; avoid unnecessary abstractions.
- Before writing dashboard SQL, invite the product owner to attempt the query first.
- Never commit secrets. Ask before installing large new dependencies.
- Prefer clear error messages that tell the user what to do next.

---

## 14. Acceptance Criteria (MVP)

- A user can upload a .docx, .pdf, .md, or .txt file, choose a type, and receive a completed review.
- Every review shows a score 0 to 100, Pass/Fail per section 4.3, a result for every rule, and suggestions grouped into Add / Change / Delete.
- A document with a Not Met critical rule fails even if its score is 80 or above, and the reason is shown.
- Reviewing the same unchanged sample document three times gives scores within ±3 points.
- Uploading a revised version links it to the same document and shows the score change; a document that failed then passed shows status Corrected.
- Dashboard counts (uploaded, reviewed, passed, failed, corrected) match the underlying data and respond to filters.
- A custom type can be defined from free-text instructions, its rules edited, weights validated to 100, and optionally saved for reuse.
- Malformed rulebooks, unsupported files, scanned PDFs, and API failures produce clear, friendly errors, never a blank screen.

---

## 15. Out of Scope for MVP

> **Amended 2026-10-19 by the product owner:** in-app rulebook editing is now **in scope** (edit/add/delete rules, upload `.md`, AI prompt to add or update rules). See CLAUDE.md, "Rulebook editing decisions".

- Login, user roles, and permissions.
- In-app editing of rulebooks (edited as Markdown files for now).
- Editing the uploaded document inside the app or auto-applying suggestions.
- OCR for scanned PDFs.
- Integrations with SharePoint, Confluence, Jira, or Google Drive.

---

## 16. Open Questions (product owner to confirm)

1. Should a failed critical rule force a Fail regardless of score? (Spec assumes yes.)
2. Is Partially Met = 50% the right credit, or should it be configurable per rule?
3. Do we need login in a later phase, and should leads see everyone's documents while analysts see only their own?
4. How long should uploaded documents be retained?
5. Who approves rulebook changes, and should rulebook versions be visible on each report? (Spec assumes visible.)

---

## 17. Future Enhancements

- **RAG:** store high-scoring past documents in a vector database and use them as examples when generating suggestions ("here is how a strong Scope section looked in Project X").
- **Agent:** an assistant that drafts the missing sections directly, or reviews a BRD and FRD together to check traceability.
- **Feedback loop:** thumbs up/down on each suggestion to measure usefulness and tune prompts.
- **Rulebook editor** in the UI with version history and approval workflow.
