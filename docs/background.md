## Background and motivation

Consider a common care transition scenario: a patient visits their primary care physician, who determines they need hospital-level care. The physician writes a referral and prepares a clinical summary documenting the patient's history, current medications, vitals, and preliminary findings. When the patient arrives at the hospital and is being admitted, the receiving clinician needs to quickly orient themselves to that documentation before deciding on a course of action.

This tool is designed for that kind of moment. A clinician can paste in a clinical summary or upload it as a PDF, and receive a structured output covering likely conditions, urgency level, red flags that may require immediate attention, and suggested next diagnostic steps. The intent is to reduce the cognitive load of synthesizing a dense referral document under time pressure, not to replace the clinician's judgment.

Healthcare systems in the US already handle care transitions at scale through EHR integrations and HL7 data exchange pipelines. This project is my attempt to prototype the core problem at a smaller scale, and to build hands-on experience with the full engineering stack involved: async task queues, LLM APIs, structured output validation, containerization, and cloud deployment. It is not production software and has not been validated clinically.

**Intended audience:** Medical professionals or developers evaluating the tool's behavior. This tool supports clinical reasoning and must not be used as a standalone diagnostic instrument.
