# DocReview

AI-assisted quality checker for business analysis documents (BRD, FRD, process docs, roadmaps). Upload a document, get a score out of 100, Pass/Fail, and specific suggestions.

- Product spec: [intent.md](intent.md)
- Build plan and progress: [PLAN.md](PLAN.md)

## First-time setup (Windows PowerShell)

Requires Python 3.11+ and Node.js 20+.

```powershell
# 1. Settings file
cd "D:\AI Agents\DocumentReviewAgent"
Copy-Item .env.example .env

# 2. Backend
cd "D:\AI Agents\DocumentReviewAgent\backend"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Frontend
cd "D:\AI Agents\DocumentReviewAgent\frontend"
npm install
```

## AI key and demo mode

Reviews use Anthropic's Claude API. Put your key in the `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Then restart the backend. **Without a key the app runs in demo mode:** reviews use simple keyword matching instead of AI (clearly labelled on every result), and drafting rules from a prompt is disabled. Everything else works. After adding a key, open any demo review and click **Re-run review** to get a real one.

## Running the app

Use two terminals. Always `cd` into the folder first; VS Code terminals open in the project root.

**Terminal 1, backend** (API on http://localhost:8000, interactive docs at http://localhost:8000/docs):

```powershell
cd "D:\AI Agents\DocumentReviewAgent\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

**Terminal 2, frontend** (the app, on http://localhost:5173):

```powershell
cd "D:\AI Agents\DocumentReviewAgent\frontend"
npm run dev
```

## Running tests

```powershell
cd "D:\AI Agents\DocumentReviewAgent\backend"
.\.venv\Scripts\python.exe -m pytest
```

## Useful scripts

```powershell
cd "D:\AI Agents\DocumentReviewAgent\backend"

# Review one document 3 times and check the scores stay within ±3 (needs the API key; each run costs one review)
.\.venv\Scripts\python.exe scripts\consistency_check.py ..\samples\brd_strong.md --type brd --runs 3

# Rebuild the sample .docx files from the .md samples
.\.venv\Scripts\python.exe scripts\make_sample_docx.py
```

## Starting fresh

All data lives in `backend\docreview.db`. To wipe everything (documents, reviews and rulebook edits), stop the backend, delete that file, and start the backend again. The five starting rulebooks are reloaded from `rulebooks\`.
