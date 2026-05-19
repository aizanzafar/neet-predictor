"""Configuration constants and paths for the NEET predictor."""

from pathlib import Path

# ── Project Root ──
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # neet-predictor/

# ── Data paths ──
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PARSED_DIR = DATA_DIR / "parsed"
CURATED_DIR = DATA_DIR / "curated"
TEMPLATES_DIR = DATA_DIR / "templates"
SOURCES_DIR = DATA_DIR / "sources"
VALIDATION_DIR = DATA_DIR / "validation"

RAW_NTA_DIR = RAW_DIR / "nta"
RAW_MCC_DIR = RAW_DIR / "mcc_aiq"
RAW_KEA_DIR = RAW_DIR / "kea_karnataka"

PARSED_MCC_DIR = PARSED_DIR / "mcc_allotments"
PARSED_KEA_DIR = PARSED_DIR / "kea_allotments"

# ── Database (archived — kept for backward compat) ──
DB_DIR = PROJECT_ROOT / "archive" / "db"
SCHEMA_FILE = DB_DIR / "schema.sql"
DB_FILE = PROJECT_ROOT / "neet_predictor.db"

# ── Year range ──
TRAINING_YEARS = [2020, 2021, 2022, 2023, 2024]
VALIDATION_YEAR = 2025
ALL_YEARS = TRAINING_YEARS + [VALIDATION_YEAR]
MIN_YEAR = 2020
MAX_YEAR = 2025

# ── Marks ──
MAX_MARKS = 720
MIN_MARKS = 0

# ── Valid enums ──
VALID_ROUNDS = ("R1", "R2", "R3", "MOPUP", "STRAY")
VALID_COURSES = ("MBBS", "BDS")
VALID_AUTHORITIES = ("MCC", "KEA")
VALID_COUNSELLING_SCOPES = ("AIQ", "STATE_KA")
VALID_OWNERSHIP = ("government", "private", "deemed", "central", "AIIMS", "JIPMER")
VALID_CONFIDENCE = ("high", "medium", "low")
VALID_SOURCE_TYPES = (
    "OFFICIAL_NTA", "OFFICIAL_MCC", "OFFICIAL_KEA",
    "VERIFIED_SCORECARD", "SECONDARY_PORTAL",
)
VALID_GRANULARITY = ("exact", "range", "bucket", "estimated")
VALID_EXTRACTION_METHODS = (
    "manual", "pdf_table", "web_table", "scorecard", "derived", "official_published",
)
VALID_PARSE_QUALITY = ("clean", "minor_issues", "major_issues", "unverified")
VALID_DERIVATION_METHODS = ("derived_from_allotments", "direct_from_cutoff_pdf")

# ── Category systems (NEVER MIX) ──
MCC_CATEGORIES = frozenset({
    "Open", "General", "OBC", "OBC-NCL", "SC", "ST", "EWS",
    "PwD Open", "PwD OBC", "PwD SC", "PwD ST", "PwD EWS",
})

KEA_CATEGORIES = frozenset({
    "GM", "1G", "2A", "2B", "3A", "3B",
    "SCG", "STG", "GMR", "GMK", "HK",
    "1GR", "2AR", "2BR", "3AR", "3BR",
    "SCR", "STR",
    "Kannada Medium", "Rural",
})

# ── Year weights for prediction ──
YEAR_WEIGHTS = {
    2024: 0.40,
    2023: 0.25,
    2022: 0.18,
    2021: 0.10,
    2020: 0.07,
}

# ── Phase 0 gate thresholds ──
GATE_MIN_ANCHOR_POINTS_PER_YEAR = 15
GATE_MIN_YEARS_WITH_DATA = 3
GATE_MIN_CLOSING_RANK_ROWS = 500
