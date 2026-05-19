# NEET Predictor — Data Inventory & What's Missing

**Last updated**: 2026-05-18

Use this to figure out which files to collect from friends/sources.

---

## Status Summary: What's Built

| Phase | Status | Tests |
|-------|--------|-------|
| Phase 0: Scaffolding & schema | ✅ Done | 65 |
| Phase 1A: Data pipelines & parsing | ✅ Done | 65 |
| Phase 1B-A: AIR → College predictor | ✅ Done | 61 |
| Phase 1B-B: Marks → AIR estimator | ✅ Done | 47 |
| Phase 1B-C: Paper-difficulty normalization | ✅ Done | 52 |
| Phase 1B-D: Rank estimator acceptance | ✅ Done | (in 1B-C count) |
| Phase 1C: Integrated pipeline (marks/AIR → colleges) | ✅ Done | 43 |
| Phase 1D: Student-facing result contract | ✅ Done | 42 |
| **Total tests passing** | | **310** |

### What's Left to Build

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1E | Streamlit UI | Not started |
| Phase 1F | LLM counselling layer (optional) | Not started |
| Phase 2 | More states (beyond Karnataka) | Not started |
| Phase 2 | Bihar data parsing | PDFs exist, parser not built |
| Phase 2 | More data years / better anchor points | Needs data |
| Future | PDF export of results | Not started |
| Future | API layer (FastAPI) | Not started |

---

## DATA INVENTORY

### 1. MCC All-India Quota (Allotment PDFs)

These are the counselling result PDFs from MCC (Medical Counselling Committee).

| Year | PDFs We Have | Parsed CSVs | R1 Closing Ranks | Notes |
|------|-------------|-------------|-------------------|-------|
| 2020 | 2 (R1, R2) | 2 | ✅ 1,241 rows | OK — but only 2 rounds |
| 2021 | 4 (R1, R2, Admitted, Provisional) + Mop-Up | 3 (R1, R2, Mop-Up) | ✅ **1,839 R1 + 1,085 Mop-Up** | **FIXED** (9-col parser fix) |
| 2022 | 4 (R1, R2, Mop-Up, Stray) | 4 | ✅ 2,486 rows | Good coverage |
| 2023 | 6 (R1, R2, R3, Stray, etc.) | 4 (R1, R2, R3, Stray) | ✅ 2,730 rows | Good coverage |
| 2024 | 7 (R1, R2, R3, Mop-Up, Stray, etc.) | 4 (R1, R2, Mop-Up, Stray) | ✅ 2,915 rows | Good coverage |
| 2025 | 2 (Multi-round, Mop-Up) | 1 (Mop-Up only) | ❌ **0 R1 rows** | **GAP — R1 not parsed yet (multi-round PDF)** |

**What's needed for MCC:**
- ⚠️ **2021**: We have the PDFs but zero closing ranks ended up in curated data. Need to investigate why R1 parsing produced 0 results and fix.
- ⚠️ **2025 R1**: The multi-round PDF needs to be parsed to extract R1 closing ranks (currently only Mop-Up is parsed).
- ⚠️ **2020 R2**: Only 2 closing rank rows from R2 — likely a parsing issue.

---

### 2. Karnataka KEA (Allotment PDFs)

| Year | PDFs We Have | Parsed CSVs | R1 Closing Ranks | Notes |
|------|-------------|-------------|-------------------|-------|
| 2020 | 1 (r2_seats.pdf) | 0 | ❌ 0 | **File is broken (186 bytes). Need a real copy.** |
| 2021 | 0 | 0 | ❌ 0 | **MISSING — no PDFs at all** |
| 2022 | 0 | 0 | ❌ 0 | **MISSING — no PDFs at all** |
| 2023 | 4 (R1, R2, Mop-Up, Stray) | 4 | ✅ 624 rows | Only year with R1 data |
| 2024 | 2 (Stray 5, Stray 6) | 1 (Stray) | ❌ 0 R1 | **MISSING R1, R2 PDFs** |
| 2025 | 2 (R2, R3) | 2 | ❌ 0 R1 | **MISSING R1 PDF** |

**What's needed for KEA:**
- 🔴 **2020**: Need a working R1 allotment PDF (current file is corrupt)
- 🔴 **2021**: Need R1 allotment PDF (nothing exists)
- 🔴 **2022**: Need R1 allotment PDF (nothing exists)
- 🔴 **2024 R1**: Need R1 allotment PDF (only have Stray rounds)
- 🔴 **2025 R1**: Need R1 allotment PDF (only have R2, R3)

**Impact**: KEA predictions currently show "Insufficient data" for almost everything because only 2023 has R1 data. Getting R1 PDFs for even 2-3 more years would dramatically improve KEA predictions.

---

### 3. Bihar BCECE/UGMAC (Allotment PDFs)

| Year | PDFs We Have | Parsed CSVs | Notes |
|------|-------------|-------------|-------|
| 2020 | 1 | 0 | Not parsed yet |
| 2021 | 0 | 0 | **MISSING** |
| 2022 | 1 | 0 | Not parsed yet |
| 2023 | 2 | 0 | Not parsed yet |
| 2024 | 4 | 0 | Not parsed yet |
| 2025 | 10 | 0 | Not parsed yet |

**Status**: Bihar PDFs exist but no parser has been built. This is Phase 2 work.

---

### 4. NTA Marks-to-Rank Calibration Points

These are the marks↔rank anchors used by the rank estimator.

| Year | Anchor Points | Source | Notes |
|------|--------------|--------|-------|
| 2020 | 3 | Official NTA / secondary | Very sparse |
| 2021 | **0** | — | **MISSING — no anchors at all** |
| 2022 | 7 | Official NTA / secondary | OK |
| 2023 | 15 | Official NTA / Careers360 | Good |
| 2024 | 15 | Official NTA / Careers360 | Good |
| 2025 | 21 | Official NTA (validation only) | Used for validation, not training |

**What's needed for NTA:**
- 🔴 **2021**: Need marks-to-rank data points (scorecards, official publications, or Careers360/Embibe tables)
- ⚠️ **2020**: Only 3 points — more would help accuracy
- Any additional verified scorecard data for any year improves the estimator

---

### 5. Exam Year Metadata

| Year | Highest | Toppers | Appeared | Cutoff UR | Status |
|------|---------|---------|----------|-----------|--------|
| 2020 | 720 | 2 | 1,366,945 | 147 | ✅ |
| 2021 | 720 | 3 | 1,544,275 | 138 | ✅ (but 0 rank anchors) |
| 2022 | 715 | 1 | 1,764,571 | 117 | ✅ |
| 2023 | 720 | 2 | 2,038,596 | 137 | ✅ |
| 2024 | 720 | 61 | 2,333,297 | 164 | ✅ |
| 2025 | 686 | 1 | 2,209,318 | 144 | ✅ |

---

## PRIORITY FILE REQUEST LIST

**Ask your friend for these files, in order of impact:**

### High Priority (would unlock major improvements)

1. **KEA Karnataka R1 allotment PDFs** for 2024 and 2025
   - File pattern: KEA Round 1 seat allotment result PDF
   - This would make Karnataka predictions actually useful (currently nearly all "Insufficient data")

2. **KEA Karnataka R1 allotment PDFs** for 2020, 2021, 2022
   - Even 1–2 more years of KEA R1 data helps enormously

3. **2021 NEET marks-to-rank data**
   - Scorecards showing marks and AIR for 2021
   - Or any published table mapping marks ranges to rank ranges for 2021
   - Currently 2021 has ZERO anchor points — it's the only year with no calibration data

### Medium Priority (improves accuracy)

4. **More 2020 marks-to-rank data points**
   - Only 3 anchors currently. Even 5-10 more would help.

5. **MCC 2025 R1 allotment PDF** (separate from multi-round)
   - Currently only Mop-Up is parsed for 2025

6. **MCC 2021 R1 investigation**
   - We have the PDF but parsing produced 0 closing ranks. May need a cleaner copy.

### Low Priority (Phase 2)

7. **Bihar BCECE parser** needs to be built (PDFs exist, parser doesn't)
8. **Other states** — Rajasthan, Tamil Nadu, Maharashtra allotment PDFs
