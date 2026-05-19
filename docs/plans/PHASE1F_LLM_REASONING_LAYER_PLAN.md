# Phase 1F: Evidence-Grounded LLM Reasoning Layer — Full Plan

## 1. Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Student (natural language)                              │
│  "I have 620 marks, OBC, Karnataka, maybe 2A,           │
│   want MBBS only, government preferred, BDS backup"      │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: INTENT PARSER (LLM call #1)                    │
│                                                          │
│  Input:  raw student message                             │
│  Output: structured JSON — StudentIntent                 │
│                                                          │
│  {                                                       │
│    "marks": 620,                                         │
│    "actual_air": null,                                   │
│    "national_category": "OBC",                           │
│    "home_state": "Karnataka",                            │
│    "pwd": false,                                         │
│    "karnataka_interest": true,                           │
│    "karnataka_domicile": null,    ← AMBIGUOUS            │
│    "karnataka_category": "2A",    ← UNCERTAIN ("maybe")  │
│    "course_pref": "MBBS",                                │
│    "college_type_pref": "government",                    │
│    "bds_backup": true,                                   │
│    "missing_slots": ["karnataka_domicile"],              │
│    "uncertain_slots": ["karnataka_category"],            │
│    "ambiguity_notes": [                                  │
│      "Student said 'maybe 2A' — not confirmed",          │
│      "Domicile status not stated"                        │
│    ]                                                     │
│  }                                                       │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: SLOT RESOLVER                                  │
│                                                          │
│  Deterministic logic (no LLM):                           │
│                                                          │
│  IF missing critical slots:                              │
│    → return clarification questions to student            │
│  IF uncertain slots:                                     │
│    → plan scenario branches (with/without that slot)     │
│  IF bds_backup:                                          │
│    → plan MBBS-only + MBBS+BDS scenarios                 │
│                                                          │
│  Output: list of ScenarioSpec to run                     │
│  [                                                       │
│    {label: "MBBS, MCC only",       ...params},           │
│    {label: "MBBS, KEA GM",         ...params},           │
│    {label: "MBBS, KEA 2A domicile",...params},           │
│    {label: "MBBS+BDS, MCC",        ...params},           │
│  ]                                                       │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: DETERMINISTIC TOOL EXECUTOR                    │
│                                                          │
│  For each ScenarioSpec:                                  │
│    1. Build UnifiedInput(marks, category, state, ...)    │
│    2. run_prediction(input) → UnifiedResult              │
│    3. build_student_result(result) → StudentResult       │
│                                                          │
│  Output: list of (ScenarioLabel, StudentResult) pairs    │
│                                                          │
│  NO LLM involved in this layer.                          │
│  Pure deterministic computation.                         │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: SCENARIO COMPARATOR (deterministic)            │
│                                                          │
│  Compare StudentResults across scenarios:                │
│  - total safe/likely/borderline per scenario             │
│  - best government MBBS options per scenario             │
│  - rank range differences                                │
│  - KEA vs MCC coverage                                   │
│  - MBBS-only vs MBBS+BDS delta                           │
│                                                          │
│  Output: ComparisonTable (structured data)               │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: LLM REASONED ANSWER (LLM call #2)             │
│                                                          │
│  Input:                                                  │
│    - StudentIntent (from Layer 1)                        │
│    - All StudentResults (from Layer 3)                   │
│    - ComparisonTable (from Layer 4)                      │
│    - System prompt with strict rules                     │
│                                                          │
│  LLM generates:                                          │
│    - Student-friendly conclusion                         │
│    - Primary recommendation path                         │
│    - Backup path                                         │
│    - Top 5–10 specific college names (from shortlists)   │
│    - Why college A is safer than college B                │
│    - KEA vs MCC comparison                               │
│    - MBBS vs BDS explanation (if backup requested)       │
│    - Risk areas                                          │
│    - What's missing / what to verify                     │
│                                                          │
│  LLM is FORBIDDEN from:                                  │
│    - Inventing colleges not in shortlists                │
│    - Upgrading chance labels (Borderline → Safe)         │
│    - Claiming exact rank                                 │
│    - Removing warnings/limitations                       │
│    - Stating admission probability percentages           │
│    - Making KEA claims without R1 data                   │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 6: OUTPUT VALIDATOR (deterministic)               │
│                                                          │
│  Checks LLM output against ground truth:                 │
│                                                          │
│  ✓ Every college name mentioned exists in shortlists     │
│  ✓ No chance label was upgraded                          │
│  ✓ No fake probability numbers                           │
│  ✓ Required warnings are present                         │
│  ✓ Required limitations are present                      │
│  ✓ "not a guarantee" disclaimer present                  │
│  ✓ No unsupported KEA claim                              │
│  ✓ Marks-to-AIR labeled as experimental if used          │
│                                                          │
│  IF validation fails:                                    │
│    → strip the LLM narrative                             │
│    → fall back to structured StudentResult only           │
│    → log the violation for debugging                     │
│                                                          │
│  Output: ValidatedCounsellingResponse                    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. File Plan

```
src/neet_predictor/counsellor/
├── __init__.py
├── intent.py          # Layer 1: StudentIntent dataclass + LLM intent parser
├── slots.py           # Layer 2: Slot resolver + ScenarioSpec builder
├── executor.py        # Layer 3: Run scenarios through deterministic tools
├── comparator.py      # Layer 4: Compare scenario results
├── reasoner.py        # Layer 5: LLM reasoned answer generation
├── validator.py       # Layer 6: Output validation
├── llm_client.py      # GLM-5 API client (Siemens endpoint)
├── prompts.py         # All prompt templates (system + user)
└── orchestrator.py    # Top-level: ties all layers together

tests/
├── test_counsellor_intent.py
├── test_counsellor_slots.py
├── test_counsellor_executor.py
├── test_counsellor_comparator.py
├── test_counsellor_validator.py
└── test_counsellor_orchestrator.py

scripts/
└── counsellor_cli_demo.py
```

---

## 3. Dataclass Contracts

### Layer 1 Output: StudentIntent

```python
@dataclass(frozen=True)
class StudentIntent:
    marks: int | None
    actual_air: int | None
    national_category: str | None
    home_state: str | None
    pwd: bool
    karnataka_interest: bool
    karnataka_domicile: bool | None  # None = not stated
    karnataka_category: str | None
    course_pref: str                 # "MBBS" | "BDS" | "MBBS+BDS"
    college_type_pref: str           # "any" | "government" | "deemed" etc.
    bds_backup: bool
    missing_slots: list[str]         # required but not provided
    uncertain_slots: list[str]       # provided but hedged ("maybe", "I think")
    ambiguity_notes: list[str]       # human-readable notes
    raw_query: str                   # original student message
```

### Layer 2 Output: ScenarioSpec

```python
@dataclass(frozen=True)
class ScenarioSpec:
    label: str                       # "MBBS, MCC only"
    description: str                 # why this scenario exists
    unified_input: UnifiedInput      # ready to pass to run_prediction()
```

### Layer 3 Output: ScenarioResult

```python
@dataclass(frozen=True)
class ScenarioResult:
    spec: ScenarioSpec
    student_result: StudentResult
```

### Layer 4 Output: ScenarioComparison

```python
@dataclass(frozen=True)
class ScenarioComparison:
    scenarios: list[ScenarioResult]
    comparison_table: list[dict]     # per-scenario summary row
    best_scenario_label: str | None  # which has most safe+likely options
    notes: list[str]                 # "KEA with 2A adds 12 more options"
```

### Layer 5 Output: CounsellingNarrative

```python
@dataclass
class CounsellingNarrative:
    summary: str                     # 2-3 sentence conclusion
    primary_path: str                # recommended strategy
    backup_path: str | None          # alternative if primary fails
    top_colleges: list[str]          # college names from shortlists only
    risk_areas: list[str]
    missing_data_caveats: list[str]
    full_narrative: str              # complete LLM-generated text
    model_used: str                  # "glm-5"
    raw_llm_response: str            # for debugging
```

### Layer 6 Output: ValidatedResponse

```python
@dataclass
class ValidatedResponse:
    narrative: CounsellingNarrative | None  # None if validation failed
    scenarios: ScenarioComparison
    validation_passed: bool
    violations: list[str]            # what the LLM got wrong
    fallback_used: bool              # True if narrative was stripped
    warnings: list[str]              # merged from all scenarios
    limitations: list[str]
```

---

## 4. LLM Interaction Points (Only 2 Calls)

| Call | Layer | Purpose | Fallback if LLM fails |
|------|-------|---------|----------------------|
| **Call 1** | Intent Parser | Extract structured intent from natural language | Ask student to fill a form manually |
| **Call 2** | Reasoned Answer | Generate counselling narrative from structured results | Show raw StudentResult tables |

Everything else is deterministic. The LLM never touches prediction math.

---

## 5. Prompt Templates (Key Excerpts)

### Intent Parser System Prompt
```
You are an intake parser for a NEET UG college prediction system.
Extract structured fields from the student's message.

RULES:
- If a field is not mentioned, set it to null.
- If a field is hedged ("maybe", "I think", "probably"), put it in
  uncertain_slots and still extract the value.
- Never assume Karnataka domicile from home_state alone.
- Never infer KEA category from national category.
- "BDS backup" means course_pref="MBBS" AND bds_backup=true.
- Valid national_category: General, OBC, SC, ST, EWS.
- Valid karnataka_category: GM, 1, 2A, 2B, 3A, 3B, SC, ST.

Output: JSON matching the StudentIntent schema. Nothing else.
```

### Reasoned Answer System Prompt
```
You are a counselling advisor for NEET UG students.
You have been given deterministic prediction results.

STRICT RULES:
1. ONLY mention colleges that appear in the provided shortlists.
2. NEVER upgrade a chance label (if the engine says Borderline, you
   say Borderline or worse, never Likely or Safe).
3. NEVER state admission probability percentages.
4. NEVER claim exact rank from marks.
5. ALWAYS include: "This is not an admission guarantee."
6. ALWAYS mention if marks-based AIR estimation was used (experimental).
7. NEVER make unsupported KEA claims if KEA data shows
   "Insufficient data".
8. ALWAYS preserve all warnings from the prediction engine.

You MUST include these sections:
- Summary (2-3 sentences)
- Primary recommended path
- Backup path (if applicable)
- Top 5-10 colleges with their chance labels
- Risk areas
- What to verify with official sources
```

---

## 6. Validator Rules (Deterministic Checks)

| Rule | Check | On Failure |
|------|-------|------------|
| No fake colleges | Every college name in narrative ∈ union of all shortlists | Strip narrative |
| No upgraded labels | If narrative says "Safe" for college X, engine must say Safe | Strip narrative |
| No probabilities | Regex: no "X% chance", "probability of", "X out of 10" | Strip sentence |
| Required disclaimer | "not.*guarantee" present | Append disclaimer |
| Experimental label | If marks-based, "experimental" or "estimated" present | Append warning |
| KEA grounding | If narrative mentions KEA college, KEA data must exist | Strip KEA claims |
| Warnings preserved | All engine warnings appear in response | Append missing |

---

## 7. Build Order

| Step | What | LLM needed? | Testable without API? |
|------|------|-------------|----------------------|
| 1 | `intent.py` — StudentIntent dataclass | No | Yes |
| 2 | `slots.py` — ScenarioSpec builder | No | Yes |
| 3 | `executor.py` — run scenarios | No | Yes |
| 4 | `comparator.py` — compare results | No | Yes |
| 5 | `validator.py` — output checker | No | Yes |
| 6 | `llm_client.py` — GLM-5 API wrapper | Config only | Mock for tests |
| 7 | `prompts.py` — prompt templates | No | Yes (static strings) |
| 8 | `reasoner.py` — LLM call #2 | Yes | Mock for tests |
| 9 | `orchestrator.py` — full pipeline | Yes | Mock LLM for tests |
| 10 | Intent parser (LLM call #1) | Yes | Mock for tests |

**Key insight**: Steps 1–5 are fully deterministic and testable with zero API access. Step 6–10 need the GLM-5 API key but can be tested with mocked LLM responses.

---

## 8. What the LLM is NOT Allowed to Do

| Forbidden | Why |
|-----------|-----|
| Predict rank from marks | Deterministic engine does this |
| Look up closing ranks | Deterministic engine does this |
| Classify chance labels | Deterministic engine does this |
| Invent colleges | Must come from curated data |
| Override warnings | Safety requirement |
| Skip disclaimer | Legal/ethical requirement |
| Derive KEA category from national category | They are separate systems |
| State percentage probabilities | We don't compute these |

---

## 9. API Configuration Needed

```python
# src/neet_predictor/counsellor/llm_client.py
LLM_CONFIG = {
    "provider": "siemens",           # or "openai-compatible"
    "model": "glm-5",               # or "qwen3.6-27b"
    "endpoint": "...",               # Siemens API URL
    "api_key_env": "SIEMENS_LLM_KEY",
    "max_tokens": 2000,
    "temperature": 0.3,             # low — we want deterministic-ish
    "timeout_seconds": 30,
}
```

---

## 10. Test Strategy

| Test File | Tests | LLM Needed? |
|-----------|-------|-------------|
| `test_counsellor_intent.py` | StudentIntent validation, missing slots detection | No (mock LLM) |
| `test_counsellor_slots.py` | Scenario generation from intent, branch logic | No |
| `test_counsellor_executor.py` | Scenarios produce valid StudentResults | No |
| `test_counsellor_comparator.py` | Comparison table, best scenario selection | No |
| `test_counsellor_validator.py` | Fake college detection, label upgrade detection, warning preservation | No |
| `test_counsellor_orchestrator.py` | End-to-end with mocked LLM | Mock |

**Target: ~40-50 new tests, all runnable without API key.**

---

## 11. Acceptance Gate

- [ ] All existing 310 tests still pass
- [ ] 40+ new tests pass (mocked LLM)
- [ ] Validator catches: fake college, upgraded label, missing disclaimer
- [ ] Fallback works: if LLM fails or is invalid, structured result still shown
- [ ] CLI demo works with real GLM-5 API (manual verification)
- [ ] No prediction logic modified
- [ ] No curated data modified
