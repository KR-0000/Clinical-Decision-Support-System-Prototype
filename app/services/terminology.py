import logging
import urllib.parse
import urllib.request
import json

logger = logging.getLogger(__name__)

# NLM Clinical Tables ICD-10-CM search API.
# Free, no API key required, maintained by the National Library of Medicine.
# Docs: https://clinicaltables.nlm.nih.gov/apidoc/icd10cm/v3/doc.html
NLM_ICD10_URL = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"


def verify_icd10(condition_name: str) -> dict:
    """
    Look up the correct ICD-10-CM code for a condition name using the NLM API.

    Takes the condition name as free text (e.g. "Subarachnoid Hemorrhage"),
    searches the NLM ICD-10-CM database, and returns the top match.

    Returns a dict with:
        code        - the verified ICD-10-CM code (e.g. "I60.9")
        description - the canonical NLM description for that code
        verified    - True if NLM returned a result, False if the lookup failed
                      or returned nothing (in which case code/description are
                      whatever Groq originally provided)

    Never raises — if the NLM call fails for any reason (network issue, timeout,
    unexpected response format), it returns verified=False and the caller keeps
    Groq's original value. A failed terminology lookup should never fail a job.
    """
    try:
        params = urllib.parse.urlencode({
            "terms": condition_name,
            "maxList": 1,          # only need the top result
            "sf": "code,name",     # search fields: code and name
            "df": "code,name",     # return fields: code and name
        })
        url = f"{NLM_ICD10_URL}?{params}"

        # urllib is in the standard library — no extra dependency needed.
        # Timeout of 5 seconds: if NLM is slow we fail fast rather than
        # blocking the worker task.
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        # NLM response format: [total_results, codes_list, extra, results_list]
        # results_list is a list of [code, name] pairs.
        # Example: [3, ["I60.9", "I60.0"], {}, [["I60.9", "Nontraumatic SAH..."], ...]]
        if not data or len(data) < 4:
            logger.warning(f"NLM returned unexpected format for '{condition_name}'")
            return {"verified": False}

        total_results = data[0]
        results = data[3]  # list of [code, name] pairs

        if total_results == 0 or not results:
            logger.warning(f"NLM found no ICD-10 match for '{condition_name}'")
            return {"verified": False}

        top_result = results[0]
        verified_code = top_result[0]
        verified_description = top_result[1]

        logger.info(
            f"ICD-10 verified: '{condition_name}' -> {verified_code} ({verified_description})"
        )
        return {
            "code": verified_code,
            "description": verified_description,
            "verified": True,
        }

    except Exception as e:
        # Catch everything — network errors, timeouts, malformed responses.
        # A terminology lookup failure must never cause a job to fail.
        logger.warning(f"ICD-10 lookup failed for '{condition_name}': {type(e).__name__}: {e}")
        return {"verified": False}


def enrich_conditions_with_verified_icd10(conditions: list) -> list:
    """
    Take the possible_conditions list from the AI response and enrich each
    condition with a verified ICD-10 code from NLM.

    For each condition:
    - Calls verify_icd10() with the condition name
    - If verified: replaces icd10 with the NLM code, adds icd10_description
      and icd10_verified=True
    - If not verified: keeps Groq's original icd10 value, adds
      icd10_verified=False so the caller knows the code is unconfirmed

    Returns the enriched list. The original list is not mutated.
    """
    enriched = []

    for condition in conditions:
        updated = dict(condition)  # copy so we don't mutate the original
        condition_name = condition.get("condition", "")
        groq_code = condition.get("icd10", "")

        result = verify_icd10(condition_name)

        if result["verified"]:
            updated["icd10"] = result["code"]
            updated["icd10_description"] = result["description"]
            updated["icd10_verified"] = True
        else:
            # Keep Groq's code but flag it as unverified
            updated["icd10"] = groq_code
            updated["icd10_description"] = None
            updated["icd10_verified"] = False

        enriched.append(updated)

    return enriched