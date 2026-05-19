"""Eligibility logic for MCC AIQ and KEA Karnataka counselling.

IMPORTANT: MCC and KEA use completely separate category systems.
- MCC categories: Open, OBC, SC, ST, EWS, PwD variants
- KEA categories: GM, 1G, 2AG, 2BG, 3AG, 3BG, SCG, STG, etc.
Never mix them.  National OBC ≠ KEA 2A/2B/3A/3B.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateProfile:
    """Candidate input profile for prediction."""

    air: int
    national_category: str  # "General", "OBC", "SC", "ST", "EWS"
    home_state: str
    pwd: bool = False
    course_pref: str = "MBBS"  # "MBBS" or "BDS"
    college_type_pref: str = "any"  # "any", "government", "deemed", "central", "AIIMS"
    karnataka_interest: bool = False
    karnataka_domicile: bool = False
    karnataka_category: str | None = None  # KEA category: "GM", "2A", "3B", etc.


# ── MCC AIQ Category Mapping ──
# (national_category, pwd) → seat categories candidate can compete for.
# Order: own category first, then Open.

_MCC_CATEGORY_MAP: dict[tuple[str, bool], list[str]] = {
    ("General", False): ["Open"],
    ("General", True): ["PwD Open", "Open"],
    ("OBC", False): ["OBC", "Open"],
    ("OBC", True): ["PwD OBC", "OBC", "PwD Open", "Open"],
    ("SC", False): ["SC", "Open"],
    ("SC", True): ["PwD SC", "SC", "PwD Open", "Open"],
    ("ST", False): ["ST", "Open"],
    ("ST", True): ["PwD ST", "ST", "PwD Open", "Open"],
    ("EWS", False): ["EWS", "Open"],
    ("EWS", True): ["PwD EWS", "EWS", "PwD Open", "Open"],
}


# ── KEA Karnataka Category Mapping ──
# Suffix: G=General merit, H=Hyderabad-Karnataka, K=Kannada medium, R=Rural
# Non-domicile candidates can ONLY compete in GM.
# National OBC is NEVER mapped to KEA 2A/2B/3A/3B — user must supply KEA category.

_KEA_DOMICILE_CATEGORY_MAP: dict[str, list[str]] = {
    "GM": ["GM"],
    "1": ["1G", "GM"],
    "2A": ["2AG", "GM"],
    "2B": ["2BG", "GM"],
    "3A": ["3AG", "GM"],
    "3B": ["3BG", "GM"],
    "SC": ["SCG", "GM"],
    "ST": ["STG", "GM"],
}


def get_mcc_eligible_categories(profile: CandidateProfile) -> list[str]:
    """Return MCC seat categories a candidate can compete for."""
    key = (profile.national_category, profile.pwd)
    categories = _MCC_CATEGORY_MAP.get(key)
    if categories is None:
        return ["Open"]
    return list(categories)


def get_kea_eligible_categories(profile: CandidateProfile) -> list[str]:
    """Return KEA seat categories a candidate can compete for.

    - No Karnataka interest → empty.
    - Non-domicile → GM only.
    - Domicile + specific KEA category → category-specific seats + GM.
    - Domicile + category=None ("Not Sure") → GM only (exploratory).
    """
    if not profile.karnataka_interest:
        return []

    if profile.karnataka_domicile and profile.karnataka_category:
        cats = _KEA_DOMICILE_CATEGORY_MAP.get(
            profile.karnataka_category, ["GM"]
        )
        return list(cats)

    # Non-domicile OR domicile without specified category → GM only
    return ["GM"]
