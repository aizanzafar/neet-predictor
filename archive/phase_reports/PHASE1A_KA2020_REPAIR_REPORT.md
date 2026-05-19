# Phase 1A — Karnataka KEA UGNEET 2020 Repair Report

**Date:** 2026-05-19  
**Scope:** Karnataka KEA UGNEET 2020 MBBS/BDS counselling data acquisition  
**Verdict:** **ACCEPTED WITH GAPS**

---

## 1. Core Data Documents Acquired

### Closing Rank PDFs (6 files — PRIMARY DATA)

Downloaded from `cetonline.karnataka.gov.in/keawebentry456/ugneet2020/R1/` and `R2/`:

| # | File | Path | Size (bytes) | SHA256 |
|---|------|------|-------------|--------|
| 1 | medi_cutoff_gen_r1.pdf | data/raw/kea_karnataka/2020/R1/ | 85,531 | c5a169c1094f885bab9b5a87cafe850891234ed8331f0cf097f5f70c7ecee599 |
| 2 | medi_cutoff_hk_r1.pdf | data/raw/kea_karnataka/2020/R1/ | 81,833 | 3600ad9caad616564f43ca4c475c49417e61e46e833fdc928be7835801660911 |
| 3 | medi_cutoff_priv_r1.pdf | data/raw/kea_karnataka/2020/R1/ | 64,622 | fdaeb23e3e21d14a13eee887dfee35ef8e4afcb04e89572b090bb558ded006b2 |
| 4 | medi_cutoff_gen.pdf | data/raw/kea_karnataka/2020/R2/ | 85,525 | c9ed04ae5d1195a498a5122ec4c8ca50b7c1993179fc7e4b0b1b0cd839b168d2 |
| 5 | medi_cutoff_hk.pdf | data/raw/kea_karnataka/2020/R2/ | 81,903 | 6b9529b4830514c98fdad317bfb9af4a8cc60da0ca31fa60de5df571cac98118 |
| 6 | medi_cutoff_priv.pdf | data/raw/kea_karnataka/2020/R2/ | 64,597 | 5896984b7046660da6160029655a05beb653e64d47508959397bb58c07d685f5 |

### Fee Structure (1 file)

| # | File | Path | Size (bytes) | SHA256 |
|---|------|------|-------------|--------|
| 7 | fees.pdf | data/raw/kea_karnataka/2020/R2/ | 96,766 | 8c09400916f1242dd3de8cac6f74cc1660f3d81c0386a085914f54d234730eef |

Note: R1/fees.pdf and R2/fees.pdf are identical (same SHA256).

### Eligible List (1 file — RANK CALIBRATION DATA)

| # | File | Path | Size (bytes) | SHA256 |
|---|------|------|-------------|--------|
| 8 | Provisional_R1_FinalNEET_2020.pdf | data/raw/kea_karnataka/2020/ | 35,893,478 | 85c181989b242eb21a4466395219b809a7f9d7c30a63d822fe805ccc5ae037be |

Source URL: `https://cetonline.karnataka.gov.in/keawebentry456/ugneet2020/EligibilityFinalNEET.pdf`  
Content: 6,925 pages; 25,569 candidates with NEET Score + AIR Rank + Category + HK/Karnataka status.

---

## 2. Parsed Data Summary

### Closing Ranks CSV

**Output:** `data/parsed/kea_cutoffs/kea_2020_closing_ranks.csv`

| Metric | Value |
|--------|-------|
| Total closing rank entries | 3,480 |
| Unique colleges | 93 |
| Courses | MBBS (2,382 entries), BDS (1,098 entries) |
| Rounds | R1 (1,734 entries), R2 (1,746 entries) |
| Category groups | General (24 cats), HK (24 cats), Private (20 cats) |
| Rank range | 3,857 – 817,500 |
| Median rank | 96,743 |

**Categories parsed:**
- **General (24):** 1G, 1K, 1R, 2AG, 2AK, 2AR, 2BG, 2BK, 2BR, 3AG, 3AK, 3AR, 3BG, 3BK, 3BR, GM, GMK, GMR, SCG, SCK, SCR, STG, STK, STR
- **Hyderabad-Karnataka (24):** 1H, 1KH, 1RH, 2AH, 2AKH, 2ARH, 2BH, 2BKH, 2BRH, 3AH, 3AKH, 3ARH, 3BH, 3BKH, 3BRH, GMH, GMKH, GMRH, SCH, SCKH, SCRH, STH, STKH, STRH
- **Private/NRI (20):** GMP, GMPH, MA, MC, ME, MEH, MK, MM, MMH, MU, NRI, OPN, OTH, RC2-RC8

**Seat types:** GOVT (2,515), PRIV (347), OTHERS (118), NRI (23)

### Eligible List CSV

**Output:** `data/parsed/rank_calibration/kea_2020_eligible_full.csv`

| Metric | Value |
|--------|-------|
| Candidates parsed | 25,569 |
| Score range | 113 – 703 |
| Rank range | 55 – 818,580 |
| Columns | neet_roll_no, neet_score, neet_ai_rank, category, hk, karnataka |
| Category distribution | General Merit 4,857; Category-2A 4,549; Category-3B 4,431; unknown 4,231; Category-3A 3,524; Category-2B 2,465; Category-1 1,512 |

---

## 3. Spot-Check Validation

### Bangalore Medical College (M001) — Round 1, MBBS, Govt

| Category | Closing Rank | Plausibility |
|----------|-------------|-------------|
| GM | 3,857 | ✅ Top govt college, lowest rank as expected |
| 3BG | 5,572 | ✅ Low rank for reserved category at top college |
| GMH | 5,990 | ✅ HK quota slightly above GM |
| SCG | 33,725 | ✅ SC category, higher rank expected |
| SCK | 72,533 | ✅ SC Karnataka reservation, higher |
| SCR | 55,546 | ✅ SC Rural, intermediate |
| STR | 29,712 | ✅ ST Rural for top college |

### M002 (Dr. B.R. Ambedkar MC) — Concatenation Fix Validation

| Category | Closing Rank | Note |
|----------|-------------|------|
| SCR | 180,454 | ✅ Originally concatenated as "18045491865" — correctly split |
| STG | 91,865 | ✅ Second part of split — valid for ST general at mid-tier college |

### High-Rank Validation (> 700K)

15 entries with rank > 700K — all are NRI seats or private BDS minority quotas (MMH, MK, ME, MA, MU), which legitimately fill at very high ranks.

---

## 4. Administrative/Reference PDFs

15 additional files downloaded from the root `ugneet2020/` directory:

| # | File | Size (bytes) | Category |
|---|------|-------------|----------|
| 1 | ebrochure.pdf | 623,191 | Reference — Information bulletin |
| 2 | aiq_joined_kea_candidatesenglish.pdf | 532,058 | Reference — AIQ candidates list |
| 3 | Neet_govnotificationenglish.pdf | 475,849 | Reference — Government notification |
| 4–15 | (11 more notification/schedule PDFs) | ~1.4 MB total | Reference — Counselling procedures |

**Total administrative files:** 3,042,742 bytes (2.9 MB), 15 files

---

## 5. Remaining Gaps

| Document | Status | Impact |
|----------|--------|--------|
| Seat matrix (R1 & R2) | NOT FOUND | Cannot determine total seats per college/category; closing ranks still usable for predictions |
| Mop-up round cutoffs | NOT FOUND | Only R1 and R2 data available |
| Allotment-level data (candidate→college mapping) | NOT FOUND | Only aggregate closing ranks available |
| Dental-specific seat matrix | NOT FOUND | BDS closing ranks ARE present in cutoff files |

**Impact Assessment:** The missing seat matrix means we cannot calculate fill rates, but the closing ranks (which are the primary input for the predictor) are fully available for all categories across 93 colleges.

---

## 6. Validation Results

| Check | Result |
|-------|--------|
| File existence | ✅ PASS — 23/23 files present (8 data + 15 admin) |
| Zero-byte check | ✅ PASS — no zero-byte files |
| SHA256 verification | ✅ PASS — all hashes verified |
| Closing rank data integrity | ✅ PASS — all 3,480 values are valid integers in range [3,857 – 817,500] |
| Required document coverage | ✅ PARTIAL — 3/5 core groups present (cutoffs ✅, eligible list ✅, fees ✅, seat matrix ❌, allotments ❌) |
| Row count sanity check | ✅ PASS — 3,480 parsed closing ranks + 25,569 eligible candidates |
| data_sources.csv entries | ✅ PASS — entries 53–60 registered with OFFICIAL_KEA provenance |
| Concatenation fix coverage | ✅ PASS — no values > 820,000 in final output |

---

## 7. Verdict

### **ACCEPTED WITH GAPS**

**Reason:** The core prediction data (college-wise closing ranks for 93 colleges × 68 categories × 2 rounds) is now available and parsed. Combined with the 25,569-candidate eligible list (providing score→rank calibration), KEA 2020 predictions are now **fully viable** for the predictor engine.

### What's Covered

| Data Type | Coverage | Enables |
|-----------|----------|---------|
| Closing ranks (R1 + R2) | 93 colleges, MBBS + BDS, all categories | College admission probability predictions |
| Eligible list | 25,569 candidates with score + rank | Score-to-rank calibration for Karnataka |
| Fee structure | All colleges, Govt/Pvt/NRI/Others | Fee information display |

### What's Missing (non-blocking)

| Data Type | Impact |
|-----------|--------|
| Seat matrix | Cannot compute fill rate; predictions still work on rank alone |
| Mop-up round | R1 + R2 sufficient for base predictions |
| Candidate-level allotments | Not needed for aggregate predictions |

### Parser

Script: `scripts/parse_kea_2020_cutoffs.py`  
Technique: `pdfplumber.extract_text(x_tolerance=1)` + intelligent splitting of concatenated numbers  
Sanity filter: Ranks validated against NEET 2020 max (820,000)

---

## 8. data_sources.csv Entries

| ID | Type | Description | Confidence |
|----|------|-------------|-----------|
| 53 | OFFICIAL_KEA | Provisional Verified Eligible List | high |
| 54 | OFFICIAL_KEA | R1 Medical Cutoff General | high |
| 55 | OFFICIAL_KEA | R1 Medical Cutoff HK | high |
| 56 | OFFICIAL_KEA | R1 Medical Cutoff Private | high |
| 57 | OFFICIAL_KEA | R2 Medical Cutoff General | high |
| 58 | OFFICIAL_KEA | R2 Medical Cutoff HK | high |
| 59 | OFFICIAL_KEA | R2 Medical Cutoff Private | high |
| 60 | OFFICIAL_KEA | Fee Structure | high |
