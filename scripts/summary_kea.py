"""Quick summary of KEA data state."""
import pandas as pd

df = pd.read_csv("data/curated/closing_ranks.csv", dtype={"quota": str, "statuses_included": str})
kea = df[df["authority"] == "KEA"]

print("=== KEA CLOSING RANKS SUMMARY ===")
print(f"Total KEA rows: {len(kea)}")
print()
for year in sorted(kea["year"].unique()):
    yr = kea[kea["year"] == year]
    methods = yr["derivation_method"].value_counts().to_dict()
    rounds = sorted(yr["round"].unique())
    print(f"  {year}: {len(yr):,} rows | rounds={rounds} | methods={methods}")

print()
print(f"Total closing_ranks.csv: {len(df):,} rows")
mcc_count = len(df[df["authority"] == "MCC"])
print(f"MCC: {mcc_count:,} | KEA: {len(kea):,}")
