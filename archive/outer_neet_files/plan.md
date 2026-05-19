**Module 1: NEET Marks → AIR Prediction**, because college prediction is a separate module that will use AIR later.

Below is the full plan you can share.

---

# NEET Marks-to-Rank Prediction Module: Full Plan for Claude/Codex

## 1. Goal of this module

Build a system that predicts a student’s **approximate NEET All India Rank range** from their **marks out of 720**.

The system should not predict one exact rank. It should output:

```text
Input marks: 620 / 720

Estimated AIR range: 22,000 – 32,000
Median estimate: 27,000
Best-case estimate: 22,000
Conservative estimate: 32,000
Confidence: Medium
```

Reason: NEET rank depends on yearly score distribution, paper difficulty, number of candidates, tie-breaking rules, and score clustering. So exact rank from marks alone is not safe.

---

# 2. How this fits into the full product

The full app has two layers:

```text
Layer 1: Marks → estimated AIR range
Layer 2: AIR + category + quota + counselling rules → college prediction
```

For now, Claude/Codex should focus on **Layer 1 only**.

Later, Layer 2 will use:

```text
AIR
National category
Home state
Karnataka domicile
Karnataka category
MCC/KEA cutoff history
Quota and seat type
```

NTA itself states that it provides **All India Rank** to candidates and admitting authorities draw merit lists based on AIR. State authorities then prepare their own merit lists according to state category and domicile rules. ([S3WaaS][1])

---

# 3. Data needed for marks-to-rank prediction

## A. Year-wise marks-vs-AIR anchor points

This is the most important dataset.

We need rows like:

| Year | Marks |                    AIR / Rank range | Source                   |
| ---: | ----: | ----------------------------------: | ------------------------ |
| 2025 |   686 |                                   1 | NTA / result data        |
| 2025 |   662 |                                  33 | NTA / result data        |
| 2025 |   625 |                                 158 | NTA / result data        |
| 2024 |   720 | 1–17 or 1–67 depending revised data | NTA / secondary verified |
| 2024 |   700 |                        around 2,250 | secondary verified       |
| 2024 |   650 |                       around 29,000 | secondary verified       |

For 2025, public summaries based on NTA data show anchor points such as 686 → AIR 1, 662 → AIR 33, 625 → AIR 158, 607 → AIR 1022, 600 → AIR 1386, 543 → AIR 15000, and so on. These are useful validation anchors but should be stored with source provenance. ([S3WaaS][1])

### Why this is needed

The model needs historical curves:

```text
marks → approximate rank
```

Without marks-rank anchor points, we cannot build a rank estimator.

---

## B. Total appeared candidates per year

We need this because rank distribution changes when candidate count changes.

Example:

```text
2020 appeared candidates
2021 appeared candidates
2022 appeared candidates
2023 appeared candidates
2024 appeared candidates
2025 appeared candidates
```

The NTA result press releases provide registered and appeared candidate counts across years. For 2024, NTA’s press release includes candidate counts from 2019–2024 and says more than 24 lakh candidates registered, with more than 23 lakh present. ([S3WaaS][1])

### Why this is needed

A score of 600 in one year may not map to the same rank in another year because:

```text
candidate count changes
paper difficulty changes
score inflation changes
top-score clustering changes
```

---

## C. Highest score and topper distribution

We need:

```text
highest score
number of students at highest score
number of students sharing AIR 1
top 10 / top 100 score distribution if available
```

For example, NEET 2024 had an unusual top-rank distribution, with many candidates sharing AIR 1. This kind of year must be handled carefully because it can distort the top-end marks-to-rank curve. ([S3WaaS][1])

### Why this is needed

If many students score 720, then:

```text
720 marks does not map to only rank 1
```

It may map to:

```text
rank 1–17
rank 1–67
or another range depending on final/revised result
```

So the estimator must support **rank ranges**, not only single rank values.

---

## D. Percentile and qualifying score ranges

Need yearly category-wise qualifying percentile and cutoff marks:

```text
UR / EWS: 50th percentile, score range
OBC: 40th percentile, score range
SC: 40th percentile, score range
ST: 40th percentile, score range
PwD categories
```

For NEET 2025, public NTA-based summaries show General 50th percentile cutoff range as 686–144 and SC/OBC/ST 40th percentile as 143–113. ([S3WaaS][1])

### Why this is needed

Percentile/cutoff data gives us distribution anchors at the lower end. It helps avoid unrealistic predictions for low scores.

---

## E. Tie-breaking rules

Need yearly rules for resolving same marks.

Typical tie-breaking fields include:

```text
Biology marks
Chemistry marks
Physics marks
incorrect-answer ratio
subject-wise incorrect-answer ratio
application number / random process, depending year
```

This is important because many students can have the same total marks.

### Important design point

For our rank predictor, if the user enters only total marks, we cannot apply tie-breaking exactly.

So output should say:

```text
Exact rank cannot be predicted from total marks alone because tie-breaking depends on subject scores and other criteria.
```

Optional future improvement:

Ask user for:

```text
Biology marks
Chemistry marks
Physics marks
incorrect attempts
```

But for MVP, keep only total marks.

---

## F. Source provenance for every data point

Every row must store:

```text
source_type
source_name
source_url
source_file
source_year
confidence_level
extraction_method
date_accessed
notes
```

Source types:

```text
OFFICIAL_NTA_PDF
OFFICIAL_NTA_NOTICE
OFFICIAL_COUNSELLING_LIST
VERIFIED_STUDENT_SCORECARD
SECONDARY_EDU_PORTAL
MANUAL_ENTRY
```

Confidence levels:

```text
high = official NTA or official counselling source
medium = credible education portal citing NTA
low = unverified web table / manually entered
```

---

# 4. Best sources and where to get data

## Priority 1: Official NTA NEET result notices

Use for:

```text
candidate count
result declaration
AIR usage
tie-breaking rules
category-wise cutoff
official score/rank data if present
```

NTA’s official NEET result notice is the highest-trust source. It confirms that NTA declares NEET scores/ranks and that AIR is used by admitting authorities. ([S3WaaS][1])

Collect for:

```text
NEET UG 2020 result notice
NEET UG 2021 result notice
NEET UG 2022 result notice
NEET UG 2023 result notice
NEET UG 2024 result notice
NEET UG 2025 result notice
```

Search terms:

```text
site:nta.ac.in NEET UG 2024 result scores rank PDF
site:exams.nta.ac.in/NEET NEET UG 2024 result rank PDF
site:nta.ac.in NEET UG 2023 result scores rank PDF
site:nta.ac.in NEET UG 2022 result scores rank PDF
site:nta.ac.in NEET UG 2021 result scores rank PDF
site:nta.ac.in NEET UG 2020 result scores rank PDF
```

---

## Priority 2: Official NTA score/rank PDF or result statistics PDF

Use for:

```text
marks-to-rank anchor points
topper data
percentile data
score range by category
appeared/qualified counts
```

This is the best source if it provides marks-rank anchors.

---

## Priority 3: Verified student scorecards

Use for:

```text
marks + AIR pairs
```

This can become a powerful private dataset.

But privacy is important. Store only:

```text
year
marks
AIR
optional category
optional state
source_confidence
```

Do not store:

```text
student name
roll number
application number
phone number
scorecard image
date of birth
```

Suggested collection form:

```text
Year of NEET
Marks out of 720
All India Rank
Category, optional
State, optional
Consent checkbox
```

---

## Priority 4: Secondary education portals

Use only as gap-filling data.

Examples:

```text
Physics Wallah
Careers360
Aakash
Shiksha
Collegedunia
```

These can provide marks-rank tables, but they should not be treated equal to official NTA data.

Use them with:

```text
source_type = SECONDARY_EDU_PORTAL
confidence_level = medium
```

---

## Priority 5: Counselling data

MCC and KEA data are mainly for college prediction, not marks-to-rank.

MCC allotment PDFs contain rank, quota, institute, course, allotted category, and candidate category. This is excellent for college prediction. ([S3WaaS][2])

KEA allotment PDFs contain All India Rank, course code, college name, course name, allotted category, course fee, and status. This is also excellent for Karnataka college prediction. ([CET Online][3])

But counselling data usually does **not** include marks. So it is useful for marks-to-rank only if the list contains both:

```text
marks + AIR
```

---

# 5. Recommended database schema for marks-to-rank module

## Table 1: exam_years

```sql
exam_year_id INTEGER PRIMARY KEY
year INTEGER UNIQUE
exam_name TEXT
max_marks INTEGER DEFAULT 720
registered_candidates INTEGER
appeared_candidates INTEGER
qualified_candidates INTEGER
result_date DATE
official_notice_url TEXT
notes TEXT
created_at TIMESTAMP
updated_at TIMESTAMP
```

---

## Table 2: marks_rank_points

```sql
point_id INTEGER PRIMARY KEY
year INTEGER
marks_min INTEGER
marks_max INTEGER
rank_min INTEGER
rank_max INTEGER
rank_median INTEGER
percentile_min REAL
percentile_max REAL
data_granularity TEXT
source_id INTEGER
confidence_level TEXT
notes TEXT
created_at TIMESTAMP
updated_at TIMESTAMP
```

### Example rows

```text
year: 2025
marks_min: 686
marks_max: 686
rank_min: 1
rank_max: 1
source_type: OFFICIAL_NTA_PDF
confidence_level: high
```

```text
year: 2025
marks_min: 635
marks_max: 630
rank_min: 170
rank_max: 250
source_type: SECONDARY_EDU_PORTAL
confidence_level: medium
```

---

## Table 3: category_cutoff_stats

```sql
cutoff_id INTEGER PRIMARY KEY
year INTEGER
category TEXT
qualifying_percentile TEXT
score_min INTEGER
score_max INTEGER
qualified_count INTEGER
source_id INTEGER
confidence_level TEXT
notes TEXT
```

---

## Table 4: topper_stats

```sql
topper_stat_id INTEGER PRIMARY KEY
year INTEGER
highest_marks INTEGER
number_at_highest_marks INTEGER
air_1_count INTEGER
top_10_score_min INTEGER
top_100_score_min INTEGER
source_id INTEGER
confidence_level TEXT
notes TEXT
```

---

## Table 5: tie_breaking_rules

```sql
rule_id INTEGER PRIMARY KEY
year INTEGER
priority_order INTEGER
criterion_code TEXT
criterion_description TEXT
source_id INTEGER
notes TEXT
```

Example:

```text
1 Biology score
2 Chemistry score
3 Physics score
4 lower incorrect-answer ratio
5 application number / random method, depending official rule
```

---

## Table 6: data_sources

```sql
source_id INTEGER PRIMARY KEY
source_type TEXT
source_name TEXT
source_url TEXT
source_file_path TEXT
publisher TEXT
published_date DATE
accessed_date DATE
confidence_level TEXT
notes TEXT
```

---

# 6. CSV templates needed

Ask Codex to create these CSV templates:

```text
data/raw/official/nta_result_notices/
data/raw/secondary/marks_rank_tables/
data/raw/verified_scorecards/
data/processed/
data/templates/
```

Templates:

```text
exam_years_template.csv
marks_rank_points_template.csv
category_cutoff_stats_template.csv
topper_stats_template.csv
tie_breaking_rules_template.csv
data_sources_template.csv
```

Example `marks_rank_points_template.csv`:

```csv
year,marks_min,marks_max,rank_min,rank_max,rank_median,percentile_min,percentile_max,data_granularity,source_type,source_name,source_url,confidence_level,notes
2025,686,686,1,1,1,,,exact,OFFICIAL_NTA_PDF,NTA NEET UG 2025 Result PDF,URL,high,official anchor point
2025,635,630,170,250,210,,,range,SECONDARY_EDU_PORTAL,Careers360/PW,URL,medium,secondary marks-rank range
```

---

# 7. Prediction algorithm

## Step 1: Load year-wise marks-rank points

Load all points from 2020–2024.

Use 2025 only for validation/backtesting.

---

## Step 2: Normalize all data into ranges

Convert every row into:

```text
marks_min
marks_max
rank_min
rank_max
```

If source gives exact value:

```text
marks_min = marks_max
rank_min = rank_max
```

If source gives range:

```text
marks_min = upper score
marks_max = lower score
rank_min = best rank
rank_max = worst rank
```

Example:

```text
635–630 marks → AIR 170–250
```

---

## Step 3: Build yearly interpolation curves

For each year:

```text
marks → rank_min
marks → rank_max
marks → rank_median
```

Recommended first method:

```text
piecewise linear interpolation
```

Do not start with heavy ML.

---

## Step 4: Enforce monotonicity

Higher marks must always predict better rank.

Example:

```text
650 marks cannot have worse rank than 640 marks
```

Use:

```text
monotonic interpolation
or isotonic regression
```

---

## Step 5: Weight years

Recommended initial weights:

| Year | Weight |
| ---: | -----: |
| 2024 |   0.40 |
| 2023 |   0.25 |
| 2022 |   0.18 |
| 2021 |   0.10 |
| 2020 |   0.07 |

Later, make this configurable.

Reason: Recent years reflect current competition better.

---

## Step 6: Output rank range

For given marks:

```text
best_case_rank = weighted lower-bound rank
median_rank = weighted median rank
conservative_rank = weighted upper-bound rank
```

Output:

```json
{
  "marks": 620,
  "estimated_air_best": 22000,
  "estimated_air_median": 27000,
  "estimated_air_conservative": 32000,
  "confidence": "medium",
  "method": "weighted_monotonic_interpolation",
  "training_years": [2020, 2021, 2022, 2023, 2024],
  "validation_year": 2025
}
```

---

# 8. Confidence scoring

Confidence should depend on:

```text
distance from nearest anchor points
number of years with data around that mark
source quality
whether score lies in dense or sparse region
agreement/disagreement across years
```

Initial rule:

```text
High confidence:
- multiple years have nearby points
- official/verified data available
- low variance across years

Medium confidence:
- some secondary data used
- moderate variance

Low confidence:
- sparse data
- extrapolation
- low-score region
- only secondary data
```

---

# 9. Validation using 2025

Train on:

```text
2020, 2021, 2022, 2023, 2024
```

Validate on:

```text
2025
```

Backtesting tasks:

```text
For each 2025 marks-rank anchor:
    predict rank range using 2020–2024
    check if actual 2025 rank lies inside predicted range
```

Metrics:

```text
coverage_rate
median_absolute_rank_error
mean_absolute_rank_error
within_10_percent_rank_band
within_20_percent_rank_band
overconfidence_rate
conservative_error_rate
```

Most important metric:

```text
coverage_rate
```

Because we are predicting ranges, the actual 2025 rank should fall inside or near the predicted range.

---

# 10. Repository setup needed

Recommended folder structure:

```text
neet-rank-predictor/
│
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── data/
│   ├── raw/
│   │   ├── official/
│   │   │   └── nta_result_notices/
│   │   ├── secondary/
│   │   │   └── marks_rank_tables/
│   │   └── verified_scorecards/
│   │
│   ├── templates/
│   │   ├── exam_years_template.csv
│   │   ├── marks_rank_points_template.csv
│   │   ├── category_cutoff_stats_template.csv
│   │   ├── topper_stats_template.csv
│   │   ├── tie_breaking_rules_template.csv
│   │   └── data_sources_template.csv
│   │
│   ├── processed/
│   │   ├── exam_years.csv
│   │   ├── marks_rank_points.csv
│   │   ├── category_cutoff_stats.csv
│   │   ├── topper_stats.csv
│   │   ├── tie_breaking_rules.csv
│   │   └── data_sources.csv
│   │
│   └── validation/
│       └── neet_2025_validation_points.csv
│
├── notebooks/
│   ├── 01_data_audit.py
│   ├── 02_marks_rank_curve.py
│   └── 03_2025_backtest.py
│
├── src/
│   └── neet_rank_predictor/
│       ├── __init__.py
│       ├── config.py
│       │
│       ├── data/
│       │   ├── loaders.py
│       │   ├── validators.py
│       │   ├── normalizers.py
│       │   └── source_registry.py
│       │
│       ├── models/
│       │   ├── interpolation.py
│       │   ├── isotonic_model.py
│       │   ├── ensemble.py
│       │   └── confidence.py
│       │
│       ├── prediction/
│       │   ├── rank_estimator.py
│       │   ├── explanation.py
│       │   └── response_schema.py
│       │
│       ├── validation/
│       │   ├── backtest_2025.py
│       │   └── metrics.py
│       │
│       └── ui/
│           └── streamlit_app.py
│
├── tests/
│   ├── test_data_validation.py
│   ├── test_monotonicity.py
│   ├── test_interpolation.py
│   ├── test_confidence.py
│   ├── test_prediction_schema.py
│   └── test_backtest.py
│
└── docs/
    ├── DATA_SOURCES.md
    ├── METHODOLOGY.md
    ├── LIMITATIONS.md
    ├── VALIDATION.md
    └── USER_GUIDE.md
```

---

# 11. MVP implementation phases

## Phase 1: Data templates and mock data

Codex should create:

```text
CSV templates
small mock dataset
data validation rules
source provenance table
```

No prediction yet.

---

## Phase 2: Data loader and validator

Implement:

```text
load_marks_rank_points()
load_exam_years()
load_sources()
validate_required_columns()
validate_marks_range_0_to_720()
validate_rank_positive()
validate_monotonicity_per_year()
validate_source_provenance()
```

---

## Phase 3: Simple interpolation model

Implement:

```text
YearlyRankCurve
WeightedRankEstimator
predict_rank_range(marks)
```

Input:

```text
marks = 620
```

Output:

```text
best_rank
median_rank
conservative_rank
confidence
```

---

## Phase 4: Confidence module

Implement:

```text
source_quality_score
anchor_density_score
year_agreement_score
extrapolation_penalty
final_confidence_label
```

---

## Phase 5: 2025 backtesting

Implement:

```text
backtest_on_2025()
calculate_coverage_rate()
calculate_rank_error()
generate_validation_report()
```

---

## Phase 6: Streamlit UI

Simple UI:

```text
Enter NEET marks
Optional: actual AIR
Show estimated AIR range
Show confidence
Show explanation
Show nearest historical data points
```

Important UI logic:

```text
If actual AIR is provided:
    say: "Use actual AIR for college prediction."
If actual AIR is not provided:
    say: "Use conservative estimated AIR for college prediction."
```

---

## Phase 7: Documentation

Create:

```text
README.md
DATA_SOURCES.md
METHODOLOGY.md
LIMITATIONS.md
VALIDATION.md
```

---

# 12. What Claude should review before Codex codes

Ask Claude to check:

```text
Is the module separated correctly from college prediction?
Is the data schema complete?
Are source provenance fields enough?
Is the prediction method too simple or good for MVP?
Is 2020–2024 enough for training?
Is 2025 validation correctly isolated?
What edge cases are missing?
What risks exist with secondary education portal data?
```

---

# 13. Prompt for Claude Opus

Paste this into Claude with the plan above.

```markdown
You are a senior AI product architect, data engineer, and educational-admissions analytics expert.

I am building a NEET UG Marks-to-AIR prediction module.

This is Module 1 of a larger NEET college predictor.

The full product has two layers:

1. Marks → estimated All India Rank range.
2. AIR + category + quota + state rules → college prediction.

For now, review only Module 1.

The goal is to estimate approximate NEET All India Rank from marks out of 720.

The system must output a rank range, not exact rank.

Example output:

Marks: 620 / 720
Estimated AIR range: 22,000–32,000
Median estimate: 27,000
Confidence: Medium

Training years:
2020–2024

Validation year:
2025

Data needed:
1. Year-wise NEET marks-vs-AIR anchor points.
2. Total appeared candidates per year.
3. Highest score/topper distribution.
4. Percentile/score statistics.
5. Tie-breaking rules.
6. Source provenance for every data point.

Data sources:
1. Official NTA NEET result notices.
2. Official NTA result/rank PDFs.
3. Verified anonymized scorecards.
4. Secondary education portals only for gap-filling.
5. Counselling data only if it contains both score and AIR.

Recommended method:
- Start with transparent monotonic interpolation.
- Use weighted historical years.
- Give recent years higher weight.
- Use 2025 only for validation.
- Output best-case, median, and conservative rank estimates.
- Include confidence scoring.

Please review this module deeply.

Your tasks:

1. Identify missing assumptions.
2. Improve the data schema.
3. Improve the source-provenance strategy.
4. Suggest a robust but simple marks-to-rank algorithm.
5. Define confidence scoring.
6. Define 2025 validation methodology.
7. Identify risks with secondary data.
8. Suggest exact CSV templates.
9. Suggest test cases.
10. Produce a final Codex-ready implementation specification.

Do not code yet.
Be critical.
Do not overbuild.
Keep the MVP practical.
```

---

# 14. Prompt for Codex after Claude review

Use this after Claude gives the final architecture.

```markdown
You are a senior Python engineer and data engineer.

Build Module 1 of a NEET UG rank prediction system:

NEET marks out of 720 → estimated All India Rank range.

Do not build college prediction yet.

Use this scope:

Training data:
2020–2024 marks-rank anchor points.

Validation data:
2025 marks-rank anchor points.

Core output:
- best-case estimated AIR
- median estimated AIR
- conservative estimated AIR
- confidence label
- explanation
- source references used

Build the repository with:

1. Data templates.
2. Mock data.
3. Source provenance table.
4. Data validators.
5. Monotonic interpolation model.
6. Weighted multi-year estimator.
7. Confidence scoring.
8. 2025 backtesting script.
9. Streamlit UI.
10. Unit tests.
11. Documentation.

Do not hallucinate official data.
Use mock/sample CSVs where official data is not provided.
Every data point must have source provenance.

Folder structure:

neet-rank-predictor/
├── data/
├── notebooks/
├── src/
├── tests/
└── docs/

Important implementation rules:

1. Marks must be between 0 and 720.
2. AIR must be positive.
3. Higher marks must never produce worse rank.
4. If actual AIR is provided, use actual AIR later for college prediction.
5. If actual AIR is not provided, use conservative estimated AIR for downstream college prediction.
6. 2025 data must not be used for fitting.
7. Output rank range, not exact rank.
8. All predictions must include confidence and explanation.

Start by implementing:
- CSV templates
- sample data
- data loader
- validators
- rank estimator
- tests
- simple Streamlit app
```

---

# 15. Final decision

For the marks-to-rank module, tell Claude/Codex this:

```text
We are not trying to predict exact rank.
We are estimating AIR range from marks.
We will train/calibrate on 2020–2024.
We will validate on 2025.
Official NTA data has highest priority.
Secondary portals are allowed only as medium-confidence gap-filling sources.
Every data point must carry provenance.
The prediction method should be transparent, monotonic, and conservative.
```

That is the cleanest and safest plan before moving to the college prediction module.

[1]: https://cdnbbsr.s3waas.gov.in/s37bc1ec1d9c3426357e69acd5bf320061/uploads/2025/06/2025061472.pdf?utm_source=chatgpt.com "NEET (UG) - 2025"
[2]: https://cdnbbsr.s3waas.gov.in/s3e0f7a4d0ef9b84b83b693bbf3feb8e6e/uploads/2024/08/2024082536.pdf?utm_source=chatgpt.com "NEET-UG Counselling Seats Allotment -2024 Round 1"
[3]: https://cetonline.karnataka.gov.in/keawebentry456/ugneet24/UGNEET_ALLOT_2024_MEDICAL_R2_provkannada.pdf?utm_source=chatgpt.com "UGNEET -2024 2nd ROUND SEAT ALLOTMENT LIST [18- ..."
