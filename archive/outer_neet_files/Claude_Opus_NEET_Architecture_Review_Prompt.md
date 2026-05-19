# Claude Opus Architecture Review Prompt: NEET Rank + College Prediction MVP

You are a senior AI product architect, data engineer, admissions-domain analyst, and technical reviewer.

I am building an MVP for a NEET UG rank and college prediction system for India.

Before asking a coding agent like Codex to implement it, I want you to deeply review the architecture, data requirements, prediction logic, user input design, risks, and implementation plan.

Your job is NOT to write code first.

Your job is to produce a clean, practical, implementation-ready architecture document that can later be given to Codex.

---

## Product Goal

Build a NEET UG prediction system that helps a student estimate:

1. Expected NEET All India Rank from marks, if AIR is not available.
2. Likely colleges through All India / MCC counselling.
3. Likely colleges through Karnataka / KEA counselling.
4. Safe / Likely / Borderline / Unlikely admission chances.
5. Explanations based on previous-year cutoff trends, category, quota, course, round, and college type.

The first version must focus only on:

- All India counselling / MCC.
- Karnataka state counselling / KEA.
- Historical data from 2020 to 2024.
- 2025 used as held-out validation/backtesting.

Do not expand to all Indian states in the MVP.

---

## Important Product Principle

This system should be transparent and conservative.

It must not pretend to guarantee admission.

It should say:

- Prediction is based on historical cutoff trends.
- Counselling rules and seat matrices can change every year.
- User must verify official MCC/KEA/NMC/KEA notifications.
- Category, quota, domicile, and document eligibility must be confirmed officially.

---

## Current Input Design

### Mandatory Inputs

These are mandatory:

1. NEET marks out of 720.
2. NEET All India Rank, if already available.
   - If AIR is provided, use it directly.
   - If AIR is not provided, estimate AIR from marks.
3. Home state.
4. National category:
   - General / UR
   - OBC / OBC-NCL
   - SC
   - ST
   - EWS
5. Karnataka counselling interest:
   - Yes / No

If Karnataka counselling interest = Yes, then ask:

6. Karnataka domicile eligibility:
   - Yes
   - No
   - Not sure

7. Karnataka category, if applicable:
   - GM
   - 2A
   - 2B
   - 3A
   - 3B
   - SCG
   - STG
   - GMR
   - GMK
   - Hyderabad-Karnataka / Kalyana Karnataka
   - Kannada medium
   - Rural
   - Other KEA-specific category
   - Not sure

### Optional Inputs With Defaults

These should not block prediction.

8. Course preference:
   - Default: All eligible courses
   - User can select:
     - MBBS
     - BDS
     - MBBS + BDS

9. College type preference:
   - Default: All eligible college/seat types
   - Multi-select:
     - Government colleges
     - Private colleges - government quota seats
     - Private open seats
     - Management quota
     - NRI quota
     - Deemed universities

10. Budget / maximum annual fee:
   - Optional only
   - Default: No fee filter

11. Preferred location / district:
   - Optional only
   - Default: All locations

Please review whether this input design is correct for the MVP, and suggest improvements only if needed.

---

## Core System Modules

The system should have these major modules:

### Module A: Marks-to-Rank Estimator

Input:
- NEET marks out of 720
- optional year context

Output:
- estimated AIR range
- confidence band
- explanation

Requirements:
- Use 2020-2024 marks-vs-rank history.
- Use 2025 only for validation/backtesting.
- The mapping must be monotonic: higher marks cannot produce worse rank.
- Start simple: interpolation, percentile mapping, isotonic regression, or monotonic regression.
- Avoid unnecessary black-box ML for the MVP.

### Module B: College Predictor

Input:
- AIR or estimated AIR
- national category
- home state
- Karnataka domicile
- Karnataka category
- course preference
- college type preference
- optional budget
- optional district/location

Output:
For each option:
- college name
- course
- counselling authority: MCC / KEA
- quota
- category
- round
- college type
- previous-year cutoff evidence
- prediction label:
  - Safe
  - Likely
  - Borderline
  - Unlikely
- explanation

Important:
- Do not mix MCC AIQ cutoff with Karnataka KEA cutoff.
- Do not mix categories incorrectly.
- Do not mix government quota, private quota, management quota, NRI quota, and deemed university cutoffs.
- Do not mix rounds carelessly.
- Keep every prediction traceable to historical cutoff rows.

---

## Required Historical Data

Please review and refine this list.

### MCC / All India Data

Need year-wise data from 2020 to 2025:

- MCC UG counselling allotment lists.
- MCC opening and closing ranks.
- Round-wise data:
  - Round 1
  - Round 2
  - Mop-up
  - Stray vacancy
- Course-wise data:
  - MBBS
  - BDS
- Quota-wise data:
  - AIQ
  - Deemed universities
  - Central universities
  - AIIMS/JIPMER/ESIC/other MCC-handled seat pools where applicable.
- Category-wise cutoff ranks.
- College names and course IDs.
- Source URLs/files for provenance.

### Karnataka / KEA Data

Need year-wise data from 2020 to 2025:

- KEA UG NEET seat matrix.
- KEA round-wise allotment results.
- KEA cutoff ranks.
- College list.
- Course list.
- Category-wise cutoffs.
- Seat type / quota:
  - Government seats
  - Private government quota seats
  - Private seats
  - Management quota
  - NRI quota, if available
- Karnataka-specific categories:
  - GM
  - 2A / 2B / 3A / 3B
  - SCG / STG
  - GMR / GMK
  - Rural
  - Kannada medium
  - Hyderabad-Karnataka / Kalyana Karnataka
  - other KEA-specific categories.
- Source URLs/files for provenance.

### College Metadata

For every college:

- college name
- state
- district/city
- ownership:
  - government
  - private
  - deemed
- counselling authority:
  - MCC
  - KEA
  - both if applicable
- course:
  - MBBS
  - BDS
- annual intake
- seat matrix by year
- quota/seat type
- fee range if available
- recognition status if available
- source provenance

---

## Initial Data Schema Idea

Please review and improve this schema.

Suggested tables:

1. `student_queries`
2. `exams`
3. `marks_rank_history`
4. `counselling_authorities`
5. `colleges`
6. `courses`
7. `seat_matrix`
8. `quota_types`
9. `categories`
10. `cutoff_history`
11. `prediction_results`
12. `data_sources`

Every cutoff row should include:

- year
- counselling_authority
- state
- college_id
- course_id
- round
- quota
- seat_type
- category
- opening_rank
- closing_rank
- source_url
- source_file
- source_confidence
- notes

---

## Initial Prediction Logic

Review this and improve it.

### Marks-to-Rank

If AIR is given:
- Use AIR directly.
- Still optionally show where marks historically correspond.

If AIR is missing:
- Estimate AIR from marks using marks-rank history.
- Return a rank range, not a single exact rank.
- Enforce monotonicity.

### College Prediction

Use historical closing ranks.

Recent years should be weighted more heavily than older years.

Possible initial weights:
- 2024: highest
- 2023: high
- 2022: medium
- 2021: lower
- 2020: lowest

2025 should be held out for validation.

Prediction labels:

- Safe:
  User AIR is comfortably better than most relevant historical closing ranks.

- Likely:
  User AIR is better than recent closing ranks but close to the boundary.

- Borderline:
  User AIR is near the historical closing-rank range.

- Unlikely:
  User AIR is worse than most relevant historical closing ranks.

Please propose a more precise scoring formula if useful.

---

## Backtesting Plan

Use 2020-2024 to fit/design.

Use 2025 as held-out validation.

Backtest questions:

1. If a student had AIR X in 2025, would the system have predicted the college they actually got?
2. How often was the actual college inside top-5 / top-10 / top-20 predicted options?
3. How often was it inside Safe / Likely / Borderline?
4. How many false-safe predictions occurred?
5. How does performance vary by category?
6. How does performance vary between MCC and KEA?
7. How does performance vary between MBBS and BDS?
8. How does performance vary by round and quota?

Metrics:

- Top-k recall.
- False-safe rate.
- Calibration quality.
- Rank-error for marks-to-rank.
- Category-wise performance.
- Quota-wise performance.
- MCC vs KEA performance.
- MBBS vs BDS performance.

---

## What I Want From You

Please produce a detailed architecture review with the following sections:

1. Executive summary.
2. Corrected MVP scope.
3. Final user input form design.
4. Mandatory vs optional field logic.
5. Data requirements.
6. Official data source checklist.
7. Data schema revision.
8. Prediction algorithm design.
9. Marks-to-rank estimator design.
10. MCC prediction design.
11. Karnataka KEA prediction design.
12. Safe/Likely/Borderline/Unlikely scoring formula.
13. Backtesting methodology using 2025.
14. Risks and failure modes.
15. Edge cases.
16. Data-cleaning challenges.
17. Recommended folder structure.
18. API/backend design.
19. UI flow.
20. Testing strategy.
21. Documentation files needed.
22. Implementation phases for Codex.
23. Final Codex-ready implementation prompt.

Important instructions:

- Be critical. Do not simply agree.
- Identify missing assumptions.
- Identify where the plan may fail.
- Keep the MVP focused.
- Avoid overengineering.
- Do not hallucinate official data.
- Make the final output directly usable as a spec for a coding agent.
