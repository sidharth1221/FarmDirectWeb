# FarmDirectWeb

> Local development: backend (FastAPI) + frontend (static HTML).

- Backend: `backend/` (FastAPI, SQLAlchemy, YOLO integration)
- Frontend: `frontend/index.html` (single-file static front-end)

## Quick start (local)

1. Create a Python virtual environment and activate it:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install backend dependencies:

```powershell
cd backend
pip install -r requirements.txt
```

3. Start backend (from repo root):

```powershell
# From project root
python start_backend.py
```

4. Serve the frontend (any static server). For example, with VS Code Live Server or:

```powershell
python -m http.server 5500 -d frontend
```

5. Open `http://localhost:5500` and use the UI.

## Notes
- Backend default port: `8001` (see `start_backend.py`).
- Add your secrets to `backend/.env` (do NOT commit `.env`).
- Large model files (`*.pt`) and credentials are ignored by `.gitignore`.