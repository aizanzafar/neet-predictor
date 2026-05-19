"""Layer 2: Slot Resolver — generates scenario branches from StudentIntent.

Pure deterministic logic. No LLM involved.
Handles: missing slots, uncertain slots, BDS backup, KEA branching.
"""

from __future__ import annotations

from neet_predictor.counsellor.models import (
    ClarificationNeeded,
    ScenarioSpec,
    StudentIntent,
)


# Slots that are absolutely required for ANY prediction
_CRITICAL_SLOTS = ("national_category",)


def resolve_slots(
    intent: StudentIntent,
) -> list[ScenarioSpec] | ClarificationNeeded:
    """Convert a StudentIntent into a list of ScenarioSpecs to run.

    Returns ClarificationNeeded if critical information is missing.
    Otherwise returns 1-4 scenario branches.
    """
    # ── Check critical missing slots ──
    questions: list[str] = []

    if intent.marks is None and intent.actual_air is None:
        questions.append(
            "Please provide either your NEET marks (0-720) or your All India Rank (AIR)."
        )

    if intent.national_category is None:
        questions.append(
            "What is your national category? (General / OBC / SC / ST / EWS)"
        )

    if questions:
        return ClarificationNeeded(
            questions=tuple(questions),
            partial_intent=intent,
        )

    # ── Build scenarios ──
    scenarios: list[ScenarioSpec] = []

    # Determine home_state (default to generic if not given)
    home_state = intent.home_state or "Unknown"

    # Base parameters shared across scenarios
    base = dict(
        marks=intent.marks,
        actual_air=intent.actual_air,
        national_category=intent.national_category,  # type: ignore[arg-type]
        home_state=home_state,
        pwd=intent.pwd,
        target_year=intent.target_year,
    )

    # ── Primary MCC scenario ──
    course = intent.course_pref if intent.course_pref != "MBBS+BDS" else "MBBS"
    scenarios.append(
        ScenarioSpec(
            label=f"{course}, MCC AIQ ({intent.national_category})",
            description="Primary MCC All India Quota prediction",
            karnataka_interest=intent.karnataka_interest,
            karnataka_domicile=False,  # MCC doesn't use KEA domicile
            karnataka_category=None,
            course_pref=course,
            college_type_pref=intent.college_type_pref,
            **base,  # type: ignore[arg-type]
        )
    )

    # ── KEA scenarios (if Karnataka interest) ──
    if intent.karnataka_interest:
        kea_cat = intent.karnataka_category

        if intent.karnataka_domicile is True or intent.karnataka_domicile is None:
            # Branch: WITH domicile (confirmed or uncertain)
            domicile_label = (
                "confirmed" if intent.karnataka_domicile is True else "if domicile"
            )
            scenarios.append(
                ScenarioSpec(
                    label=f"{course}, KEA {kea_cat or 'GM'} ({domicile_label})",
                    description=(
                        f"Karnataka state counselling with "
                        f"{'confirmed' if intent.karnataka_domicile else 'assumed'} domicile"
                    ),
                    karnataka_interest=True,
                    karnataka_domicile=True,
                    karnataka_category=kea_cat,
                    course_pref=course,
                    college_type_pref=intent.college_type_pref,
                    **base,  # type: ignore[arg-type]
                )
            )

        if intent.karnataka_domicile is None:
            # Also branch: WITHOUT domicile (exploratory)
            scenarios.append(
                ScenarioSpec(
                    label=f"{course}, KEA GM (no domicile)",
                    description="Karnataka exploratory without domicile confirmation",
                    karnataka_interest=True,
                    karnataka_domicile=False,
                    karnataka_category=None,
                    course_pref=course,
                    college_type_pref=intent.college_type_pref,
                    **base,  # type: ignore[arg-type]
                )
            )

    # ── BDS backup scenario ──
    if intent.bds_backup and course == "MBBS":
        scenarios.append(
            ScenarioSpec(
                label=f"MBBS+BDS, MCC AIQ ({intent.national_category})",
                description="Backup scenario including BDS colleges",
                karnataka_interest=intent.karnataka_interest,
                karnataka_domicile=False,
                karnataka_category=None,
                course_pref="MBBS+BDS",
                college_type_pref=intent.college_type_pref,
                **base,  # type: ignore[arg-type]
            )
        )

    return scenarios
