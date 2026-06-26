"""
22 clinical test fixtures across 10 categories.

Each fixture is a dict with:
  id           - unique slug for parametrize IDs
  category     - one of the 10 clinical domains
  case_text    - the case description submitted to the API
  urgency      - expected urgency tier (Emergent / Urgent / Semi-urgent / Non-urgent)
  key_terms    - words that should appear somewhere in the AI differential (checked
                 against a mocked response in test_clinical_cases.py)
"""

CLINICAL_CASES = [
    # ── Cardiac (3) ──────────────────────────────────────────────────────────
    {
        "id": "cardiac_stemi",
        "category": "cardiac",
        "case_text": (
            "65-year-old male with sudden onset crushing substernal chest pain radiating "
            "to the left arm and jaw, diaphoresis, nausea, and vomiting for 45 minutes. "
            "BP 145/90, HR 102, RR 18, SpO2 96%. History of hypertension and hyperlipidemia. "
            "On lisinopril and atorvastatin. 30 pack-year smoking history. "
            "ECG shows 3mm ST elevation in V1-V4 with reciprocal changes in inferior leads."
        ),
        "urgency": "Emergent",
        "key_terms": ["myocardial infarction", "STEMI"],
    },
    {
        "id": "cardiac_aortic_dissection",
        "category": "cardiac",
        "case_text": (
            "55-year-old male with sudden onset severe tearing chest pain radiating to the "
            "back between shoulder blades, onset at rest. BP 180/100 right arm, 140/85 left arm. "
            "HR 110, RR 20, SpO2 98%. History of uncontrolled hypertension, Marfan features noted. "
            "No prior cardiac history. Peripheral pulses asymmetric. CXR shows widened mediastinum."
        ),
        "urgency": "Emergent",
        "key_terms": ["aortic dissection"],
    },
    {
        "id": "cardiac_heart_failure",
        "category": "cardiac",
        "case_text": (
            "72-year-old female with progressive dyspnea on exertion over 2 weeks, now dyspnea "
            "at rest and orthopnea requiring 3 pillows. Bilateral leg edema to mid-calf. "
            "BP 165/95, HR 96, RR 22, SpO2 90% on room air. JVD present, S3 gallop on auscultation, "
            "bibasilar crackles. History of ischemic cardiomyopathy, EF 30% on last echo."
        ),
        "urgency": "Urgent",
        "key_terms": ["heart failure"],
    },

    # ── Neurological (3) ─────────────────────────────────────────────────────
    {
        "id": "neuro_sah",
        "category": "neurological",
        "case_text": (
            "58-year-old female with sudden onset severe headache described as worst headache "
            "of her life, rated 10/10, onset during exertion. Associated neck stiffness, nausea, "
            "and vomiting. BP 178/102, HR 88, temp 37.8C, GCS 14. No prior headache history, "
            "no anticoagulants. Pupils equal and reactive. No focal neurological deficits."
        ),
        "urgency": "Emergent",
        "key_terms": ["subarachnoid hemorrhage"],
    },
    {
        "id": "neuro_ischemic_stroke",
        "category": "neurological",
        "case_text": (
            "72-year-old male with sudden onset right-sided facial droop, right arm and leg "
            "weakness, and slurred speech for 90 minutes. Last known well 2 hours ago. "
            "BP 195/110, HR 82, RR 16, SpO2 97%, temp 37.0C. History of atrial fibrillation, "
            "not on anticoagulation. NIHSS 12. No recent surgery or trauma."
        ),
        "urgency": "Emergent",
        "key_terms": ["ischemic stroke", "cerebral infarction"],
    },
    {
        "id": "neuro_meningitis",
        "category": "neurological",
        "case_text": (
            "22-year-old male college student with 12-hour history of fever, severe headache, "
            "neck stiffness, photophobia, and phonophobia. Vomiting twice. BP 110/70, HR 120, "
            "temp 39.8C, RR 18, GCS 14. Non-blanching petechial rash on trunk and legs. "
            "Kernig sign positive. No recent travel, immunocompetent."
        ),
        "urgency": "Emergent",
        "key_terms": ["meningitis"],
    },

    # ── Respiratory (2) ──────────────────────────────────────────────────────
    {
        "id": "respiratory_pe",
        "category": "respiratory",
        "case_text": (
            "45-year-old female 6 days post right hip replacement with sudden onset dyspnea, "
            "pleuritic right-sided chest pain, and hemoptysis. HR 118, RR 24, BP 105/70, "
            "SpO2 92% on room air, temp 37.5C. Right calf swelling and tenderness. "
            "Wells score 6. No prior VTE history. On enoxaparin prophylaxis post-surgery."
        ),
        "urgency": "Emergent",
        "key_terms": ["pulmonary embolism"],
    },
    {
        "id": "respiratory_cap",
        "category": "respiratory",
        "case_text": (
            "67-year-old male with 5-day history of productive cough with yellow-green sputum, "
            "fever, and right-sided pleuritic chest pain. BP 128/80, HR 95, temp 38.9C, "
            "RR 20, SpO2 94% on room air. Decreased breath sounds and dullness to percussion "
            "right lower lobe. History of COPD, current smoker."
        ),
        "urgency": "Urgent",
        "key_terms": ["pneumonia"],
    },

    # ── Sepsis / Infectious (2) ───────────────────────────────────────────────
    {
        "id": "sepsis_septic_shock",
        "category": "sepsis",
        "case_text": (
            "68-year-old female nursing home resident with 2-day history of dysuria and flank pain, "
            "now presenting with altered mental status and hypotension. BP 82/50, HR 128, "
            "temp 39.2C, RR 26, SpO2 95%. Lactate 4.2 mmol/L. WBC 22,000 with left shift. "
            "History of recurrent UTIs, T2DM. Foley catheter in situ."
        ),
        "urgency": "Emergent",
        "key_terms": ["sepsis", "septic shock"],
    },
    {
        "id": "sepsis_necrotizing_fasciitis",
        "category": "sepsis",
        "case_text": (
            "50-year-old male with diabetes presenting with 48-hour history of rapidly "
            "worsening left lower leg pain, erythema, swelling with crepitus on palpation, "
            "and skin bullae. Pain out of proportion to examination. BP 95/60, HR 120, "
            "temp 39.5C. WBC 28,000. Lactate 3.8. Recent minor skin abrasion at the site."
        ),
        "urgency": "Emergent",
        "key_terms": ["necrotizing fasciitis"],
    },

    # ── GI / Surgical (2) ────────────────────────────────────────────────────
    {
        "id": "gi_appendicitis",
        "category": "gastrointestinal",
        "case_text": (
            "24-year-old male with 18-hour history of periumbilical pain migrating to right "
            "lower quadrant, anorexia, nausea, and one episode of vomiting. Temp 38.2C, "
            "HR 95, BP 118/76. RLQ tenderness with guarding, positive Rovsing sign, "
            "positive psoas sign. WBC 14,500 with neutrophilia. No prior abdominal surgeries."
        ),
        "urgency": "Urgent",
        "key_terms": ["appendicitis"],
    },
    {
        "id": "gi_bowel_obstruction",
        "category": "gastrointestinal",
        "case_text": (
            "60-year-old male with prior right hemicolectomy presenting with 24-hour history "
            "of colicky abdominal pain, abdominal distension, vomiting, and absolute constipation. "
            "BP 130/85, HR 100, temp 37.4C. Abdomen distended and tympanitic with high-pitched "
            "bowel sounds. AXR shows multiple air-fluid levels. No flatus for 24 hours."
        ),
        "urgency": "Urgent",
        "key_terms": ["bowel obstruction", "intestinal obstruction"],
    },

    # ── Obstetric (2) ────────────────────────────────────────────────────────
    {
        "id": "obs_eclampsia",
        "category": "obstetric",
        "case_text": (
            "28-year-old female at 36 weeks gestation with severe headache, visual disturbances, "
            "and right upper quadrant pain. BP 168/112, HR 98, RR 18. Generalized tonic-clonic "
            "seizure witnessed for 90 seconds. 3+ proteinuria on dipstick. Reflexes brisk with "
            "clonus. Fetal heart rate 155 bpm. No prior hypertension history."
        ),
        "urgency": "Emergent",
        "key_terms": ["eclampsia"],
    },
    {
        "id": "obs_ectopic",
        "category": "obstetric",
        "case_text": (
            "26-year-old female G1P0 with 7 weeks amenorrhea, left lower quadrant sharp pain "
            "radiating to shoulder tip, and vaginal spotting. BP 96/60, HR 118, temp 37.0C. "
            "Tender adnexa on left, cervical motion tenderness. Positive urine hCG. "
            "Serum hCG 2,400 IU/L. Prior history of PID. Ultrasound: no intrauterine pregnancy."
        ),
        "urgency": "Emergent",
        "key_terms": ["ectopic pregnancy"],
    },

    # ── Endocrine (2) ────────────────────────────────────────────────────────
    {
        "id": "endo_dka",
        "category": "endocrine",
        "case_text": (
            "19-year-old male with known type 1 diabetes presenting with 24-hour history of "
            "nausea, vomiting, polyuria, polydipsia, and abdominal pain. Kussmaul breathing noted. "
            "BP 100/65, HR 112, temp 37.1C. Glucose 28 mmol/L, bicarbonate 10, pH 7.18, "
            "ketones 3+. Last insulin dose skipped due to illness."
        ),
        "urgency": "Emergent",
        "key_terms": ["diabetic ketoacidosis", "DKA"],
    },
    {
        "id": "endo_addisonian_crisis",
        "category": "endocrine",
        "case_text": (
            "35-year-old female with known Addison disease who stopped her hydrocortisone 3 days "
            "ago due to vomiting illness. Presents with severe fatigue, confusion, abdominal pain, "
            "and weakness. BP 78/48, HR 120, temp 37.8C. Sodium 126, potassium 6.1, glucose 3.2. "
            "Skin hyperpigmentation noted. No recent trauma or surgery."
        ),
        "urgency": "Emergent",
        "key_terms": ["adrenal", "addisonian"],
    },

    # ── Trauma (2) ───────────────────────────────────────────────────────────
    {
        "id": "trauma_tbi",
        "category": "trauma",
        "case_text": (
            "30-year-old male restrained driver in high-speed MVA. Initial GCS 10 at scene, "
            "now GCS 12 in ED. Left pupil 5mm sluggishly reactive, right 3mm brisk. "
            "BP 160/90, HR 58, RR 14 (Cushing triad pattern). Laceration to left temporal region. "
            "Reports headache and one episode of vomiting. No anticoagulants."
        ),
        "urgency": "Emergent",
        "key_terms": ["traumatic brain injury", "intracranial hemorrhage"],
    },
    {
        "id": "trauma_hemorrhagic_shock",
        "category": "trauma",
        "case_text": (
            "40-year-old male pedestrian struck by vehicle. BP 78/50, HR 138, RR 26, GCS 13. "
            "Obvious deformity right femur, distended abdomen, decreased breath sounds left. "
            "Estimated blood loss 2L. Pelvis unstable on compression. SpO2 88% on 15L NRB. "
            "Massive transfusion protocol activated. No past medical history available."
        ),
        "urgency": "Emergent",
        "key_terms": ["hemorrhagic shock", "trauma"],
    },

    # ── Psychiatric / Toxicological (2) ──────────────────────────────────────
    {
        "id": "psych_lithium_toxicity",
        "category": "psychiatric",
        "case_text": (
            "45-year-old female with bipolar disorder on lithium 1200mg/day presenting with "
            "3-day history of coarse tremor, confusion, ataxia, and slurred speech. Has been "
            "dehydrated due to gastroenteritis. BP 108/70, HR 88, temp 37.2C. Serum lithium "
            "3.2 mEq/L (therapeutic 0.6-1.2). Creatinine elevated at 180 umol/L."
        ),
        "urgency": "Urgent",
        "key_terms": ["lithium toxicity"],
    },
    {
        "id": "psych_acute_psychosis",
        "category": "psychiatric",
        "case_text": (
            "25-year-old male brought in by family with 2-week history of first episode of "
            "disorganized speech, auditory and visual hallucinations, paranoid delusions, "
            "and social withdrawal. No prior psychiatric history. BP 125/80, HR 88, temp 37.0C, "
            "GCS 15. Urine toxicology positive for cannabis only. No neurological deficits. "
            "No recent medication changes or medical illness."
        ),
        "urgency": "Urgent",
        "key_terms": ["psychosis"],
    },

    # ── Dermatological / Allergic (2) ────────────────────────────────────────
    {
        "id": "derm_anaphylaxis",
        "category": "dermatological",
        "case_text": (
            "30-year-old female stung by bee 15 minutes ago. Generalized urticaria and angioedema, "
            "stridor, bronchospasm, and hypotension. BP 78/48, HR 128, SpO2 88% on room air, "
            "RR 28. Throat feels tight. Prior history of bee sting reaction requiring EpiPen. "
            "No current medications. Has not received epinephrine yet."
        ),
        "urgency": "Emergent",
        "key_terms": ["anaphylaxis"],
    },
    {
        "id": "derm_sjs",
        "category": "dermatological",
        "case_text": (
            "40-year-old male started on amoxicillin 10 days ago for sinusitis, now presenting "
            "with target lesions on trunk and extremities, blistering mucosal involvement of "
            "mouth and eyes, and painful skin detachment affecting approximately 15% BSA. "
            "Temp 38.5C, HR 102, BP 118/76. Nikolsky sign positive. Ophthalmology consulted."
        ),
        "urgency": "Urgent",
        "key_terms": ["Stevens-Johnson", "toxic epidermal necrolysis"],
    },
]

CASE_IDS = [c["id"] for c in CLINICAL_CASES]
