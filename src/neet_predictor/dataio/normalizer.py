"""College name normalization and category mapping utilities."""

import re
from typing import Optional

import pandas as pd


# ── Common substitutions for college name normalization ──
_NAME_REPLACEMENTS = [
    (r"\bgovt\.?\b", "government"),
    (r"\bgov\.?\b", "government"),
    (r"\bmed\.?\b", "medical"),
    (r"\bcoll\.?\b", "college"),
    (r"\binst\.?\b", "institute"),
    (r"\buniv\.?\b", "university"),
    (r"\bhosp\.?\b", "hospital"),
    (r"\bres\.?\b", "research"),
    (r"\bsci\.?\b", "science"),
    (r"\bdist\.?\b", "district"),
    (r"\bdr\.?\b", "doctor"),
    (r"\bshri\.?\b", "shri"),
    (r"\bsri\.?\b", "sri"),
    (r"\b&\b", "and"),
    (r"\s&\s", " and "),
]

# Characters to strip
_STRIP_CHARS = re.compile(r"[,\.\(\)\[\]\{\}\"\'`/\\;:\-]+")
_MULTI_SPACE = re.compile(r"\s+")


def normalize_college_name(raw_name: str) -> str:
    """Normalize a college name to a canonical lowercase form.

    Handles: abbreviations, punctuation, extra whitespace, case.
    """
    if not raw_name or not isinstance(raw_name, str):
        return ""

    name = raw_name.lower().strip()

    # Apply replacements
    for pattern, replacement in _NAME_REPLACEMENTS:
        name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)

    # Remove pin codes (6-digit numbers)
    name = re.sub(r"\b\d{6}\b", "", name)

    # Remove standalone state/UT mentions at end (after comma)
    # e.g., "aiims new delhi, delhi (nct), 110029" → "aiims new delhi"
    # Keep this light — aggressive removal can lose info
    name = re.sub(r",\s*(delhi\s*\(nct\)|[a-z\s]+)\s*$", "", name)

    # Strip special chars
    name = _STRIP_CHARS.sub(" ", name)

    # Collapse whitespace
    name = _MULTI_SPACE.sub(" ", name).strip()

    return name


def find_college_by_alias(
    alias_normalized: str,
    aliases_df: pd.DataFrame,
) -> Optional[int]:
    """Look up a college_id by normalized alias name.

    Args:
        alias_normalized: The normalized name to search for.
        aliases_df: DataFrame of college_aliases with columns
                    [college_id, alias_normalized].

    Returns:
        college_id if found, None otherwise.
    """
    if aliases_df is None or aliases_df.empty:
        return None

    match = aliases_df[aliases_df["alias_normalized"] == alias_normalized]
    if len(match) > 0:
        return int(match.iloc[0]["college_id"])
    return None


def parse_mcc_rank(rank_str: str) -> tuple[str, int]:
    """Parse MCC rank string into (rank_raw, air).

    Handles formats like '1.01', '18.0', '18', '1234'.

    Returns:
        (rank_raw, air) where air is the integer AIR.
    """
    rank_raw = str(rank_str).strip()
    try:
        rank_float = float(rank_raw)
        air = int(rank_float)  # Floor to get base AIR
        return rank_raw, air
    except (ValueError, TypeError):
        raise ValueError(f"Cannot parse rank: '{rank_str}'")


# ── Category mapping (for display/explanation only — never for prediction) ──

MCC_TO_KEA_DISPLAY_MAP = {
    "General": "GM",
    "OBC": "2A/2B/3A/3B (depends on sub-category)",
    "OBC-NCL": "2A/2B/3A/3B (depends on sub-category)",
    "SC": "SCG",
    "ST": "STG",
    "EWS": "No direct KEA equivalent",
}
