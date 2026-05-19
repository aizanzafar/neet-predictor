# PHASE 1A: Data Population Report

**Generated**: 2026-05-17  
**Status**: COMPLETE — Gates partially met (2 structural blockers)

---

## 1. Data Acquisition Summary

| Source Authority | PDFs Available | PDFs Parsed | Years Covered | Total Rows |
|-----------------|---------------|-------------|---------------|------------|
| MCC (AIQ)       | 18            | 18          | 2020–2025     | 226,934    |
| KEA (Karnataka) | 8             | 8           | 2023–2025     | 21,548     |
| **Total**       | **26**        | **26**      | 2020–2025     | **248,482**|

### Missing Data (Cannot Acquire Locally)
- **NTA Result Notices**: Required for `exam_years.csv` (total candidates, cutoff) and `marks_rank_points.csv` (marks-to-rank mapping). These are published as press releases/PDFs on nta.ac.in and are not included in the raw data archive.
- **2025 MCC Multi-Round Wide Format**: Source_ID 24 (`202504151694474576.pdf`) uses a 16-column format not yet supported by the parser.
- **2020 KEA r2_seats.pdf**: Corrupted file (186 bytes, 0 pages).

---

## 2. Curated Data Files

| File | Rows | Status |
|------|------|--------|
| `data_sources.csv` | 34 | Complete |
| `exam_years.csv` | 0 | BLOCKED — NTA data unavailable |
| `marks_rank_points.csv` | 0 | BLOCKED — NTA data unavailable |
| `allotments.csv` | 231,495 | Complete |
| `colleges.csv` | 1,301 | Complete (267 with unknown state) |
| `college_aliases.csv` | 1,537 | Complete |
| `closing_ranks.csv` | 16,468 | Complete |

---

## 3. Parsing Results by File

### MCC AIQ Allotments

| Source ID | Year | Round | PDF | Pages | Rows | Skipped |
|-----------|------|-------|-----|-------|------|---------|
| 1 | 2020 | R1 | 2022072721-1.pdf | 403 | 17,777 | 29 |
| 2 | 2020 | R2 | 2022072916.pdf | 730 | 17,777 | 5,869 |
| 3 | 2021 | R1 | 2022060614.pdf (2021-fmt) | 1,161 | 16,981 | 235 |
| 4 | 2021 | R2 | 2022061436.pdf | 1,360 | 19,536 | 5,884 |
| 5 | 2021 | R1 | 2022061461.pdf (std-fmt) | 721 | 15 | 20,018 |
| 7 | 2022 | MOPUP | 2023053114.pdf | 31 | 367 | 248 |
| 8 | 2022 | STRAY | 2023053124.pdf | 32 | 493 | 188 |
| 9 | 2022 | R1 | 2023053188-1.pdf | 1,138 | 22,265 | 560 |
| 10 | 2022 | R2 | 2023053196.pdf | 2,378 | 22,265 | 6,456 |
| 11 | 2023 | R1 | 2023073062.pdf | 951 | 22,902 | 33 |
| 12 | 2023 | R2 | 2023081882.pdf | 2,405 | 22,902 | 6,218 |
| 13 | 2023 | R3 | 2023090732.pdf | 4,114 | 8,023 | 24,216 |
| 14 | 2023 | STRAY | 2023092765.pdf | 88 | 2,043 | 133 |
| 17 | 2024 | R1 | 2024082536.pdf | 1,098 | 25,643 | 503 |
| 18 | 2024 | R2 | 2024092017.pdf | 2,813 | 25,643 | 8,284 |
| 19 | 2024 | MOPUP | 2024103043.pdf | 45 | 982 | 107 |
| 20 | 2024 | STRAY | 2024112362.pdf | 16 | 252 | 83 |
| 25 | 2025 | MOPUP | 202511141694474556.pdf | 52 | 1,068 | 103 |

**MCC Total**: 18 files, 226,934 rows, 4,821.6s processing time

### Skipped MCC Files

| Source ID | Reason |
|-----------|--------|
| 6 | Duplicate of source_id 1 (same 2020 R1 data) |
| 15 | BDS/nursing-only file |
| 16 | BDS/nursing-only file |
| 22 | Duplicate R2 (same as source_id 12) |
| 24 | 2025 wide 16-col format — parser not implemented |

### KEA Karnataka Allotments

| Source ID | Year | Round | Format | Pages | Rows | Skipped |
|-----------|------|-------|--------|-------|------|---------|
| 28 | 2023 | R1 | 5-col | 80 | 1,954 | 0 |
| 29 | 2023 | R2 | 8-col | 471 | 8,014 | 0 |
| 27 | 2023 | MOPUP | 8-col | 54 | 889 | 0 |
| 30 | 2023 | STRAY | 8-col | 11 | 151 | 0 |
| 31 | 2024 | STRAY | 8-col | 5 | 6 | 48 |
| 32 | 2024 | STRAY | 8-col | 1 | 1 | 6 |
| 33 | 2025 | R2 | 8-col | 540 | 9,566 | 1 |
| 34 | 2025 | R3 | 8-col | 60 | 967 | 0 |

**KEA Total**: 8 files, 21,548 rows

---

## 4. Validation Results

```
[PASS] data_sources: 34 rows
[PASS] colleges: 1,301 rows
[PASS] allotments: 231,495 rows
  WARN: 5 (year, round, authority, quota, air) groups map to multiple colleges
[PASS] closing_ranks: 16,468 rows
SKIPPED (no data): exam_years, marks_rank_points
```

- **4 tables PASS**, 0 FAIL
- 5 warnings: legitimate multi-pool allotments (same AIR across AIIMS/JIPMER/Central pools, or across different quotas)
- **65 unit tests pass** (0 failures)

---

## 5. Gate Status

| Gate | Threshold | Actual | Status |
|------|-----------|--------|--------|
| exam_years ≥ 5 years | 5 | 0 | **FAIL** (NTA data unavailable) |
| marks_rank_points ≥ 15 anchors/yr for ≥ 3 years | 15×3 | 0 | **FAIL** (NTA data unavailable) |
| closing_ranks ≥ 500 rows | 500 | 16,468 | **PASS** |
| Zero unresolved colleges | 0 | 0 | **PASS** |
| All source_id FKs resolve | 100% | 100% | **PASS** |
| All validation tests pass | 100% | 4/4 pass | **PASS** |

### Gate Assessment

**Overall: GATES NOT MET** — 4 of 6 gates pass. Two are structurally impossible without NTA data:

1. `exam_years` — requires total candidates appeared, cutoff marks per category
2. `marks_rank_points` — requires official marks-to-rank mapping data points

These are published by NTA post-exam as press releases. The raw data archive contains only MCC/KEA counselling PDFs (allotment lists), not NTA exam results.

**Recommendation**: Proceed to Phase 1B (rank estimation) using only allotment-derived closing ranks as anchors. The marks→rank mapping can be built from verified scorecard data points or secondary sources when available.

---

## 6. Data Quality Notes

### College State Extraction
- 1,034 / 1,301 colleges (79.5%) have state extracted from college name
- 267 colleges tagged as "Unknown" — names lack state/city identifiers
- KEA colleges auto-assigned "Karnataka"

### Duplicate AIR Groups (5 warnings)
These are legitimate cases where the same AIR appears for different colleges:
- **2022 R1/R2 AIR 2040**: EWS (SETH G.S. Medical, Mumbai) vs Open (Dr Ram Manohar Lohia, Lucknow) — same candidate in different category pools
- **2022 R1/R2 AIR 26272**: OBC All India (GOVT Dental Raipur) vs Open Muslim Quota (Jamia Millia Islamia) — different quotas
- **2023 R1/R2/R3 AIR 1**: JIPMER vs AIIMS — separate counselling pools (Open Seat Quota each)
- **2023 R2 KEA AIR 34119**: Two different colleges under OPN category

### 2020 Category Abbreviations
The 2020 MCC PDFs use abbreviated category codes, mapped via `_MCC_2020_CATEGORY_MAP`:
- GN → Open, GNNO → General, OBC → OBC, SC → SC, ST → ST, EWS → EWS
- GNPH → PwD Open, OBCPH → PwD OBC, SCPH → PwD SC, STPH → PwD ST, EWPH → PwD EWS
- 50 priority-suffix entries cleaned via `postprocess_categories.py`

### 2020 Quota Abbreviations
Mapped via `_MCC_2020_QUOTA_MAP`:
- AI → All India, OS → Open Seat Quota, IP → Internal

### 2024 Rank Format
Uses decimal notation (e.g., "1.01") where digits after decimal indicate tie-breaking position.

### 2023 Rank Format
Uses letter notation (e.g., "1(A)") for tie-breaking.

### Source ID 5 (2021 R1 Standard Format)
Only 15 MBBS/BDS rows extracted from 721 pages — nearly all entries were non-MBBS/BDS courses, correctly filtered out.

### Closing Ranks Derivation
- 116,124 allotment rows excluded (non-final statuses like "Not Allotted", "Resigned")
- 16,468 closing rank entries derived from remaining allotments
- Falls back to `college_raw` when `college_id` unavailable

---

## 7. File Inventory

### Parsed CSVs (data/parsed/)

```
mcc_allotments/
  mcc_2020_R1.csv (17,777)    mcc_2022_MOPUP.csv (367)     mcc_2023_R3.csv (8,023)     mcc_2024_STRAY.csv (252)
  mcc_2020_R2.csv (17,777)    mcc_2022_STRAY.csv (493)     mcc_2023_STRAY.csv (2,043)  mcc_2025_MOPUP.csv (1,068)
  mcc_2021_R1.csv (16,981)    mcc_2022_R1.csv (22,265)     mcc_2024_R1.csv (25,643)
  mcc_2021_R2.csv (19,536)    mcc_2022_R2.csv (22,265)     mcc_2024_R2.csv (25,643)
  mcc_2021_R1.csv (15)*       mcc_2023_R1.csv (22,902)     mcc_2024_MOPUP.csv (982)

kea_allotments/
  kea_2023_R1.csv (1,954)     kea_2023_STRAY.csv (151)     kea_2025_R2.csv (9,566)
  kea_2023_R2.csv (8,014)     kea_2024_STRAY.csv (7)       kea_2025_R3.csv (967)
  kea_2023_MOPUP.csv (889)
```

### Curated CSVs (data/curated/)

```
data_sources.csv      (34 rows)
allotments.csv        (231,495 rows)
colleges.csv          (1,301 rows)
college_aliases.csv   (1,537 rows)
closing_ranks.csv     (16,468 rows)
exam_years.csv        (header only — BLOCKED)
marks_rank_points.csv (header only — BLOCKED)
```

---

## 7. Files Modified/Created

### Parser Scripts
- `pipelines/parse_mcc_pdf.py` — Full MCC parser (standard 8-col + 2021 format)
- `pipelines/parse_kea_pdf.py` — Full KEA parser (5-col + 8-col formats)
- `pipelines/build_curated.py` — Unified curated CSV builder
- `pipelines/build_college_master.py` — College deduplication pipeline
- `pipelines/build_closing_ranks.py` — Closing rank derivation

### Data Files
- `data/sources/data_sources.csv` — 34 source entries with SHA256
- `data/parsed/mcc_allotments/` — Parsed MCC CSVs
- `data/parsed/kea_allotments/` — Parsed KEA CSVs
- `data/curated/` — Final curated tables

### Runner Scripts
- `run_batch_mcc.py` — Combined batch parser runner
- `run_validators.py` — Validation + gate check runner
