# Interactive design plan and independent review

Status: isolated prototype, pending user review before production integration. This review used the rendered desktop screenshot and source; it did not consult detector findings. Browser and functional verification are separate gates.

## Proposed screens and states

| State | Purpose and interaction |
| --- | --- |
| Text entry | Clinical summary, guidance, character count, synthetic sample and validation. |
| PDF upload | Text-based PDF selection, size/type feedback and removal. |
| Queued | Submitted/queued/analyzing/ready timeline, elapsed time and animated clock. |
| Processing | Same timeline with active analysis stage and animated gear. |
| Results | Summary, visible differential reasoning, inline ICD-10 verification, likelihood and review priorities. |
| Long results | Stress layout with long names and reasoning; disclose only genuinely extended content. |
| Empty results | Explain missing output without implying clinical reassurance. |
| Print layout | Readable full review without navigation and action controls. |
| Connection interrupted | Preserve the draft and distinguish uncertain submission from confirmed failure. |
| Analysis failed | Explain failed status and provide status check or return to the case. |

The screen selector and navy-header comparison belong only to design review. These are states of the existing submission/review workflow, not ten invented product pages.

## Design decisions

- Retain the original Source Sans 3 in weights 400/600: 16px body, 14px secondary text, 18px section headings and 24px title. Use Source Code Pro only for codes and identifiers.
- Use white reading surfaces on gray `#f4f6f7`, dark text `#20303c` and blue `#235c91` actions. The optional header uses navy `#17324d`.
- Reserve muted red for red flags and amber for urgency. Likelihood uses neutral tonal differences; it must not be mistaken for urgency. Small green verification marks establish terminology lookup only, never diagnostic correctness.
- Keep short reasoning visible. Use whitespace, typography and placement before adding cards or icons. No decorative blue side stripes.
- Put review priorities alongside the report on desktop and make red flags prominent on narrow screens. Animate only the active clock/gear and honor reduced-motion preferences.

## Independent findings

The prototype materially improves on the generated image studies. Its real font rendering, visible reasoning, compact verification marks and differentiated likelihood badges support scanning. The conventional clinical workspace is appropriate; novelty is not a goal.

Findings were handed to the builder and **were not yet verified as fixed when this review was written**:

1. Reconcile mobile visual and semantic reading order: red flags visually move ahead of the report but originally followed the entire differential in the DOM.
2. Explicitly explain that submission always produces a fixed fictional result; typed text and PDFs are not interpreted.
3. Distinguish starting a genuinely new case from returning to the retained draft. Recovery should use an accurate label such as “Edit case.”
4. Expand stress fixtures beyond repeated prose: lengthy diagnosis names, several red flags, long missing-information items and absent optional sections.

Nonblocking observations: next-step and missing-information counts may add clutter; the generic reasoning note earns its space only when backed by meaningful output. Keep urgency and red flags distinct, and avoid further warning decoration.

## Isolation and next gate

The preview uses fictional fixtures, makes no clinical service requests and persists no case data. Google Fonts supplies typography. PDF handling checks the chosen file locally; it does not upload or analyze it. Verification badges are illustrative.

Complete browser, responsive, keyboard, motion, copy/print and error checks, plus the independent detector review. Show the working prototype for user feedback before changing the production interface. Production integration subsequently requires the repository test suite and live synthetic workflow checks; this document does not claim clinical validation or production readiness.

## Verification update

The builder applied the four review corrections, plus explicit invalid-field accessibility state, a print verification explanation and removal of duplicated copied reasoning. Browser inspection confirmed red flags precede the report in the semantic tree, the simulation disclosure appears, New case clears the draft, and long mode includes three flags. Desktop and 390px mobile layouts were inspected with no horizontal overflow. Source Sans 3 loaded successfully. Text/PDF missing-input validation, queued/processing transitions, recovery controls, extended reasoning, empty results, clipboard success and the print-layout view were exercised. The clock has an active rotation animation; reduced-motion support was verified in CSS, not through OS preference emulation. Native printing and actual PDF selection were not exercised.

Final JavaScript syntax check passed; Impeccable detector returned zero findings. Repository suite: 222 passed with two existing Pydantic deprecation warnings. The initial sandbox test run stalled; the permitted nonsandbox rerun completed successfully. No new production deployment or live clinical API test was performed for this isolated preview.

Open http://127.0.0.1:8766/ while the preview server is running. To restart from the repository root: `.\\.venv\\Scripts\\python.exe -m http.server 8766 --bind 127.0.0.1 --directory design-preview`. Review uses synthetic fixtures only. Design tokens remain provisional until user review; the production interface has not adopted this design.
