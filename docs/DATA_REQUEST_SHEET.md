# NEET UG College Predictor — Data Request Sheet

> **Share this with your friend.** It lists exactly what data files we need, why, and where to find them.  
> Last updated: 18 May 2026

---

## What We're Building

A NEET UG college prediction engine that takes a student's marks/rank and tells them which colleges they can likely get into under:
- **MCC All-India Quota** (central counselling)
- **KEA Karnataka** (state counselling)
- **Bihar UGMAC** (state counselling — Phase 2)

The engine needs **Round 1 allotment PDFs** from counselling websites to compute closing ranks.  
It also needs **marks-to-rank mapping data** from NTA to estimate AIR from marks.

---

## What We Already Have

### MCC All-India Quota — ✅ COMPLETE

| Year | R1 Closing Ranks | Colleges with R1 | Other Rounds | Status |
|------|----------------:|------------------:|--------------|--------|
| 2020 | 1,241 rows | 326 colleges | Mop-Up (220), R2 (2) | Complete |
| 2021 | 1,839 rows | 345 colleges | Mop-Up (1,085), Stray (459) | Complete |
| 2022 | 2,486 rows | 469 colleges | Mop-Up (183), Stray (353) | Complete |
| 2023 | 2,730 rows | 504 colleges | Stray (861) | Complete |
| 2024 | 2,915 rows | 536 colleges | Mop-Up (630), Stray (171) | Complete |
| 2025 | 3,048 rows | 563 colleges | R2 (2,839), R3 (2,438), Stray (587) | Complete |

> **Total MCC closing ranks: 28,396 across all years and rounds.** All MCC AIQ PDFs for 2020–2025 have been downloaded and parsed.

### KEA Karnataka

| Year | R1 Closing Ranks | Colleges with R1 | Other Rounds | Status |
|------|----------------:|------------------:|--------------|--------|
| 2020 | **0** | **0** | Corrupt file (186 bytes) | **NEED FILE** |
| 2021 | **0** | **0** | No files at all | **NEED FILE** |
| 2022 | **0** | **0** | No files at all | **NEED FILE** |
| 2023 | 624 rows | 38 colleges | R2, Mop-Up, Stray | **Only complete year** |
| 2024 | **0** | **0** | Only Stray 5 & 6 | **NEED R1** |
| 2025 | **0** | **0** | R2, R3 only | **NEED R1** |

### Marks-to-Rank Anchor Points

| Year | Anchor Points | Status |
|------|-------------:|--------|
| 2020 | 3 | Sparse — more would help |
| 2021 | **0** | **MISSING — only year with zero** |
| 2022 | 7 | OK |
| 2023 | 15 | Good |
| 2024 | 15 | Good |
| 2025 | 21 | Good (validation set) |

### Bihar UGMAC

| Year | PDFs | Parsed | Status |
|------|-----:|-------:|--------|
| 2020 | 1 | 0 | Parser not built yet |
| 2021 | **0** | 0 | **NEED FILE** |
| 2022 | 1 | 0 | Parser not built yet |
| 2023 | 2 | 0 | Parser not built yet |
| 2024 | 4 | 0 | Parser not built yet |
| 2025 | 10 | 0 | Parser not built yet |

---

## FILES NEEDED (Priority Order)

### P0 — Critical (Blocks Karnataka predictions entirely)

These are the files that would unlock the biggest improvement. Without them, KEA predictions show "Insufficient data" for almost everything.

| # | What | Where to Find | File Type | Why It Matters |
|---|------|--------------|-----------|----------------|
| **1** | **KEA Karnataka Round 1 allotment list — 2024** | [cetonline.karnataka.gov.in](https://cetonline.karnataka.gov.in) → NEET UG → Results → Round 1 Allotment | PDF | **Unlocks 2024 KEA predictions (currently 0 R1 data)** |
| **2** | **KEA Karnataka Round 1 allotment list — 2025** | Same website → 2025 results | PDF | **Unlocks 2025 KEA predictions** |
| **3** | **KEA Karnataka Round 1 allotment list — 2022** | Same website → 2022 results / archives | PDF | **Adds another year of KEA training data** |
| **4** | **KEA Karnataka Round 1 allotment list — 2021** | Same website → 2021 results / archives | PDF | **Adds another year of KEA training data** |
| **5** | **KEA Karnataka Round 1 allotment list — 2020** | Same website → 2020 results / archives | PDF | **Replaces our corrupt 186-byte file** |

> **What these files look like:** PDF titled something like "Round 1 Allotment List" or "First Round Seat Allotment Result". Contains columns like: CET No, Candidate Name, Rank, College Allotted, Course, Category. Usually 40-100 pages.

---

### P1 — High Priority (Fixes marks-to-rank estimation)

| # | What | Where to Find | File Type | Why It Matters |
|---|------|--------------|-----------|----------------|
| **8** | **NEET 2021 marks-to-rank data** | NTA result notice, Careers360 cutoff tables, Embibe rank predictor archives, student scorecards | Any (PDF / table / image) | **2021 has ZERO rank anchor points — only missing year** |
| **9** | **Additional NEET 2020 marks-to-rank data** | Same sources for 2020 | Any | **Only 3 anchors for 2020 — need 5-10 more** |

> **What we need per data point:** A marks value and the corresponding AIR (All-India Rank). Examples:
> - "I scored 650 in NEET 2021 and got AIR 12,450" ← perfect
> - NTA table: "Marks 600-610 → Rank range 15,000-18,000" ← also works
> - Careers360 article: "NEET 2021 cutoff for General was 138 marks" ← already have this
>
> Any verified scorecard screenshot (marks + rank visible) from 2020 or 2021 students is gold.

---

---

### P4 — Low Priority (Phase 2 — Bihar)

| # | What | Where to Find | File Type | Why It Matters |
|---|------|--------------|-----------|----------------|
| **13** | **Bihar UGMAC Round 1 allotment — 2021** | [bceceboard.bihar.gov.in](https://bceceboard.bihar.gov.in) → UGMAC 2021 | PDF | Only missing year |
| **14** | **Bihar UGMAC Round 1 allotment — any year** (if R1 is identifiable) | Same site | PDF | We have files but can't tell which round is which |

---

### P5 — Nice to Have (New states)

| # | What | Where to Find | File Type | Why It Matters |
|---|------|--------------|-----------|----------------|
| **15** | **Tamil Nadu state counselling R1 allotment** (any year) | TN Medical Selection Committee | PDF | New state support |
| **16** | **Maharashtra state counselling R1 allotment** (any year) | DMER Maharashtra | PDF | New state support |
| **17** | **Rajasthan state counselling R1 allotment** (any year) | Rajasthan UG Medical | PDF | New state support |

---

## How to Find These Files

### MCC All-India Quota
1. Go to **mcc.nic.in**
2. Navigate to **UG Counselling** → select the year
3. Look for **"Allotment Result"** or **"Seat Allotment Result"** 
4. Download the **Round 1** PDF specifically
5. File is typically 500-4000 pages, 1-10 MB

### KEA Karnataka
1. Go to **cetonline.karnataka.gov.in** (or kea.kar.nic.in)
2. Navigate to **NEET UG / UGCET** → select the year
3. Look for **"Round 1 Seat Allotment Result"** or **"First Round Allotment List"**
4. Download the PDF
5. File is typically 40-100 pages, 200KB-3MB

### NTA Marks-to-Rank Data
1. **NTA Official**: nta.ac.in → NEET UG → Results section → "Result Notice" or "Score vs Rank" tables
2. **Careers360**: Search "NEET 2021 marks vs rank" — they publish tables
3. **Embibe / Allen / Aakash**: These coaching institutes publish rank predictor data
4. **Student scorecards**: Any friend who took NEET 2020 or 2021 — screenshot showing marks + rank
5. **Quora / Reddit**: Threads where students share their marks and rank

### Bihar UGMAC
1. Go to **bceceboard.bihar.gov.in**
2. Navigate to **UGMAC** → select the year
3. Download allotment result PDFs

---

## File Naming Convention (When Sending)

Please name files clearly so we can identify them:

```
<authority>_<year>_<round>_<description>.pdf

Examples:
  KEA_2024_R1_allotment.pdf
  KEA_2025_R1_allotment.pdf
  MCC_2021_R1_allotment.pdf
  MCC_2025_R1_allotment.pdf
  Bihar_2021_R1_allotment.pdf
  NTA_2021_marks_rank_table.pdf    (or .png / .jpg / .xlsx)
  NTA_2020_scorecard_student1.jpg
```

---

## Quick Impact Summary

| If you get... | What it unlocks |
|---------------|-----------------|
| KEA R1 2024 + 2025 | Karnataka predictions go from "Insufficient data" → **actually useful** |
| KEA R1 for any 2 more years (2020-2022) | KEA confidence goes from 1-year guess → **multi-year weighted** |
| MCC R1 2021 | MCC coverage goes from 4/6 years → **5/6 years** |
| NEET 2021 marks-rank data | Rank estimation goes from 5/6 years → **all 6 years calibrated** |
| All of the above | System goes from ~70% coverage to **~95% coverage** |

---

## What We DON'T Need

- ~~Seat matrix PDFs~~ (we derive closing ranks from allotment lists)
- ~~Individual student results~~ (we use aggregate data only)
- ~~Fee structure PDFs~~ (not in scope)
- ~~Admission brochures~~ (not in scope)
- ~~AIIMS/JIPMER data~~ (merged into NEET from 2020, already covered under MCC)
- ~~Private deemed university separate counselling~~ (not in scope for now)

---

## Contact / Questions

If unsure whether a file is what we need, just send it anyway — we can check.  
Any file is better than no file. Even a screenshot of a table helps for marks-to-rank data.
