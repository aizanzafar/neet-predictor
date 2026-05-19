"""Parse KEA 2022 fees PDF (tabular format)."""
import pdfplumber
import csv
import re
from pathlib import Path

pdf = pdfplumber.open("data/raw/kea_karnataka/2022/R2/fees.pdf")
full_text = ""
for page in pdf.pages:
    text = page.extract_text(x_tolerance=1)
    if text:
        full_text += text + "\n"
pdf.close()

lines = full_text.split("\n")
rows = []
for line in lines:
    line = line.strip()
    if not line or line.startswith("COLLCD"):
        continue
    # Match: code + name + 1-4 fee numbers at end
    m = re.match(r"^(M\d{3}|D\d{3})\s+(.+?)(\d[\d\s]+)$", line)
    if m:
        code = m.group(1)
        name = m.group(2).strip().rstrip(",")
        nums_str = m.group(3).strip()
        nums = nums_str.split()
        quotas = ["GOVT", "PRIVATE", "NRI", "OTHERS"]
        for i, val in enumerate(nums):
            if i < len(quotas):
                rows.append({
                    "year": 2022, "round": "R2",
                    "college_code": code, "college_name": name,
                    "quota": quotas[i], "fee": int(val),
                })

colleges = set(r["college_code"] for r in rows)
print(f"Parsed {len(rows)} fee records from {len(colleges)} colleges")

out = Path("data/parsed/kea_fees/kea_2022_fees.csv")
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["year", "round", "college_code", "college_name", "quota", "fee"])
    w.writeheader()
    w.writerows(rows)
print(f"Saved: {out}")
for r in rows[:5]:
    print(f"  {r['college_code']} {r['quota']}: {r['fee']:,}")
