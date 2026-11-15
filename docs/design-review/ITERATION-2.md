# Recruiter entry and clinical review iteration

Status: proposed in the isolated interactive preview; production integration remains pending design review.

## Changes to review

- Wider desktop workspace with 24px gutters; retain bounded reading lines within the report. Progress screens use task-focused alignment rather than a large centered presentation.
- Stronger explicit urgency summary near the top. High/moderate/low likelihood remain a separate ordinal assessment, not an emergency scale or calibrated probability.
- Retain Source Sans 3 for interface headings and body, with size and weight hierarchy; Source Code Pro for codes. A second display font is not needed for clinical task UI.
- Make assigned ICD-10-CM codes visibly linked to NLM MedlinePlus Connect. This provides related health information, not authoritative code-definition guidance or evidence that the diagnosis is correct. Links carry only the selected code and coding system, never case text.
- Put three named fictional case buttons above the blank entry field. Choosing a case prefills editable text; it does not silently submit it. The design preview still shows a fixed illustrative result and says so.
- Offer a first-session invitation with a brief animated workflow miniature, easy dismissal, and replay through How it works. A short delay is a review hypothesis, not an evidence-backed optimal timing. Suppress automatic interruption once the visitor interacts.
- Let impatient visitors view a simulated walkthrough without waiting for backend startup. In the integrated app, separately label live analysis so visitors know when Groq actually runs.

## Production startup plan

Repository evidence: README requires visiting cds-worker.onrender.com before submission; worker_health.py serves a separate HTTP response while Celery consumes Redis tasks. Render's free web services sleep after idle time and wake on HTTP traffic. Enqueuing a Redis task does not provide that HTTP traffic.

On an explicit live-demo/analysis action, start bounded API and worker wake requests and show Preparing analysis service. Use a fixed configured worker URL, never a user-supplied proxy target. Prefer a readable same-origin API response or narrowly configured worker CORS; do not interpret an opaque no-CORS fetch as readiness. Deduplicate requests, handle timeout/cancel, and avoid periodic keepalive traffic when no demo is requested. Do not submit duplicate cases while checking readiness.

After HTTP startup succeeds, track the actual queued job until processing proves Celery picked it up. Keep a bounded timeout with an explicit Open worker in new tab fallback and status retry. Never label a worker HTTP 200 as proof that Redis, Groq, or Celery is healthy. This functional change needs implementation tests and a deployed cold-start check after integration; the preview does not implement network warming.

Repository review recommends concurrent frontend requests to API `/health` and a new worker `/health`, with exact-origin CORS on the worker and a recognizable JSON response. Preserve the existing worker root response. Use a shared startup deadline (initial proposal: 90 seconds), per-request aborts and a single submit after startup. If submission's response is lost, do not automatically repeat the POST. The current polling loop needs an actual wall-clock deadline because its fetches are not bounded. No new API key is required. Update stale render.yaml comments that say the worker serves no HTTP.

## Evidence

- [NN/g: Onboarding tutorials vs contextual help](https://www.nngroup.com/articles/onboarding-tutorials/): unsolicited tutorials interrupt tasks; optional contextual entry is preferable. No universal one-second timing rule was found.
- [Render free services](https://render.com/docs/free): HTTP traffic wakes a sleeping service, typically taking about a minute.
- [NLM MedlinePlus Connect web application](https://medlineplus.gov/medlineplus-connect/web-application/): ICD-10-CM coding system and code parameters link to related health information.

These sources inform the choices; they do not demonstrate that this prototype increases recruiter retention. Evaluate time to first example, completion, dismissal and abandonment with real visitors before making that claim.

## Review and verification

Independent design/source review and actual browser inspection completed. Fixed its two findings: redundant urgency badge and a native-dialog close-event focus race. Retested Try an example focus on the first case button and Start walkthrough focus on main content. Checked first-visit invitation, dismissal via Escape, replay, editable example prefill, automatic queued/processing/results walkthrough, startup fallback disclosure, code-link URL, and 390px mobile layout without horizontal overflow. NLM's J18.9 link was independently opened and returned Pneumonia. JavaScript syntax and final Impeccable scan passed (zero findings). Reduced-motion handling remains implemented; OS preference emulation and actual worker startup are not claimed as tested. No production integration or deployment occurred in this iteration.
