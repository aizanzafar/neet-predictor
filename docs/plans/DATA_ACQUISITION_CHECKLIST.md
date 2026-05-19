# Phase 1A Data Acquisition Checklist

## Status Legend
- ✅ Available locally (PDF in workspace)
- ❌ Not available — must be obtained
- ⚠️ Partially available or format issues

---

## 1. NTA Result Notices / Statistics (for marks_rank_points + exam_years)

| Year | Status | Source | Notes |
|------|--------|--------|-------|
| 2020 | ❌ | NTA NEET Result Notice | Need: cutoffs, toppers count, total appeared, marks→rank mapping |
| 2021 | ❌ | NTA NEET Result Notice | Need: cutoffs, toppers count, total appeared, marks→rank mapping |
| 2022 | ❌ | NTA NEET Result Notice | Need: cutoffs, toppers count, total appeared, marks→rank mapping |
| 2023 | ❌ | NTA NEET Result Notice | Need: cutoffs, toppers count, total appeared, marks→rank mapping |
| 2024 | ❌ | NTA NEET Result Notice | Need: cutoffs, toppers count, total appeared, marks→rank mapping |
| 2025 | ❌ | NTA NEET Result Notice | Need: cutoffs, toppers count, total appeared, marks→rank mapping |

**ACTION REQUIRED**: NTA result notices are NOT in the workspace. These are required for:
- `exam_years.csv` (appeared candidates, cutoffs, toppers)
- `marks_rank_points.csv` (marks-to-rank anchor points)

Without these, the marks-to-rank estimator has zero training data.

---

## 2. MCC AIQ Allotment PDFs

| Year | Round | File | Pages | Format | Status |
|------|-------|------|-------|--------|--------|
| 2020 | ? | `2022072721-1.pdf` | 403 | Standard 8-col | ✅ |
| 2020 | ? | `2022072916.pdf` | 730 | Standard 8-col | ✅ |
| 2021 | ? | `2022060614.pdf` | 1161 | 11-col (Roll/Name/AIR) | ⚠️ Different format |
| 2021 | ? | `2022061436.pdf` | 1360 | Standard 8-col | ✅ |
| 2021 | ? | `2022061461.pdf` | 721 | TBD | ✅ |
| 2021 | ? | `2022072753.pdf` | 723 | TBD | ✅ |
| 2022 | ? | `2023053114.pdf` | 31 | Standard 8-col (BDS?) | ⚠️ Small |
| 2022 | ? | `2023053124.pdf` | 32 | TBD | ⚠️ Small |
| 2022 | ? | `2023053188-1.pdf` | 1138 | Standard 8-col | ✅ |
| 2022 | ? | `2023053196.pdf` | 2378 | Standard 8-col | ✅ |
| 2023 | R1 | `2023073062.pdf` | 951 | Standard 8-col | ✅ |
| 2023 | ? | `2023081882.pdf` | 2405 | Standard 8-col | ✅ |
| 2023 | ? | `2023090732.pdf` | 4114 | Standard 8-col | ✅ |
| 2023 | ? | `2023092765.pdf` | 88 | Standard 8-col | ✅ |
| 2023 | ? | `2023101919.pdf` | 15 | Standard 8-col | ✅ |
| 2023 | ? | `2023111060.pdf` | 15 | Standard 8-col | ✅ |
| 2024 | R1 | `2024082536.pdf` | 1098 | Standard 8-col | ✅ |
| 2024 | R2 | `2024092017.pdf` | 2813 | Standard 8-col | ✅ |
| 2024 | R2 | `2024_R2_allotment_result_89084e4f.pdf` | 2813 | Standard 8-col | ⚠️ Duplicate of above |
| 2024 | ? | `2024103043.pdf` | 45 | Standard 8-col | ✅ |
| 2024 | ? | `2024112362.pdf` | 16 | Standard 8-col | ✅ |
| 2024 | ? | `2024121323.pdf` | 3 | Standard 8-col | ✅ |
| 2024 | R3 | `FinalAllotmentStatusUG_R3_...pdf` | 3598 | Standard 8-col | ✅ |
| 2025 | Multi | `202510231373953523.pdf` | 1930 | Multi-round wide | ⚠️ Different format |
| 2025 | ? | `202511141694474556.pdf` | 52 | Standard 8-col | ✅ |

---

## 3. KEA Karnataka Allotment PDFs

| Year | Round | File | Pages | Status |
|------|-------|------|-------|--------|
| 2020 | R2 | `r2_seats.pdf` | ? | ⚠️ Seat matrix only (not allotment) |
| 2023 | R1 | `2023_round1_karnataka_allotmentlist_04e0cb3f.pdf` | 80 | ✅ |
| 2023 | R2 | `2023_round2_karnataka_allotmentlist_a36fea30.pdf` | ? | ✅ |
| 2023 | MOPUP | `2023_mopup_karnataka_allotmentlist_48858628.pdf` | ? | ✅ |
| 2023 | STRAY | `2023_stray_karnataka_allotmentlist_bae991fc.pdf` | ? | ✅ |
| 2024 | STRAY5 | `2024_stray5_karnataka_allotmentlist_f558cf0b.pdf` | 5 | ⚠️ Non-standard round |
| 2024 | STRAY6 | `2024_stray6_karnataka_allotmentlist_bdc7b9cf.pdf` | ? | ⚠️ Non-standard round |
| 2025 | R2 | `2025_round2_prov2_karnataka_allotmentlist_19bfff91.pdf` | 540 | ✅ |
| 2025 | R3 | `2025_round3_karnataka_allotmentlist_e2b2bb6d.pdf` | ? | ✅ |

**Missing KEA Data**: No R1 for 2024, 2025. No data for 2021, 2022.

---

## 4. Bihar (OUT OF MVP SCOPE per BLUEPRINT)

Bihar data is present but NOT in scope for the current MVP.

---

## Summary of Critical Gaps

| Data Need | Status | Impact |
|-----------|--------|--------|
| NTA result notices (any year) | ❌ Not available | **P0 BLOCKER**: Cannot populate exam_years or marks_rank_points |
| MCC R1 PDFs identified | ⚠️ Need round identification | Can parse once rounds identified |
| KEA R1 2024/2025 | ❌ Missing | Gap in KEA closing rank data |
| KEA 2021/2022 data | ❌ Missing | Gap in historical KEA data |
