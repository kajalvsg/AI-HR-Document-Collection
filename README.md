# AI HR Document Collection System

Full-stack HR candidate resume intake + PAN/Aadhaar collection system.

- **Backend**: Flask + SQLAlchemy + SQLite  
- **Frontend**: React + TypeScript + Tailwind (Vite)  
- **AI**: OpenRouter (`/chat/completions`, OpenAI-compatible) for document request messages

## Features

- Resume upload (**PDF/DOCX**) and text extraction
- Candidate extraction: name, email, phone, company, designation, skills + confidence scores
- Candidate dashboard + profile page
- Generate PAN/Aadhaar request message (AI or template fallback)
- Upload PAN/Aadhaar (PDF or image) with duplicate prevention
- Candidate delete (removes DB records + uploaded files)

## Project structure

```
backend/
frontend/
```

## Prerequisites

- Python 3.11+
- Node.js 18+

## Backend setup (Flask)

```powershell
cd backend

# Create / activate venv (if you don’t already have one)
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Create `backend/.env` locally (do **not** commit it). Start from `backend/.env.example`.

Run backend:

```powershell
.\venv\Scripts\python.exe run.py
```

Health check: `GET http://localhost:5000/api/health`

## Frontend setup (React)

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## API quick reference

- `POST /api/candidates/upload` (multipart `resume`)
- `GET /api/candidates`
- `GET /api/candidates/<id>`
- `DELETE /api/candidates/<id>`
- `POST /api/candidates/<id>/request-documents`
- `POST /api/candidates/<id>/submit-documents` (multipart `pan`, `aadhaar`)

## Notes

- **Secrets**: keep `backend/.env` local. Use `backend/.env.example` as a template.
- **AI fallback**: if OpenRouter fails or returns an invalid message, the backend uses a template message.

