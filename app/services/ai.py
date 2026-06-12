import os
import json
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# temperature=0.1 means low randomness.
# For clinical data extraction you want consistent, literal output
# not creative interpretation. Lower temperature = more deterministic.
MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.1

# These are the top-level keys the model must return.
# Used to validate the response before returning it to the worker.
REQUIRED_FIELDS = {
    "patient_summary",
    "possible_conditions",
    "red_flags",
    "suggested_next_steps",
    "missing_information",
    "urgency",
    "clinical_note",
}

# These are the keys each condition object must contain.
REQUIRED_CONDITION_FIELDS = {"condition", "icd10", "likelihood", "reasoning"}

SYSTEM_PROMPT = """You are a clinical decision support assistant helping experienced clinicians think through complex cases.

Your role is to surface possibilities and flag gaps — not to replace clinical judgment.
Always respond with valid JSON only. No markdown formatting, no backticks, no explanation text before or after the JSON.
Just the raw JSON object."""

USER_PROMPT = """Analyze this clinical case and return a JSON object with exactly these keys:

- patient_summary: string — a concise 2-3 sentence restatement of the case in clinical narrative form.
    Write it as you would in a handoff note: age, sex, chief complaint, key vitals, relevant history,
    and current medications if provided. Example style: "58-year-old female presenting with sudden onset
    severe headache rated 10/10, associated neck stiffness and vomiting. BP 178/102, HR 88, temp 37.8C.
    No prior headache history or recent trauma. Not on any anticoagulants."

- possible_conditions: list of objects ordered from highest to lowest likelihood, each with:
    - condition: string (full condition name)
    - icd10: string (the most specific applicable ICD-10-CM code, e.g. "I60.9", "J18.9", "I26.99")
    - likelihood: string (one of exactly: "High", "Moderate", "Low")
    - reasoning: string (1-2 sentences referencing specific findings from this case, not generic statements)

- red_flags: list of strings — findings in this case that require urgent rule-out or immediate action.
    Be specific to this case. Reference actual values where relevant.

- suggested_next_steps: list of strings — diagnostic tests, imaging, labs, or consults to consider.
    Order by priority. Include brief rationale if not obvious.

- missing_information: list of strings — specific history, exam findings, or data that would
    meaningfully change the differential for this case.

- urgency: string (one of exactly: "Emergent", "Urgent", "Semi-urgent", "Non-urgent")

- clinical_note: string — 1-2 sentences summarizing the core clinical reasoning approach for this case.

Rules:
- Reference the patient's actual values and findings throughout. Never give generic responses.
- ICD-10 codes must be real, valid ICD-10-CM codes. Use the most specific code that fits.
- If a condition has multiple subtypes, use the unspecified version (e.g. I26.99 not I26.01).

Clinical case:
{case_text}"""


class AIResponseValidationError(ValueError):
    """
    Raised when the AI returns valid JSON but the structure is wrong —
    missing required fields or malformed condition objects.

    This is a non-retryable error. If the model returns structurally wrong
    output, retrying with the same input will likely produce the same result.
    The worker catches this specifically and marks the job failed immediately
    without burning through retries.
    """
    pass


def _validate_response(data: dict) -> None:
    """
    Check that the parsed JSON contains all required fields and that
    each condition object is properly structured.

    Raises AIResponseValidationError with a specific message if anything
    is missing, so the error stored in the DB tells you exactly what went wrong.
    """
    missing_top = REQUIRED_FIELDS - set(data.keys())
    if missing_top:
        raise AIResponseValidationError(
            f"AI response missing required fields: {sorted(missing_top)}"
        )

    if not isinstance(data["possible_conditions"], list):
        raise AIResponseValidationError(
            "possible_conditions must be a list"
        )

    for i, condition in enumerate(data["possible_conditions"]):
        if not isinstance(condition, dict):
            raise AIResponseValidationError(
                f"possible_conditions[{i}] is not an object"
            )
        missing_cond = REQUIRED_CONDITION_FIELDS - set(condition.keys())
        if missing_cond:
            raise AIResponseValidationError(
                f"possible_conditions[{i}] missing fields: {sorted(missing_cond)}"
            )

    valid_likelihoods = {"High", "Moderate", "Low"}
    for i, condition in enumerate(data["possible_conditions"]):
        if condition.get("likelihood") not in valid_likelihoods:
            raise AIResponseValidationError(
                f"possible_conditions[{i}].likelihood must be High, Moderate, or Low. "
                f"Got: {condition.get('likelihood')!r}"
            )

    valid_urgency = {"Emergent", "Urgent", "Semi-urgent", "Non-urgent"}
    if data.get("urgency") not in valid_urgency:
        raise AIResponseValidationError(
            f"urgency must be one of {valid_urgency}. Got: {data.get('urgency')!r}"
        )


def analyze_case(case_text: str) -> dict:
    """
    Send a clinical case description to Groq and return validated structured output.

    Uses response_format={"type": "json_object"} which instructs Groq at the
    API level to return only valid JSON — no prose wrappers, no markdown fences,
    no conversational text. This is more reliable than prompt-only instructions.

    After parsing, validates the structure with _validate_response() to catch
    cases where the JSON is valid but fields are missing or misnamed.

    Raises:
        AIResponseValidationError — valid JSON but wrong structure. Non-retryable.
        ValueError — JSON parse failure despite json_object mode (rare). Retryable.
        groq.RateLimitError — 429 from Groq. Retryable with backoff.
        groq.APITimeoutError — request timed out. Retryable.
        groq.APIConnectionError — network issue. Retryable.

    The worker inspects the exception type to decide whether to retry or fail fast.
    """
    truncated = case_text[:5000]
    logger.info(f"Sending case to Groq ({len(truncated)} characters)")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT.format(case_text=truncated)}
        ],
        temperature=TEMPERATURE,
        # Instructs Groq at the API level to return only valid JSON.
        # This eliminates the entire class of markdown/prose wrapper problems.
        # The model still needs the prompt to know what structure to return —
        # this just guarantees the outer format is parseable JSON.
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content
    logger.info("Received response from Groq")

    # json_object mode guarantees valid JSON, but we still wrap this in
    # a try/except because defensive programming is always correct here.
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed despite json_object mode. Raw: {raw[:400]}")
        raise ValueError(f"Unexpected JSON parse failure: {e}")

    # Validate structure — raises AIResponseValidationError if anything is wrong
    _validate_response(result)

    logger.info(
        f"Response validated: {len(result.get('possible_conditions', []))} conditions, "
        f"urgency={result.get('urgency')}"
    )

    return result