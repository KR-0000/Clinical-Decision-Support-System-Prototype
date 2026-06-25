ICD-10 codes are International Classification of Diseases
NLM Verified - verified groq's guess on icd-10 code from National Library of Medicine's api


## For running locally

Terminal 1 — Start the API

powershell.venv\Scripts\activate
uv run python -m uvicorn app.main:app --reload

Expected:

INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.

--reload makes uvicorn restart automatically when you edit a file. Use this in development only.

Terminal 2 — Start the Celery worker

powershell.venv\Scripts\activate
uv run python -m celery -A app.workers.tasks worker --loglevel=info --pool=so