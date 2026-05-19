# NEET UG Predictor

A data-driven NEET UG rank estimator and college predictor using historical counselling data (2020–2025).

**Status**: MVP — Rank estimator and college predictor operational. No UI yet.

## What It Does

1. **Marks → AIR Estimator** — Given NEET marks and target year, predicts an AIR range (best/conservative) using weighted percentile interpolation across 5 training years with paper-difficulty normalization.
2. **AIR → College Predictor** — Given an AIR and category, predicts college eligibility across MCC AIQ and Karnataka KEA counselling with Safe/Moderate/Risky classification.

## Project Structure

```
neet-predictor/
├── src/neet_predictor/          # Core library
│   ├── config.py                # Year weights, paths, constants
│   ├── rank/                    # Marks-to-AIR estimation
│   │   ├── estimator.py         # RankEstimator, validation, comparison
│   │   └── calibration.py       # Paper-difficulty normalization strategies
│   ├── college/                 # AIR-to-college prediction
│   │   ├── predictor.py         # College prediction engine
│   │   ├── eligibility.py       # Candidate profiles & category logic
│   │   └── explainer.py         # Human-readable result formatting
│   ├── data/                    # Data loading, validation, normalization
│   │   ├── loader.py
│   │   ├── normalizer.py
│   │   └── validator.py
│   └── ui/                      # (placeholder — not yet built)
│
├── tests/                       # 225 tests (pytest)
│   ├── test_rank_estimator.py   # 47 tests — rank estimation
│   ├── test_rank_calibration.py # 52 tests — normalization & acceptance
│   ├── test_predictor.py        # College predictor tests
│   ├── test_loader.py           # Data loader tests
│   ├── test_normalizer.py       # Normalizer tests
│   ├── test_schema.py           # Schema validation tests
│   └── test_validator.py        # Data validator tests
│
├── pipelines/                   # PDF parsing & data processing
│   ├── parse_mcc_pdf.py         # MCC AIQ allotment PDF parser
│   ├── parse_kea_pdf.py         # Karnataka KEA PDF parser
│   ├── build_closing_ranks.py   # Derive closing rank tables
│   ├── build_college_master.py  # Build college master list
│   ├── build_curated.py         # Build curated datasets
│   └── manifest.py              # PDF manifest management
│
├── scripts/                     # CLI tools & batch runners
│   ├── cli_demo.py              # College predictor CLI
│   ├── rank_cli_demo.py         # Rank estimator CLI
│   ├── run_batch_mcc.py         # Batch parse all PDFs
│   └── run_validators.py        # Run data validation suite
│
├── data/                        # Datasets (curated + raw)
│   ├── curated/                 # Production CSVs
│   │   ├── exam_years.csv       # Year metadata (highest, toppers, appeared, cutoff)
│   │   ├── marks_rank_points.csv # Marks-to-rank anchor points per year
│   │   ├── closing_ranks.csv    # College closing ranks by year/round/category
│   │   ├── colleges.csv         # College master list
│   │   └── ...
│   ├── parsed/                  # Intermediate parsed data
│   ├── raw/                     # Raw downloads (NTA, MCC, KEA)
│   ├── sources/                 # Data source registry
│   └── templates/               # CSV templates for data entry
│
├── mcc_aiq/                     # MCC All India Quota PDFs (2020–2025)
├── states/                      # State counselling PDFs (Bihar, Karnataka)
├── db/                          # Database schema
│
├── docs/
│   ├── reports/                 # Phase completion reports
│   │   ├── PHASE0_REPORT.md
│   │   ├── PHASE1A_DATA_REPORT.md
│   │   ├── PHASE1B_AIR_COLLEGE_PREDICTOR_REPORT.md
│   │   ├── PHASE1B_MARKS_TO_AIR_REPORT.md
│   │   ├── PHASE1B_C_RANK_CALIBRATION_REPORT.md
│   │   └── PHASE1B_D_RANK_ACCEPTANCE_REPORT.md
│   └── plans/                   # Planning & tracking docs
│       ├── NEET_rank_prediction_plan.md
│       └── DATA_ACQUISITION_CHECKLIST.md
│
├── _archive/                    # Archived/unused files
├── pyproject.toml
├── requirements.txt
└── .gitignore
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -q

# Estimate rank from marks
python scripts/rank_cli_demo.py --marks 600 --normalization affine_two_point

# Run validation against 2025 held-out data
python scripts/rank_cli_demo.py --validate

# Compare all normalization strategies
python scripts/rank_cli_demo.py --compare

# Predict colleges from AIR
python scripts/cli_demo.py --air 5000 --category General --state Karnataka
```

## Normalization Strategies

| Strategy | Coverage (2025) | Description |
|----------|----------------|-------------|
| `none` | 42.9% | Raw interpolation, no adjustment |
| `topper_score` | 66.7% | Scale by highest marks ratio |
| `affine_two_point` | 66.7% | Two-point affine (highest + cutoff anchors) — **recommended** |
| `piecewise_affine` | 66.7% | Affine + top-band compression — experimental |

## Tech Stack

- Python 3.12, pandas, numpy, scipy, pdfplumber
- pytest (225 tests)
- No ML models — pure interpolation from historical data


# SIEMENS LLM API

API key stored in `.env` (not committed to Git).

```bash
# .env (create from .env.example)
SIEMENS_API_KEY=your-key-here
LLM_MODEL_PRIMARY=deepseek-v4-flash
LLM_MODEL_NARRATIVE=gpt-oss-120b
LLM_MODEL_FALLBACK=qwen-3.6-27b
```

## Available Models
mistral-7b-instruct
qwen-3.6-27b
glm-5
ministral-3-14b-instruct-2512
deepseek-v4-flash
gpt-oss-120b
whisper-large-v3-turbo