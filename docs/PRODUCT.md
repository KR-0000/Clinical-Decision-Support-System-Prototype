# Clinical Decision Support Prototype

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Clinicians and developers evaluating structured review of referral summaries, and recruiters exploring the technical portfolio with limited time. This is an evaluation prototype, not validated software for patient care.

## Product Purpose

Submit narrative text or a text-based PDF; review a structured differential, reasoning, ICD-10 codes, red flags, next steps, and missing information.

## Operating Context

Existing static frontend on Render; FastAPI, Celery, Upstash Redis, Supabase database/storage, Groq analysis and NLM terminology lookup. Preserve these services during this update.

## Capabilities and Constraints

- Two core pages: submission and result review, with asynchronous queued/processing/failure states.
- Current phase: integrate the user-approved interactive design into the live application's frontend, with real API submissions and an isolated simulated walkthrough.
- No accounts, history, new clinical-question input, or fabricated citations.
- User approved the design and authorized implementation, automated tests, browser/live synthetic checks, commit and push to GitHub. Report deployment verification separately from local verification.
- Code lookup verifies terminology existence, not diagnosis correctness.

## Brand Commitments

User requests a conventional commercial clinical application, with Isabel and VisualDx as reference craft levels. Retain Source Sans 3 and Source Code Pro from the original prototype. Restrained blue; no decorative colored side stripes. Minimize icons and boxed sections. Keep useful warning callouts and an animated clock/gear progress timeline with reduced-motion support.

## Evidence on Hand

README.md documents architecture and prototype limitations. tests/fixtures/clinical_cases.py contains synthetic test cases. The earlier generated PNG studies are rejected as implementation authority; actual rendered prototypes must establish the design.

## Product Principles

- Make reasoning and missing information easy to review without unnecessary clicks.
- Distinguish clinical urgency, model likelihood, and terminology verification.
- Show honest operational states and recovery actions.
- Offer obvious fictional example cases and a short optional visual walkthrough. Respect dismissal and do not interrupt typing.
- A live-demo action should wake sleeping services automatically; a second browser tab is a fallback, not a prerequisite. A health-server response is not evidence that Celery is consuming jobs.
- Never fabricate features to fill navigation or dashboard space.
