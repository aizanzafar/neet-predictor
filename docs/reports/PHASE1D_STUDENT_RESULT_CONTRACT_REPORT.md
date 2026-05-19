# Phase 1D: Student-Facing Result Contract Report

**Date**: 2025-05-17  
**Status**: ACCEPTED  
**Test Suite**: 310 tests passing (42 new + 268 existing, zero regressions)

---

## 1. Summary

Phase 1D introduces `StudentResult` — a stable, frozen dataclass contract that transforms the raw `UnifiedResult` into a student-facing structure. It is designed to be consumed by three future layers without modification:

1. **Streamlit UI** — render sections directly
2. **PDF/export** — serialise to JSON or format to PDF
3. **LLM counselling layer** — pass as structured context to prompt templates

No prediction logic was added or changed. This is a pure view transform.

---

## 2. Contract Structure

```
StudentResult
├── input_summary: InputSummary        # Echo of student's input
├── rank_summary: RankSummary          # Estimated AIR range (if marks provided)
├── rank_used: RankUsedSummary         # Which AIR drives college prediction
├── shortlist: list[CollegeEntry]      # Top-N colleges, best → worst
├── mcc_summary: AuthoritySummary      # MCC total + counts by chance label
├── kea_summary: AuthoritySummary      # KEA total + counts by chance label
├── course_split: list[CourseSplit]    # MBBS/BDS breakdown of shortlist
├── warnings: list[str]               # Pipeline warnings
├── limitations: list[str]            # Fixed limitations (always shown)
└── metadata: Metadata                # Timestamp, engine version, top_n
```

All dataclasses are `frozen=True` — immutable after construction.

---

## 3. Key Design Decisions

### 3.1 Chance Labels Preserved

The backend labels are used as-is:
- **Safe** — admitted all years, margin ≥ 20%, 3+ years data
- **Likely** — admitted all years
- **Borderline** — admitted some years, or weighted margin ≥ -10%
- **Unlikely** — everything else
- **Insufficient data** — fewer than 2 R1 years

No renaming to "reach/ambitious" — those terms were deliberately avoided.

### 3.2 Shortlist Logic

- Default top-N = 20
- Sorted by: chance label (best first) → weighted margin (highest first) → name
- "Insufficient data" entries are excluded from shortlist unless there are fewer than top-N usable predictions
- Configurable via `top_n` parameter

### 3.3 Course Split

Counts MBBS vs BDS entries *within the shortlist only*, not across all predictions. This gives an accurate picture of what the student will see.

### 3.4 Limitations vs Warnings

- **Warnings**: Dynamic, flow-dependent (e.g., "estimated AIR used", "marks experimental")
- **Limitations**: Static, always present (e.g., "based on R1 only", "KEA data limited", "not a guarantee")

### 3.5 Normalization Stored as String

`InputSummary.normalization` is the string value of the enum (e.g., `"affine_two_point"`) for easy serialization.

---

## 4. Dataclass Reference

| Class | Fields | Frozen |
|-------|--------|--------|
| `StudentResult` | 10 fields | Yes |
| `InputSummary` | 12 fields | Yes |
| `RankSummary` | 7 fields | Yes |
| `RankUsedSummary` | 3 fields | Yes |
| `CollegeEntry` | 12 fields | Yes |
| `ChanceBucket` | 2 fields (label, count) | Yes |
| `AuthoritySummary` | 4 fields | Yes |
| `CourseSplit` | 2 fields (course, count) | Yes |
| `Metadata` | 5 fields | Yes |

---

## 5. Test Coverage (42 tests)

| Test Class | Count | Purpose |
|-----------|-------|---------|
| TestInputSummary | 5 | All three flows + normalization + Karnataka |
| TestRankSummary | 4 | Has/no estimate, rank order, both flow |
| TestRankUsed | 4 | Source correct per flow, explanation non-empty |
| TestShortlist | 7 | List type, top-N, ordering, fields, usable-first |
| TestAuthoritySummary | 6 | MCC/KEA present, exploratory flag, bucket sums |
| TestCourseSplit | 3 | List type, entries valid, sums to shortlist |
| TestWarningsAndLimitations | 5 | Pipeline warnings, static limitations, KEA sparse |
| TestMetadata | 5 | ISO timestamp, version, top-N, totals |
| TestFrozenContract | 3 | Immutability of result, input, rank |

---

## 6. Files Created

| File | Purpose |
|------|---------|
| `src/neet_predictor/integrated/summary.py` | `StudentResult`, `build_student_result()`, all sub-dataclasses |
| `tests/test_integrated_summary.py` | 42 tests |
| `docs/reports/PHASE1D_STUDENT_RESULT_CONTRACT_REPORT.md` | This report |

---

## 7. What Was NOT Done (By Design)

- No Streamlit UI
- No LLM integration
- No PDF export
- No prediction logic changed
- No curated data modified
- No new chance labels introduced
- No admission guarantee language
- No invented probabilities

---

## 8. How Consumers Will Use `StudentResult`

### Streamlit UI (Phase 1E)
```python
sr = build_student_result(run_prediction(input))
st.metric("AIR Used", f"{sr.rank_used.air:,}")
for entry in sr.shortlist:
    render_college_card(entry)
for w in sr.warnings:
    st.warning(w)
```

### LLM Layer (Phase 1F)
```python
sr = build_student_result(run_prediction(input))
prompt = f"""Given this student's prediction result:
- Rank: {sr.rank_summary}
- Top colleges: {sr.shortlist[:10]}
- Warnings: {sr.warnings}
Generate a counselling summary..."""
```

### PDF Export (Future)
```python
sr = build_student_result(run_prediction(input))
data = dataclasses.asdict(sr)  # All frozen → safe to serialise
json.dumps(data)
```

---

## 9. Full Test Suite

```
310 passed in 125.36s
```

Zero regressions across all phases (1A through 1D).
