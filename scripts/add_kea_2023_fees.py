"""Add 2023 fee data to colleges.csv from allotment-extracted fees."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from neet_predictor.config import CURATED_DIR
from scripts.integrate_kea_cutoffs import build_kea_code_to_college_id

fees_df = pd.read_csv("data/parsed/kea_cutoffs/kea_2023_fees.csv")
print(f"Fee entries: {len(fees_df)}")

cutoff_df = pd.read_csv("data/parsed/kea_cutoffs/kea_2023_closing_ranks.csv")
aliases_df = pd.read_csv(CURATED_DIR / "college_aliases.csv")
mapping, _ = build_kea_code_to_college_id(cutoff_df, aliases_df)

colleges_df = pd.read_csv(CURATED_DIR / "colleges.csv")

updated = 0
for _, row in fees_df.iterrows():
    code = row["college_code"]
    college_id = mapping.get(code)
    if college_id is None:
        continue
    
    fee = row["fee"]
    course = row["course"]
    
    idx = colleges_df[colleges_df["college_id"] == college_id].index
    if len(idx) == 0:
        continue
    
    if "GOVT" in course:
        colleges_df.loc[idx[0], "fee_govt_quota"] = fee
    elif "PRIV" in course:
        colleges_df.loc[idx[0], "fee_private"] = fee
    updated += 1

print(f"Updated {updated} fee entries in colleges.csv")
colleges_df.to_csv(CURATED_DIR / "colleges.csv", index=False)

ka = colleges_df[colleges_df["state"] == "Karnataka"]
govt_count = ka["fee_govt_quota"].notna().sum()
priv_count = ka["fee_private"].notna().sum()
print(f"Karnataka with govt fee: {govt_count}")
print(f"Karnataka with priv fee: {priv_count}")
