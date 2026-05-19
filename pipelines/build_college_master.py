"""Build college master table from parsed allotment CSVs.

Extracts unique college names, normalizes them, and creates the colleges.csv.
Also populates college_aliases.csv with all observed name variants.
"""

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neet_predictor.config import CURATED_DIR, PARSED_MCC_DIR, PARSED_KEA_DIR
from neet_predictor.dataio.normalizer import normalize_college_name


# Indian states/UTs for extraction from college names
_INDIAN_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
    "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand",
    "west bengal", "delhi (nct)", "delhi", "puducherry", "chandigarh",
    "jammu and kashmir", "ladakh", "andaman and nicobar",
    "dadra and nagar haveli", "daman and diu", "lakshadweep",
}

# City → state mapping for common medical college cities
_CITY_TO_STATE = {
    "new delhi": "Delhi", "delhi": "Delhi",
    "mumbai": "Maharashtra", "pune": "Maharashtra", "nagpur": "Maharashtra",
    "chennai": "Tamil Nadu", "madurai": "Tamil Nadu", "coimbatore": "Tamil Nadu",
    "kolkata": "West Bengal",
    "bangalore": "Karnataka", "bengaluru": "Karnataka", "mangalore": "Karnataka",
    "hubli": "Karnataka", "mysore": "Karnataka", "mysuru": "Karnataka",
    "bagalkot": "Karnataka", "belgaum": "Karnataka", "davangere": "Karnataka",
    "shimoga": "Karnataka", "bellary": "Karnataka", "raichur": "Karnataka",
    "gulbarga": "Karnataka", "bidar": "Karnataka", "dharwad": "Karnataka",
    "mandya": "Karnataka", "hassan": "Karnataka",
    "hyderabad": "Telangana", "warangal": "Telangana",
    "lucknow": "Uttar Pradesh", "varanasi": "Uttar Pradesh", "agra": "Uttar Pradesh",
    "allahabad": "Uttar Pradesh", "prayagraj": "Uttar Pradesh",
    "jaipur": "Rajasthan", "jodhpur": "Rajasthan", "ajmer": "Rajasthan",
    "bhopal": "Madhya Pradesh", "indore": "Madhya Pradesh", "gwalior": "Madhya Pradesh",
    "patna": "Bihar", "muzaffarpur": "Bihar", "darbhanga": "Bihar",
    "ahmedabad": "Gujarat", "vadodara": "Gujarat", "surat": "Gujarat", "rajkot": "Gujarat",
    "chandigarh": "Chandigarh", "thiruvananthapuram": "Kerala", "kochi": "Kerala",
    "trivandrum": "Kerala", "calicut": "Kerala", "kozhikode": "Kerala",
    "thrissur": "Kerala",
    "bhubaneswar": "Odisha", "cuttack": "Odisha",
    "raipur": "Chhattisgarh", "ranchi": "Jharkhand",
    "dehradun": "Uttarakhand", "rishikesh": "Uttarakhand",
    "shimla": "Himachal Pradesh",
    "jammu": "Jammu and Kashmir", "srinagar": "Jammu and Kashmir",
    "guwahati": "Assam", "dibrugarh": "Assam",
    "imphal": "Manipur", "shillong": "Meghalaya", "gangtok": "Sikkim",
    "agartala": "Tripura", "aizawl": "Mizoram", "kohima": "Nagaland",
    "itanagar": "Arunachal Pradesh",
    "puducherry": "Puducherry", "pondicherry": "Puducherry",
    "port blair": "Andaman and Nicobar",
    "panaji": "Goa", "margao": "Goa",
    "amritsar": "Punjab", "ludhiana": "Punjab", "patiala": "Punjab",
    "rohtak": "Haryana", "hisar": "Haryana", "faridabad": "Haryana",
    "visakhapatnam": "Andhra Pradesh", "vijayawada": "Andhra Pradesh",
    "tirupati": "Andhra Pradesh", "guntur": "Andhra Pradesh",
    "kurnool": "Andhra Pradesh", "kakinada": "Andhra Pradesh",
}


def _extract_state(college_name: str, authority: str) -> str:
    """Extract state from college name. Returns state name or 'Unknown'."""
    if authority == "KEA":
        return "Karnataka"

    name_lower = college_name.lower()

    # Try matching Indian state names in the college name text
    for state in sorted(_INDIAN_STATES, key=len, reverse=True):
        if state in name_lower:
            return state.title().replace("(Nct)", "(NCT)")

    # Try matching city names
    for city, state in _CITY_TO_STATE.items():
        if city in name_lower:
            return state

    return "Unknown"


def build_college_master(allotments_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build colleges and college_aliases from allotment data.

    Args:
        allotments_df: DataFrame with at minimum 'college_raw' and 'authority' columns.

    Returns:
        Tuple of (colleges_df, aliases_df).
    """
    if allotments_df is None or allotments_df.empty:
        print("No allotment data. Cannot build college master.")
        return pd.DataFrame(), pd.DataFrame()

    if "college_raw" not in allotments_df.columns:
        print("ERROR: 'college_raw' column not found in allotments data.")
        return pd.DataFrame(), pd.DataFrame()

    # Get unique raw college names with their authority
    raw_names = allotments_df[["college_raw", "authority"]].dropna(subset=["college_raw"])
    raw_names = raw_names.drop_duplicates()

    # Normalize each name
    raw_names["name_normalized"] = raw_names["college_raw"].apply(normalize_college_name)

    # Group by normalized name to get unique colleges
    unique_colleges = raw_names.groupby("name_normalized").agg(
        college_name=("college_raw", "first"),  # Use first raw name as canonical
        authority=("authority", lambda x: "BOTH" if x.nunique() > 1 else x.iloc[0]),
    ).reset_index()

    # Extract state from college names
    unique_colleges["state"] = unique_colleges.apply(
        lambda row: _extract_state(row["college_name"], row["authority"]), axis=1
    )

    # Build colleges DataFrame
    colleges = pd.DataFrame({
        "college_id": range(1, len(unique_colleges) + 1),
        "college_code": None,
        "college_name": unique_colleges["college_name"],
        "name_normalized": unique_colleges["name_normalized"],
        "state": unique_colleges["state"],
        "city": None,
        "ownership": "government",  # Default; must be corrected
        "counselling": unique_colleges["authority"],
        "courses": None,
        "annual_intake": None,
        "fee_govt_quota": None,
        "fee_private": None,
        "nmc_approved": 1,
        "source_id": None,
        "notes": "auto-generated from allotment data; needs manual review",
    })

    # Build aliases DataFrame — every raw variant maps to a college_id
    norm_to_id = dict(zip(unique_colleges["name_normalized"], range(1, len(unique_colleges) + 1)))

    aliases = pd.DataFrame({
        "alias_id": range(1, len(raw_names) + 1),
        "college_id": raw_names["name_normalized"].map(norm_to_id).values,
        "alias_name": raw_names["college_raw"].values,
        "alias_normalized": raw_names["name_normalized"].values,
        "authority": raw_names["authority"].values,
        "year": None,
        "source_id": None,
        "notes": None,
    })

    print(f"Built {len(colleges)} unique colleges from {len(raw_names)} raw name variants")
    return colleges, aliases


def main():
    # Try to load from curated allotments
    allotments_path = CURATED_DIR / "allotments.csv"
    if not allotments_path.exists() or pd.read_csv(allotments_path).empty:
        # Try parsed directories
        parsed_files = list(PARSED_MCC_DIR.glob("*.csv")) + list(PARSED_KEA_DIR.glob("*.csv"))
        if not parsed_files:
            print("ERROR: No allotment data found. Parse PDFs first.")
            sys.exit(1)
        dfs = [pd.read_csv(f) for f in parsed_files]
        allotments_df = pd.concat(dfs, ignore_index=True)
    else:
        allotments_df = pd.read_csv(allotments_path)

    colleges, aliases = build_college_master(allotments_df)

    if not colleges.empty:
        colleges.to_csv(CURATED_DIR / "colleges.csv", index=False)
        print(f"Saved colleges.csv ({len(colleges)} rows)")

    if not aliases.empty:
        aliases.to_csv(CURATED_DIR / "college_aliases.csv", index=False)
        print(f"Saved college_aliases.csv ({len(aliases)} rows)")


if __name__ == "__main__":
    main()
