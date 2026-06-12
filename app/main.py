import logging
from fastapi import FastAPI
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
    title="Clinical Case Analysis Pipeline",
    description=(
        "Decision support tool for clinicians. "
        "Submit a patient case as text or PDF and receive a structured differential "
        "with possible conditions, red flags, and suggested next steps. "
        "This tool supports clinical reasoning — it does not replace it."
    ),
    version="0.1.0"
)

# Register the jobs router — this adds all /jobs/* endpoints to the app
app.include_router(jobs_router)


@app.get("/health", tags=["system"])
def health():
    """
    Basic health check. Confirms the API is running.
    In Phase 2 this will be expanded to check DB and Redis connectivity.
    """
    return {"status": "ok"}