# DocReview

AI-assisted quality checker for business analysis documents (BRD, FRD, process docs, roadmaps). Upload a document, get a score out of 100, Pass/Fail, and specific suggestions.

- Product spec: [intent.md](intent.md)
- Build plan: [PLAN.md](PLAN.md)

## First-time setup (Windows PowerShell)

Requires Python 3.11+ and Node.js 20+.

```powershell
# 1. Settings: copy the example and add your Anthropic API key
Copy-Item .env.example .env

# 2. Backend
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..

# 3. Frontend
cd frontend
npm install
cd ..
```

## Running the app

Use two terminals. Always `cd` into the folder first; VS Code terminals open in the project root.

**Terminal 1, backend** (API on http://localhost:8000, interactive docs at http://localhost:8000/docs):

```powershell
cd "D:\AI Agents\DocumentReviewAgentackend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

**Terminal 2, frontend** (app on http://localhost:5173):

```powershell
cd "D:\AI Agents\DocumentReviewAgentrontend"
npm run dev
```

## Running tests

```powershell
cd "D:\AI Agents\DocumentReviewAgentackend"
.\.venv\Scripts\python.exe -m pytest
```
