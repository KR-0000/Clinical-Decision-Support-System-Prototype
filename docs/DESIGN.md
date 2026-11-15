---
name: Clinical Decision Support Prototype
description: A restrained clinical workspace for case submission and structured review
colors:
  ink: "#20303c"
  secondary: "#53616c"
  primary: "#235c91"
  primary-hover: "#17466f"
  ground: "#f4f6f7"
  surface: "#ffffff"
  line: "#d0d7dd"
  verification: "#276044"
  urgent: "#852c34"
  demo-frame: "#17324d"
  supporting-1: "#00000040"
  supporting-2: "#152d42"
  supporting-3: "#172b3d75"
  supporting-5: "#173f61"
  supporting-7: "#174c79"
  supporting-8: "#1b649c"
  supporting-11: "#263b4b"
  supporting-13: "#294b6a"
  supporting-14: "#30495e"
  supporting-15: "#304c65"
  supporting-16: "#344c60"
  supporting-17: "#354550"
  supporting-18: "#3c5264"
  supporting-19: "#425564"
  supporting-20: "#425d72"
  supporting-21: "#43515d"
  supporting-22: "#45647b"
  supporting-24: "#59656f"
  supporting-25: "#5b7691"
  supporting-26: "#606e79"
  supporting-27: "#654600"
  supporting-28: "#663338"
  supporting-29: "#6c927c"
  supporting-30: "#7194b2"
  supporting-31: "#76212b"
  supporting-32: "#777"
  supporting-33: "#795000"
  supporting-34: "#8495a2"
  supporting-36: "#8e9da9"
  supporting-37: "#922f35"
  supporting-38: "#9a3037"
  supporting-39: "#9bbbd5"
  supporting-40: "#9eb1c4"
  supporting-41: "#a8b5c0"
  supporting-42: "#aab7c0"
  supporting-43: "#bbc6ce"
  supporting-44: "#bbc8d1"
  supporting-46: "#d4e6f4"
  supporting-47: "#d9e6f0"
  supporting-48: "#dbe2e8"
  supporting-49: "#dceaf5"
  supporting-50: "#dfeaf2"
  supporting-51: "#e2e8ee"
  supporting-52: "#e2edf6"
  supporting-53: "#e4eaf0"
  supporting-54: "#e4edf4"
  supporting-55: "#e4eee8"
  supporting-56: "#e8ecef"
  supporting-57: "#e8edf1"
  supporting-58: "#e8eef2"
  supporting-59: "#e9edf0"
  supporting-60: "#ebeff2"
  supporting-61: "#edf1f4"
  supporting-62: "#edf2f5"
  supporting-63: "#edf3f7"
  supporting-64: "#edf3f8"
  supporting-65: "#eef2f5"
  supporting-66: "#f0f2f4"
  supporting-67: "#f0f3f5"
  supporting-68: "#f1f4f6"
  supporting-69: "#f3e4bf"
  supporting-71: "#f5f7f9"
  supporting-72: "#f9e9e9"
  supporting-73: "#ffe6e8"
  supporting-75: "#fff2d7"
typography:
  caption:
    fontSize: "12px"
  title:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 600
    lineHeight: 1.25
  heading:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.35
  body:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  secondary:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
  code:
    fontFamily: "Source Code Pro, monospace"
    fontSize: "13px"
  supporting-15px:
    fontSize: "15px"
  supporting-17px:
    fontSize: "17px"
  supporting-20px:
    fontSize: "20px"
  supporting-22px:
    fontSize: "22px"
  supporting-23px:
    fontSize: "23px"
  supporting-26px:
    fontSize: "26px"
  supporting-28px:
    fontSize: "28px"
rounded:
  annotation: "8px"
  control: "5px"
  dialog: "12px"
spacing:
  small: "8px"
  medium: "16px"
  gutter: "24px"
---

# Design System: Clinical Decision Support Prototype

## Overview

The user approved a conventional clinical workspace after reviewing rendered code prototypes. Precision, visible reasoning and clear task states guide the design. Recruiters can explore substantial example cases and a short optional demonstration; clinicians can scan urgency, differential reasoning and missing information.

## Colors

White reading surfaces sit on a subtle gray ground. Blue identifies actions and links. Urgency uses a prominent burgundy treatment; likelihood uses neutral tonal differences and ordinal bars. Green terminology marks communicate code lookup only. The navy demo frame makes simulated playback unmistakable.

## Typography

Source Sans 3 serves headings and body with deliberate size and weight hierarchy. Source Code Pro is reserved for ICD-10 codes and identifiers. Short clinical reasoning remains visible. Body text uses a bounded reading measure around 65–75 characters.

## Layout

The desktop workspace uses a maximum width of 1440px and 24px outer gutters. Results place the report beside review priorities. On narrow screens, red flags precede the report in both semantic and visual order. Submission puts obvious example buttons above the editor and grouped bullet guidance beside it.

## Elevation & Depth

Routine workspace surfaces remain flat. The focused welcome dialog uses one offset, blurred neutral shadow. The demonstration uses a full-view frame rather than nested content cards.

## Shapes

Controls have small radii and clear borders. Dialogs use a 12px radius. Icons are sparse, consistently stroked SVGs for meaningful warnings, verification, upload and progress.

## Components

Primary actions use filled blue buttons; secondary actions use outlined buttons. Code links are visibly underlined and open related NLM MedlinePlus information. The urgency banner is distinct from diagnosis likelihood. Progress uses submitted, queued, analyzing and ready stages without invented percentages. Only active clock/gear symbols animate.

The invitation grows from How it works into a centered dialog with Start walkthrough and Explore on my own. A framed demo begins with input, then follows submission and results using a visible cursor. Pause, next and exit remain reachable. Exit restores the previous draft. Reduced-motion visitors receive manual progression without sweeping motion.

The entry page groups short patient-led example buttons into well-documented cases and incomplete or off-topic input. Titles truncate visually while retaining their full accessible names. Grouping uses space rather than decorative dividers. A prominent Start walkthrough action appears before How it works and uses one finite attention animation after 1.5 seconds. The automatic invitation waits 2.6 seconds and expands over 700 milliseconds. Tour explanations appear beside highlighted targets with directional arrows, following the guided-tour popover pattern documented by Driver.js.

## Do's and Don'ts

- Do distinguish urgency, likelihood and terminology verification.
- Do label synthetic examples outside the clinical narrative.
- Do preserve focus, keyboard controls, readable errors and draft recovery.
- Don't add decorative colored side stripes, eyebrow labels, excessive icons or nested cards.
- Don't hide short reasoning behind unnecessary disclosures.
- Don't imply that an HTTP health response proves Celery or Groq readiness.
