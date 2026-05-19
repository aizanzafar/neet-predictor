"""Parse KEA 2023 remaining seat and fee data."""

import re
from pathlib import Path

import pdfplumber

BASE = Path("data/raw/kea_karnataka/2023")


def parse_seat_matrix_page(text):
    """Parse a seat matrix page."""
    entries = []
    lines = text.split("\n")
    for line in lines[2:]:  # skip header lines
        m = re.match(r"([MD]\d{3}\w{2})\s+(.+?)(\s+\d+)+\s*$", line)
        if m:
            code_full = m.group(1)
            code = code_full[:4]
            suffix = code_full[4:]
            numbers = re.findall(r"\d+", line[len(code_full):])
            if numbers:
                total = int(numbers[-1])
                entries.append({
                    "code": code,
                    "suffix": suffix,
                    "total_seats": total,
                })
    return entries


def main():
    r2_files = [
        (BASE / "R2" / "medi_cutoff_gen.pdf", "GEN"),
        (BASE / "R2" / "medi_cutoff_hk.pdf", "HK"),
        (BASE / "R2" / "medi_cutoff_priv.pdf", "PRIV"),
        (BASE / "R2" / "medi_cutoff_nri_oth.pdf", "NRI"),
    ]

    mopup_files = [
        (BASE / "MOPUP" / "medi_cutoff_gen.pdf", "GEN"),
        (BASE / "MOPUP" / "medi_cutoff_hk.pdf", "HK"),
        (BASE / "MOPUP" / "medi_cutoff_priv.pdf", "PRIV"),
        (BASE / "MOPUP" / "medi_cutoff_nri_oth.pdf", "NRI"),
        (BASE / "MOPUP" / "medi_cutoff_spl.pdf", "SPL"),
    ]

    all_seats = []
    for pdf_path, quota_type in r2_files:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text(x_tolerance=1)
            if text:
                entries = parse_seat_matrix_page(text)
                for e in entries:
                    e["round"] = "R2"
                    e["quota_type"] = quota_type
                all_seats.extend(entries)
                print(f"{pdf_path.name} ({quota_type}): {len(entries)} colleges")

    for pdf_path, quota_type in mopup_files:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text(x_tolerance=1)
            if text:
                entries = parse_seat_matrix_page(text)
                for e in entries:
                    e["round"] = "MOPUP"
                    e["quota_type"] = quota_type
                all_seats.extend(entries)
                print(f"{pdf_path.name} ({quota_type}): {len(entries)} colleges")

    print(f"\nTotal seat entries: {len(all_seats)}")
    total_by_round = {}
    for s in all_seats:
        total_by_round.setdefault(s["round"], 0)
        total_by_round[s["round"]] += s["total_seats"]
    print(f"Total seats by round: {total_by_round}")

    # Extract fee data directly from R2 allotment
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import pandas as pd
    from scripts.parse_kea_2023_allotments import parse_allotment_pdf
    
    fee_entries = []
    seen_keys = set()
    r2_allot = BASE / "R2" / "allotment_r2_medical.pdf"
    if r2_allot.exists():
        print("\nExtracting fees from R2 allotment...")
        entries = parse_allotment_pdf(r2_allot, "R2")
        for e in entries:
            if e["fees"]:
                key = (e["college_code"], e["course"])
                if key not in seen_keys:
                    seen_keys.add(key)
                    fee_entries.append({
                        "college_code": e["college_code"],
                        "course": e["course"],
                        "fee": e["fees"],
                    })
    
    print(f"\nFee data: {len(fee_entries)} college-course combinations")
    
    # Save fee data
    out = Path("data/parsed/kea_cutoffs/kea_2023_fees.csv")
    pd.DataFrame(fee_entries).to_csv(out, index=False)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
