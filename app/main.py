import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from app.limiter import limiter
from app.routers.jobs import router as jobs_router

load_dotenv()

# ALLOWED_ORIGINS is set in the Render environment to the exact frontend URL.
# Locally, leave unset (defaults to "*") so file:// and localhost dev both work.
# allow_credentials must be False when using "*" — the app uses no cookies or sessions.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")]

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

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    # Must be False when allow_origins contains "*" (CORS spec forbids both).
    # This app has no cookies or session tokens, so credentials are never sent.
    allow_credentials=False,
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