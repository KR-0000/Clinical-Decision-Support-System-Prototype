import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers.jobs import router as jobs_router

load_dotenv()

# Set up logging before anything else.
# INFO level means you will see info, warning, and error messages in the terminal.
# The format includes timestamp, level, logger name, and the message.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)

app = FastAPI(
    title="Clinical Decision Support (CDS) System",
    description=(
        "Decision support tool for clinicians. "
        "Submit a patient case as text or PDF and receive a structured differential "
        "with possible conditions, red flags, and suggested next steps. "
        "This tool supports clinical reasoning -- it does not replace it."
    ),
    version="0.1.0"
)

# CORS middleware: required for the frontend HTML files to talk to this API
# when opened directly in a browser (file:// protocol).
# allow_origins=["*"] is safe for local development.
# In production, restrict this to your actual deployed frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the jobs router — adds all /jobs/* endpoints to the app
app.include_router(jobs_router)


@app.get("/health", tags=["system"])
def health():
    """
    Basic health check. Confirms the API is running.
    In Phase 2 this will be expanded to check DB and Redis connectivity.
    """
    return {"status": "ok"}