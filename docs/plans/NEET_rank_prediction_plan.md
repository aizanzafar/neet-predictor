# NEET Rank + College Prediction Plan

## 1. Product Role

Build a NEET UG prediction system that accepts a student’s marks/rank/profile and returns:

1. Expected All India Rank (AIR) from marks.
2. Expected Karnataka state counselling opportunities.
3. Possible MBBS/BDS college options under:
   - All India Quota / MCC counselling.
   - Karnataka state quota / KEA counselling.
   - Government, private, minority, NRI, and management categories where applicable.
4. Confidence bands instead of one hard answer.
5. Explanation of why a college is predicted: previous-year closing rank, category, quota, round, fee type, and seat type.

The system should not claim guaranteed admission. It should produce probability bands: Safe, Likely, Borderline, Unlikely.

---

## 2. Initial Scope

### Phase 1 Scope

Focus only on:

1. NEET UG MBBS/BDS prediction.
2. All India Rank prediction from marks.
3. All India Quota counselling through MCC.
4. Karnataka state counselling through KEA.
5. Historical data from 2020–2024.
6. 2025 as test/validation year.

### Recommended Data Window

Use 2020–2024 as the first training/backtesting window and use 2025 as the holdout validation year.

Reason:

- Five years is enough to capture post-COVID normalization, paper difficulty variation, rank inflation, counselling changes, and seat expansion.
- 2025 is ideal for testing because it is recent and already includes a different score/rank pattern compared with 2024.
- For the final production system, keep extending the dataset yearly: 2019–2025, then 2026 onward.

### Important Decision

Do not train only on 2024. NEET marks-to-rank changes sharply every year due to paper difficulty and score distribution. The model must learn year-specific normalization.

---

## 3. User Inputs Required

### Minimum Required Inputs

These are mandatory for prediction:

1. NEET marks out of 720.
2. NEET All India Rank, if already available.
3. Home state.
4. Category:
   - General / UR
   - OBC / OBC-NCL
   - SC
   - ST
   - EWS
5. Karnataka category, if applying through Karnataka counselling:
   - GM
   - 2A / 2B / 3A / 3B
   - SCG / STG
   - GMR / GMK / Hyderabad-Karnataka / Kannada / Rural / other KEA-specific categories, as applicable.
6. Domicile eligibility for Karnataka.
7. Course preference:
   - MBBS only
   - BDS only
   - MBBS + BDS
8. College type preference:
   - Government
   - Private government quota seats
   - Private open seats
   - Management quota
   - NRI quota
   - Deemed universities
9. Budget / maximum annual fee range.
10. Preferred location or district.

### Strongly Recommended Inputs

These improve college prediction quality:

1. Gender, only if a specific quota/college rule uses it.
2. PwD status.
3. Minority eligibility:
   - Linguistic minority
   - Religious minority
   - Institution-specific minority quota
4. Kannada medium / rural / HK region eligibility, if applicable.
5. Willingness to participate in later rounds:
   - Round 1 only
   - Round 2
   - Mop-up
   - Stray vacancy
6. Willingness for high-fee private/deemed colleges.
7. Whether the student wants only Karnataka or all India options.
8. Whether the student is open to BDS/AYUSH as backup.

### Optional Inputs for Future Personalization

1. Preferred college ranking priority:
   - Reputation
   - Low fee
   - City preference
   - Chance of admission
   - Clinical exposure
2. Bond/service obligation preference.
3. Hostel requirement.
4. Parent/student risk preference:
   - Conservative
   - Balanced
   - Aggressive option filling.

---

## 4. Data Required

The system needs two major data layers:

1. Rank prediction data.
2. College allotment prediction data.

---

## 5. Rank Prediction Data

### Required Fields

For each year from 2020 to 2025:

1. Year.
2. Total candidates registered.
3. Total candidates appeared.
4. Total candidates qualified.
5. Category-wise candidate counts.
6. Marks range versus AIR.
7. Percentile versus marks, if available.
8. Qualifying cutoff by category.
9. Tie-breaking rule for that year.
10. Exam difficulty indicators, if available:
    - Topper score.
    - Number of candidates above 700.
    - Number of candidates above 650, 600, 550, etc.
    - Score distribution table.

### Primary Source

Use NTA official NEET result press releases and information bulletins.

### Why This Matters

The same marks can lead to very different AIR across years. For example, if a paper is easier, more students score high, and the same marks produce a worse rank. Therefore, the model should learn from marks distribution, not only from a static marks-vs-rank table.

---

## 6. All India Counselling Data Required

### Authority

MCC handles online counselling for 15% All India Quota UG seats and other central/institutional categories.

### Required Data

For each year from 2020 to 2025:

1. MCC seat matrix by round:
   - Round 1
   - Round 2
   - Mop-up
   - Stray vacancy
2. College/institute list.
3. Course:
   - MBBS
   - BDS
4. Seat type:
   - AIQ government
   - AIIMS
   - JIPMER
   - Central university
   - Deemed university
   - ESIC
   - AFMC, if applicable
5. Category-wise seat counts:
   - UR
   - OBC-NCL
   - SC
   - ST
   - EWS
   - PwD subcategories
6. Round-wise allotment result.
7. Round-wise opening and closing rank.
8. Candidate category and allotted category.
9. Fees, where available.
10. Seat withdrawal/addition notices.
11. Conversion rules after each round.

### Output Use

This data supports predictions like:

- “At AIR 18,000, OBC-NCL, you are Safe/Likely/Borderline for these AIQ government colleges based on previous closing ranks.”
- “Deemed university options are available but fee range is high.”

---

## 7. Karnataka Counselling Data Required

### Authority

KEA conducts Karnataka medical/dental/AYUSH seat allotment based on NEET score and the Karnataka government seat matrix.

### Required Karnataka Data

For each year from 2020 to 2025:

1. KEA medical seat matrix.
2. KEA dental seat matrix.
3. Government college list.
4. Private college list.
5. Government quota seats in private colleges.
6. Private open seats.
7. Management quota seats.
8. NRI quota seats.
9. Minority quota seats.
10. Category-wise seat matrix:
    - GM
    - 1G
    - 2AG / 2BG / 3AG / 3BG
    - SCG / STG
    - GMR / GMK / rural / Kannada / Hyderabad-Karnataka variations
11. Round-wise allotment lists:
    - Round 1
    - Round 2
    - Mop-up / Round 3
    - Stray vacancy, if available
12. Round-wise closing rank by:
    - College
    - Course
    - Category
    - Seat type
    - Fee type
13. Fee data by seat type.
14. Candidate eligibility rules.
15. Domicile/study certificate rules.
16. Caste/category certificate rules.
17. Rural/Kannada/HK eligibility rules.
18. Seat addition/removal notices.
19. Post-allotment status:
    - Allotted
    - Reported
    - Not reported
    - Cancelled
    - Converted
    - Vacant

### Karnataka-Specific Important Fields

The Karnataka model must not only use AIR. It must map AIR to KEA category and seat type. The same AIR can produce very different outcomes depending on whether the student is eligible for GM, 2A, 3B, SCG, STG, GMR, GMK, private open, NRI, or management seats.

---

## 8. College Master Database

Create one normalized master table for all colleges.

### Fields

1. College code.
2. College name.
3. State.
4. District/city.
5. Ownership:
   - Government
   - Private
   - Deemed
   - Central
   - AIIMS/JIPMER
6. Counselling authority:
   - MCC
   - KEA
7. Course:
   - MBBS
   - BDS
8. Annual intake.
9. Seat type distribution.
10. Fee by seat type.
11. Bond/service obligation.
12. Minority status.
13. College website.
14. NMC approval status.
15. Last updated date.

### Primary Source

Use NMC college/course search and official seat matrix documents for seat validation.

---

## 9. Prediction Engine Design

The system should have three layers.

---

### Layer 1: Marks to AIR Prediction

Input:

- NEET marks.
- Exam year, if known.
- Category, optional for qualifying cutoff only.

Output:

- Predicted AIR range.
- Confidence interval.
- Percentile estimate.
- Category qualification status.

Recommended approach:

1. Build marks-to-rank curves for 2020–2025.
2. Use interpolation between known marks/rank points.
3. Fit monotonic regression or isotonic regression.
4. Add uncertainty bands using year-wise variance.
5. Use latest year trend adjustment.

Prediction format:

- Expected AIR: 18,000–22,000.
- Conservative AIR: 24,000.
- Optimistic AIR: 16,500.

Do not output only one exact rank.

---

### Layer 2: College Eligibility Filter

Input:

- AIR or predicted AIR range.
- Home state.
- Domicile.
- Category.
- Karnataka category.
- Quota eligibility.
- Course preference.
- Budget.

Filter logic:

1. Is the student eligible for MCC AIQ?
2. Is the student eligible for Karnataka state counselling?
3. Which KEA categories apply?
4. Which seat types are financially allowed?
5. Which colleges/courses are eligible?
6. Which rounds should be considered?

Output:

- Eligible counselling paths.
- Ineligible paths with reason.

Example:

- Eligible: MCC AIQ MBBS/BDS.
- Eligible: KEA Karnataka government quota, if domicile verified.
- Not eligible: Karnataka rural quota, if no rural certificate.
- Not eligible: NRI quota, if not selected.

---

### Layer 3: College Chance Prediction

Input:

- AIR range.
- Category.
- Quota.
- Seat type.
- Historical closing ranks.

Output:

Each college receives a chance label:

1. Safe: candidate rank is comfortably better than historical closing rank.
2. Likely: rank is near but better than closing trend.
3. Borderline: rank is within fluctuation range.
4. Unlikely: rank is worse than previous closing rank.
5. Not eligible: quota/category mismatch.

Recommended rule:

- Safe: candidate rank is at least 15–25% better than historical closing rank.
- Likely: candidate rank is 0–15% better.
- Borderline: candidate rank is 0–15% worse but within historical fluctuation.
- Unlikely: candidate rank is more than 15–25% worse.

These thresholds should be calibrated separately for:

- AIQ government colleges.
- Karnataka government colleges.
- Karnataka private government quota seats.
- Private open seats.
- Management/NRI seats.

---

## 10. Database Schema

### Table: `exam_year_stats`

Fields:

- year
- registered_count
- appeared_count
- qualified_count
- topper_score
- cutoff_ur
- cutoff_obc
- cutoff_sc
- cutoff_st
- cutoff_ews
- source_url

### Table: `marks_rank_curve`

Fields:

- year
- marks_min
- marks_max
- rank_min
- rank_max
- percentile_min
- percentile_max
- source_url

### Table: `college_master`

Fields:

- college_id
- college_code
- college_name
- state
- district
- ownership_type
- counselling_authority
- course
- annual_intake
- nmc_status
- source_url

### Table: `seat_matrix`

Fields:

- year
- counselling_authority
- round
- college_id
- course
- quota
- category
- seat_type
- seats_available
- fee
- source_url

### Table: `allotment_results`

Fields:

- year
- counselling_authority
- round
- air
- college_id
- course
- allotted_category
- candidate_category
- seat_type
- fee
- status
- source_url

### Table: `closing_rank_summary`

Fields:

- year
- counselling_authority
- round
- college_id
- course
- quota
- category
- seat_type
- opening_rank
- closing_rank
- seats_filled
- source_url

### Table: `rules_master`

Fields:

- rule_id
- authority
- year
- rule_type
- rule_text
- applies_to
- source_url

---

## 11. Data Collection Pipeline

### Step 1: Collect Official Sources

Sources:

1. NTA NEET result press releases.
2. MCC UG counselling portal.
3. MCC seat matrix PDFs.
4. MCC allotment result PDFs.
5. KEA UGNEET portal.
6. KEA seat matrix PDFs.
7. KEA allotment PDFs.
8. KEA cutoff rank PDFs.
9. NMC college/course data.
10. Government fee orders and counselling bulletins.

### Step 2: Convert PDFs to Tables

Use:

- Tabula / Camelot for table PDFs.
- OCR only when PDFs are scanned.
- Manual validation for broken tables.

### Step 3: Normalize Names and Codes

Normalize:

- College code.
- College name.
- Course name.
- Category code.
- Quota name.
- Seat type.
- Round name.

### Step 4: Build Cutoff Tables

For every combination:

- Year
- Round
- College
- Course
- Category
- Quota
- Seat type

Compute:

- Opening rank.
- Closing rank.
- Number of seats allotted.
- Last reported rank.

### Step 5: Validate Data

Validation checks:

1. Seat counts in allotment should not exceed seat matrix.
2. Closing rank should be worse than or equal to opening rank.
3. College code must exist in master table.
4. Category code must exist in category mapping.
5. Round sequence must be valid.
6. Fee should match seat type.
7. If a seat was added/withdrawn, it must be traced to an official notice.

---

## 12. Model Evaluation Plan

Use 2020–2024 as training/backtesting and 2025 as final validation.

### Rank Prediction Metrics

1. Mean absolute rank error.
2. Error by marks band:
   - 650+
   - 600–650
   - 550–600
   - 500–550
   - 450–500
   - Below 450
3. Coverage of confidence interval.
4. Category-wise qualification accuracy.

### College Prediction Metrics

For 2025:

1. Whether actual allotted college appears in predicted list.
2. Top-10 recall.
3. Top-25 recall.
4. Safe/Likely/Borderline calibration.
5. False-safe rate: predicted Safe but student did not get seat.
6. False-negative rate: predicted Unlikely but student got seat.
7. Round-wise accuracy.
8. Category-wise accuracy.
9. Government/private/deemed accuracy separately.

### Most Important Metric

False-safe rate must be very low. It is better to say “Borderline” than to falsely promise “Safe.”

---

## 13. Prediction Output Format

For a student, output should be structured like this:

```json
{
  "student_profile": {
    "marks": 625,
    "predicted_air_range": "15000-19000",
    "home_state": "Karnataka",
    "category": "OBC-NCL",
    "karnataka_category": "2AG",
    "course_preference": "MBBS"
  },
  "rank_prediction": {
    "expected_air": 17000,
    "optimistic_air": 15000,
    "conservative_air": 19000,
    "confidence": "medium"
  },
  "counselling_paths": [
    {
      "authority": "MCC",
      "quota": "AIQ",
      "eligible": true
    },
    {
      "authority": "KEA",
      "quota": "Karnataka State Quota",
      "eligible": true
    }
  ],
  "college_predictions": [
    {
      "college": "Example Medical College",
      "course": "MBBS",
      "authority": "KEA",
      "seat_type": "Government quota",
      "category": "2AG",
      "last_year_closing_rank": 18500,
      "chance": "Likely",
      "reason": "Predicted rank is within previous closing rank trend for this category and seat type."
    }
  ],
  "warnings": [
    "Prediction is based on previous-year cutoffs and does not guarantee allotment.",
    "KEA category eligibility must be verified through official documents."
  ]
}
```

---

## 14. User-Facing Explanation Template

The app should explain results in simple language:

“Based on your marks and category, your expected AIR is around X–Y. Under MCC AIQ, your chances for top government colleges are unlikely/limited, but you may have options in BDS/deemed/private depending on budget. Under Karnataka KEA, because you are eligible for [category], these colleges fall into Safe/Likely/Borderline zones based on 2020–2024 closing rank trends and 2025 validation.”

---

## 15. Risk Handling

### Risks

1. Official data PDFs may be inconsistent or scanned.
2. Category codes differ between MCC and KEA.
3. Seat matrices change during counselling.
4. Colleges add/remove seats mid-process.
5. Candidate behavior changes by year.
6. Fee structures change.
7. Karnataka domicile/category rules are complex.
8. Marks-to-rank shifts significantly with paper difficulty.

### Mitigation

1. Store source URL for every data row.
2. Keep year-specific rules.
3. Keep round-specific seat matrices.
4. Use confidence bands, not deterministic outputs.
5. Validate 2025 separately before public launch.
6. Add “last updated” timestamp to every prediction.
7. Display source-based explanation for each college prediction.

---

## 16. Implementation Roadmap

### Week 1: Data Foundation

1. Collect 2020–2025 NTA result data.
2. Collect 2020–2025 MCC seat matrix and allotment PDFs.
3. Collect 2020–2025 KEA seat matrix, cutoff, and allotment PDFs.
4. Create college master database.
5. Define category mapping for MCC and KEA.

### Week 2: Data Extraction and Cleaning

1. Extract PDF tables.
2. Normalize college names and codes.
3. Normalize category and quota codes.
4. Build round-wise closing rank tables.
5. Validate seat counts.

### Week 3: Rank Prediction Engine

1. Build marks-to-rank curves.
2. Build interpolation model.
3. Add uncertainty bands.
4. Backtest 2020–2024.
5. Validate on 2025.

### Week 4: College Prediction Engine

1. Build eligibility filter.
2. Build AIQ prediction engine.
3. Build Karnataka prediction engine.
4. Add Safe/Likely/Borderline/Unlikely labels.
5. Test with 2025 actual allotments.

### Week 5: App Prototype

1. Build Streamlit frontend.
2. Add student input form.
3. Add rank prediction panel.
4. Add AIQ college prediction panel.
5. Add Karnataka college prediction panel.
6. Add explanation and source references.

### Week 6: Validation and Launch Readiness

1. Test with 100–500 historical candidates if available.
2. Compare predictions against 2025 allotments.
3. Tune confidence thresholds.
4. Add disclaimers.
5. Prepare demo and documentation.

---

## 17. MVP Features

### Must Have

1. Marks to AIR prediction.
2. AIR-based college prediction.
3. MCC AIQ support.
4. Karnataka KEA support.
5. Category and quota filtering.
6. Round-wise previous cutoff display.
7. Safe/Likely/Borderline/Unlikely labels.
8. Source-backed explanation.
9. Budget filter.
10. Export result as PDF.

### Should Have

1. Option filling recommendation.
2. College comparison.
3. Fee comparison.
4. Round-wise strategy.
5. Backup BDS/AYUSH recommendation.

### Later

1. Other states.
2. AI chatbot counselling assistant.
3. Parent/student dashboard.
4. Preference optimizer.
5. Live counselling update tracker.
6. WhatsApp report generation.

---

## 18. Final Recommendation

Start with 2020–2024 data and validate on 2025. This is a strong MVP strategy.

For the first release, do not try to cover all India state counselling. Build a high-quality system for:

1. AIR prediction from marks.
2. MCC All India Quota prediction.
3. Karnataka KEA prediction.

The core strength of the system should be explainability. Every college prediction must show:

- Previous-year closing rank.
- Year and round.
- Category.
- Quota.
- Seat type.
- Fee type.
- Confidence label.
- Source document.

This makes the tool trustworthy and useful for real students and parents.

---

## 19. Official Source Checklist

Use these as the first official sources:

1. NTA NEET UG result press releases and score/rank data.
2. MCC UG Medical Counselling portal.
3. MCC seat matrix and allotment result PDFs.
4. KEA UGNEET portal.
5. KEA Karnataka seat matrix PDFs.
6. KEA Karnataka cutoff rank PDFs.
7. KEA Karnataka round-wise allotment PDFs.
8. NMC college and course search.
9. Karnataka government fee and admission orders.

---

## 20. Disclaimer Text for App

“This prediction is based on previous-year official counselling data, seat matrices, category rules, and rank trends. It is not an admission guarantee. Actual allotment depends on official counselling rules, seat availability, category verification, candidate preferences, fee payment, document verification, and yearly competition.”
