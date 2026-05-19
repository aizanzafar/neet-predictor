"""Post-process parsed CSVs to fix category/quota normalization.

This is faster than re-parsing all PDFs when only mappings change.
Run after batch parsing to ensure consistent category names.

Usage:
    python pipelines/postprocess_categories.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neet_predictor.config import PARSED_MCC_DIR

# Standard MCC category names (post-2020)
_CATEGORY_NORMALIZE = {
    # 2020 space-separated abbreviations
    "GN": "Open",
    "GN PwD": "PwD Open",
    "GN NO": "General",
    "GNNO": "General",
    "GNPH": "PwD Open",
    "OBC PwD": "PwD OBC",
    "OBCPH": "PwD OBC",
    "SC PwD": "PwD SC",
    "SCPH": "PwD SC",
    "ST PwD": "PwD ST",
    "STPH": "PwD ST",
    "EW PwD": "PwD EWS",
    "EW NO": "EWS",
    "EWNO": "EWS",
    "EWPH": "PwD EWS",
    "EWS PwD": "PwD EWS",
    # Later years variants
    "Open PwD": "PwD Open",
    "OBC-NCL": "OBC",
}

_QUOTA_NORMALIZE = {
    "AI": "All India",
    "AIQ": "All India",
    "OS": "Open Seat Quota",
    "IP": "Internal",
}


def postprocess_mcc_csv(csv_path: Path) -> int:
    """Apply category normalization to a parsed MCC CSV. Returns number of changes."""
    df = pd.read_csv(csv_path)
    changes = 0

    # Only apply abbreviation mapping to 2020 data
    if "year" in df.columns and (df["year"] == 2020).any():
        for col in ["seat_category", "candidate_category"]:
            if col in df.columns:
                # Strip priority suffix first: "GN (Priority: 5B)" → "GN"
                priority_mask = df[col].str.contains(r"\(Priority:", na=False)
                if priority_mask.any():
                    df.loc[priority_mask, col] = df.loc[priority_mask, col].str.replace(
                        r"\s*\(Priority:.*?\)", "", regex=True
                    ).str.strip()
                    changes += priority_mask.sum()

                # Then apply category mapping
                mask = df[col].isin(_CATEGORY_NORMALIZE.keys())
                if mask.any():
                    df.loc[mask, col] = df.loc[mask, col].map(_CATEGORY_NORMALIZE)
                    changes += mask.sum()

        if "allotted_quota" in df.columns:
            mask = df["allotted_quota"].isin(_QUOTA_NORMALIZE.keys())
            if mask.any():
                df.loc[mask, "allotted_quota"] = df.loc[mask, "allotted_quota"].map(_QUOTA_NORMALIZE)
                changes += mask.sum()

    if changes > 0:
        df.to_csv(csv_path, index=False)

    return changes


def main():
    mcc_dir = PARSED_MCC_DIR
    if not mcc_dir.exists():
        print("No parsed MCC directory found.")
        return

    csv_files = sorted(mcc_dir.glob("mcc_2020_*.csv"))
    if not csv_files:
        print("No 2020 MCC CSVs to post-process.")
        return

    total_changes = 0
    for f in csv_files:
        changes = postprocess_mcc_csv(f)
        if changes:
            print(f"  {f.name}: {changes} cells normalized")
            total_changes += changes
        else:
            print(f"  {f.name}: no changes needed")

    print(f"\nTotal changes: {total_changes}")


if __name__ == "__main__":
    main()
