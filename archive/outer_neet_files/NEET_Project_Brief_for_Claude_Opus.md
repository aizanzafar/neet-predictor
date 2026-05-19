# NEET Rank + College Prediction MVP: Input File for Claude Opus

## 1. Project Name

NEET UG Rank and College Prediction MVP

---

## 2. Business/Product Idea

Build a student-facing NEET UG prediction tool that estimates:

- likely All India Rank from NEET marks if rank is not available,
- likely MCC All India counselling options,
- likely Karnataka KEA counselling options,
- admission probability category: Safe / Likely / Borderline / Unlikely,
- explanation based on previous-year cutoffs.

The first version will focus only on:

- All India / MCC counselling.
- Karnataka / KEA counselling.
- MBBS and BDS.
- Historical data from 2020 to 2024.
- 2025 used only for validation/backtesting.

---

## 3. Why This Product

Students and parents often struggle to interpret NEET marks, ranks, quotas, state counselling rules, categories, and previous-year cutoffs.

Existing prediction tools are often unclear about:

- which quota was used,
- which round was used,
- whether MCC or state counselling data was used,
- whether private/deemed/management/NRI seats are mixed,
- how confident the prediction is.

This product should be more transparent and explainable.

---

## 4. Target Users

Primary users:

- NEET UG students.
- Parents.
- Counselling advisors.
- Small admission counselling businesses.

Initial geography:

- India overall through MCC.
- Karnataka through KEA.

---

## 5. First MVP Scope

### Included

- Marks-to-rank estimation.
- AIR-based college prediction.
- MCC counselling prediction.
- Karnataka KEA counselling prediction.
- MBBS and BDS.
- Category-aware predictions.
- Quota-aware predictions.
- Round-aware historical evidence.
- Safe / Likely / Borderline / Unlikely labels.
- Basic UI.
- Source provenance.

### Excluded from MVP

- Other Indian states except Karnataka.
- Payment system.
- User accounts.
- Real-time counselling automation.
- Seat locking or choice-filling automation.
- Guarantee of admission.
- Complex black-box ML unless clearly justified.
- End-to-end scraping of every source if manual CSV ingestion is more reliable at first.

---

## 6. Mandatory User Inputs

The form must remain simple.

Mandatory:

1. NEET marks out of 720.
2. NEET All India Rank, if available.
   - If AIR is given, use it directly.
   - If AIR is missing, estimate AIR from marks.
3. Home state.
4. National category:
   - General / UR
   - OBC / OBC-NCL
   - SC
   - ST
   - EWS
5. Karnataka counselling interest:
   - Yes
   - No

Conditional mandatory fields if Karnataka counselling interest = Yes:

6. Karnataka domicile eligibility:
   - Yes
   - No
   - Not sure

7. Karnataka category:
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

---

## 7. Optional User Inputs

These should not block prediction.

1. Course preference:
   - Default: All eligible courses.
   - Options:
     - MBBS
     - BDS
     - MBBS + BDS

2. College type preference:
   - Default: All eligible seat/college types.
   - Multi-select:
     - Government colleges
     - Private government quota seats
     - Private open seats
     - Management quota
     - NRI quota
     - Deemed universities

3. Budget / maximum annual fee:
   - Optional.
   - Default: No fee filter.

4. Preferred location / district:
   - Optional.
   - Default: All locations.

---

## 8. Data Needed

### Marks-to-Rank Data

For 2020 to 2025:

- NEET marks.
- AIR or rank band.
- percentile if available.
- number of candidates.
- exam year.
- source.

Use 2020-2024 for training/design.
Use 2025 for validation/backtesting.

### MCC Data

For 2020 to 2025:

- counselling year.
- round.
- college.
- course.
- quota.
- category.
- opening rank.
- closing rank.
- seat type.
- source.

### Karnataka KEA Data

For 2020 to 2025:

- counselling year.
- round.
- college.
- course.
- KEA category.
- quota/seat type.
- opening rank.
- closing rank.
- seat matrix.
- source.

### College Metadata

- college name.
- state.
- district.
- ownership.
- counselling authority.
- course.
- intake.
- fee range if available.
- recognition status if available.
- source.

---

## 9. Prediction Output

For each predicted option, show:

- rank used for prediction,
- whether rank is actual AIR or estimated,
- college name,
- course,
- counselling authority,
- category matched,
- quota/seat type,
- round evidence,
- previous-year cutoff trend,
- prediction label:
  - Safe
  - Likely
  - Borderline
  - Unlikely
- explanation,
- warning/disclaimer.

---

## 10. Important Constraints

The system must not:

- mix MCC and KEA cutoffs,
- mix categories incorrectly,
- mix quotas incorrectly,
- mix MBBS/BDS cutoffs,
- treat management/NRI/deemed/government seats as the same,
- guarantee admission,
- hallucinate data,
- hide source limitations.

The system must:

- keep source provenance,
- show confidence,
- be conservative,
- handle missing optional fields,
- clearly separate prediction from official counselling advice.

---

## 11. Preferred MVP Technology

Use a simple Python-first stack.

Possible stack:

- Python
- Pandas
- SQLite or PostgreSQL
- Scikit-learn for marks-rank model if needed
- Streamlit for fastest MVP UI
- FastAPI later if needed
- Pytest for testing

The system should be modular enough to later migrate from Streamlit to React/FastAPI.

---

## 12. Required Claude Opus Output

Claude Opus should produce:

1. Final architecture.
2. Corrected product scope.
3. Final user-input design.
4. Data dictionary.
5. Database schema.
6. Prediction algorithm.
7. Scoring formula.
8. Backtesting plan.
9. Edge cases.
10. Data-cleaning risks.
11. Folder structure.
12. UI flow.
13. Test plan.
14. Phased implementation roadmap.
15. Final prompt for Codex implementation.
