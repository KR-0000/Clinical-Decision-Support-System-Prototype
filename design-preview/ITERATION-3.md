# Visible guided demonstration

This iteration follows the user's review of the actual browser prototype. It remains isolated from the deployed application.

## Motion and interaction plan

The focal sequence is the demonstration itself: a visible cursor chooses a substantial example, exposes the entered clinical summary, submits it, follows the timeline, then directs attention through results. A persistent whole-view frame and player controls identify demonstration mode without relying on prose. Pause, next and exit remain available; exiting restores the visitor's previous draft. Demonstration steps do not call clinical APIs.

The invitation expands from the How it works control to establish a spatial relationship. Use a short decelerating transform, not a generic card entrance or decorative bouncing. Open automatically on a fresh entry-page visit, unless the visitor is already interacting; never interrupt result deep links. Two centered choices: Start walkthrough and Explore on my own. Reduced-motion visitors receive a static invitation and manually advanced demonstration steps.

## Content plan

Remove the redundant paragraph under the example buttons and remove synthetic-label wording from the pasted clinical narratives. Label examples at the interface level. Expand all three narratives with a useful timeline, observations, examination, history, medications, allergies, relevant negatives and explicit unknowns. Keep fixture data internally consistent; examples are illustrative, not clinical recommendations. Improve What to include with three bullet groups and a clear heading.

## Reference patterns

- [Storylane demo settings](https://docs.storylane.io/editing-demos/demo-settings): explicit navigation, progress, frame and autoplay controls.
- [Storylane guided steps](https://docs.storylane.io/editing-demos/adding-and-editing-guided-steps): hotspots, spotlighting and controlled step progression.
- [Arcade interactive demos](https://www.arcade.software/product/interactive-demo): focused movement, chapters and contextual callouts.
- [Arcade changelog](https://www.arcade.software/changelog): visible cursor movement and click feedback.

These are implementation references, not evidence that this particular preview improves retention. No third-party demo service or account is required for this local implementation.

## Verification

Independent review and browser testing caught and fixed the old start-button wiring, SVG cursor visibility, and replaying completed animations on resume. The completed state now offers replay and exit without an inert Resume control. Cursor state resets between steps.

Verified automatic entry invitation, two primary choices, substantial example prefills without the old prefix, input-first playback, visible cursor, automatic completion through eight steps, pause/manual next, draft restoration on exit, and desktop/390px mobile layout. Mobile showed no horizontal overflow and retained visible player controls. JavaScript syntax, Impeccable scan (zero findings), and git whitespace check passed. Reduced-motion behavior was reviewed in code; browser OS-preference emulation was not available. No production files or live service integration changed in this iteration.
