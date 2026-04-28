# Guardians Frame MVP

Guardians Frame is an MVP for dual-layer sports media protection. It includes a FastAPI backend for media upload and verification workflows, plus a Next.js frontend for interacting with the system.

## Project Structure

```text
backend/   FastAPI API, media processing, matching, Firestore/vector services
frontend/  Next.js app
```

## Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

The API starts at `http://localhost:8080`.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The app starts at `http://localhost:3000`.

## Environment Variables

Copy `.env.example` to `.env` and fill in your local credentials.

Do not commit `.env`, `.env.local`, Firebase service account JSON files, uploaded videos, or generated cache/build folders.

## Tests

```powershell
cd backend
pytest
```
