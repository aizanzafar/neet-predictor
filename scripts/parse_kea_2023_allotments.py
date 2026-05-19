"""Parse KEA 2023 allotment PDFs to derive closing ranks for R2/Mopup.

The R2 and Mopup rounds don't have separate cutoff PDFs (those are seat matrices).
Instead, we derive closing ranks from allotment lists: max rank per college/category = closing rank.

Also extracts fee data per college/course.

Usage:
    python scripts/parse_kea_2023_allotments.py
"""

import csv
import re
from pathlib import Path

import pdfplumber

BASE = Path("data/raw/kea_karnataka/2023")
OUT_DIR = Path("data/parsed/kea_cutoffs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Pattern: SL.NO RANK COLLEGE_CODE(+suffix) ... COURSE CATEGORY FEES
# Examples:
#   "1 326 M051MG MBBS-GOVT. GM 144496"
#   "6 802 M031MG Karnataka Institute of Medical Sciences,Vidyanagar,Hubli MBBS-GOVT. GM 60100"
DATA_PAT = re.compile(
    r"^\d+\s+(\d+)\s+([MD]\d{3})(\w{2})\s+.*?"
    r"(MBBS|BDS)[-\s]*(GOVT|PRIV)\.?\s+"
    r"([A-Z0-9]+)\s+(\d+)\s*$"
)

# R1 allotment format (no fees, no course on data line):
# "1 127 M001MG Bangalore Medical College,...,Bangalore GM"
R1_PAT = re.compile(
    r"^\d+\s+(\d+)\s+([MD]\d{3})(\w{2})\s+.*?\s+([A-Z0-9]+)\s*$"
)


def parse_allotment_pdf(pdf_path: Path, round_name: str) -> list[dict]:
    """Parse an allotment PDF and return entries with rank, college, category, fees."""
    entries = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1)
            if not text:
                continue
            for line in text.split("\n"):
                line = line.strip()
                m = DATA_PAT.match(line)
                if m:
                    rank = int(m.group(1))
                    code = m.group(2)
                    suffix = m.group(3)
                    course_type = m.group(4)
                    seat_type = m.group(5)
                    category = m.group(6)
                    fees = int(m.group(7))
                    
                    course = f"{course_type}-{seat_type}."
                    entries.append({
                        "rank": rank,
                        "college_code": code,
                        "suffix": suffix,
                        "course": course,
                        "category": category,
                        "fees": fees,
                        "round": round_name,
                    })
    return entries


def parse_r1_allotment(pdf_path: Path) -> list[dict]:
    """Parse R1 allotment (different format - no fees, no course on data line)."""
    entries = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1)
            if not text:
                continue
            for line in text.split("\n"):
                line = line.strip()
                m = R1_PAT.match(line)
                if m:
                    rank = int(m.group(1))
                    code = m.group(2)
                    suffix = m.group(3)
                    category = m.group(4)
                    
                    # Infer course from suffix
                    course_type = "MBBS" if code.startswith("M") else "BDS"
                    seat_type = "GOVT" if suffix.endswith("G") else "PRIV"
                    course = f"{course_type}-{seat_type}."
                    
                    entries.append({
                        "rank": rank,
                        "college_code": code,
                        "suffix": suffix,
                        "course": course,
                        "category": category,
                        "fees": None,
                        "round": "R1",
                    })
    return entries


def derive_closing_ranks(entries: list[dict]) -> list[dict]:
    """Derive closing ranks: max rank per college/course/category."""
    from collections import defaultdict
    
    groups = defaultdict(lambda: {"max_rank": 0, "count": 0, "fees": None})
    
    for e in entries:
        key = (e["college_code"], e["course"], e["category"], e["round"])
        g = groups[key]
        if e["rank"] > g["max_rank"]:
            g["max_rank"] = e["rank"]
        g["count"] += 1
        if e["fees"] and not g["fees"]:
            g["fees"] = e["fees"]
    
    closing = []
    for (code, course, category, round_name), g in groups.items():
        closing.append({
            "year": 2023,
            "round": round_name,
            "college_code": code,
            "college_name": "",  # Will be filled from cutoff data
            "course": course,
            "seat_type": "GOVT" if "GOVT" in course else "PRIV",
            "category": category,
            "closing_rank": g["max_rank"],
        })
    
    return closing


def main():
    # Parse R2 allotments
    r2_files = [
        (BASE / "R2" / "allotment_r2_medical.pdf", "R2"),
        (BASE / "R2" / "allotment_r2_dental.pdf", "R2"),
    ]
    
    mopup_files = [
        (BASE / "MOPUP" / "allotment_mopup.pdf", "MOPUP"),
    ]
    
    stray_files = [
        (BASE / "STRAY" / "allotment_stray.pdf", "STRAY"),
    ]
    
    all_entries = []
    
    for pdf_path, round_name in r2_files + mopup_files + stray_files:
        if not pdf_path.exists():
            print(f"SKIP: {pdf_path}")
            continue
        print(f"Parsing: {pdf_path.name} ({round_name})...", end=" ")
        entries = parse_allotment_pdf(pdf_path, round_name)
        print(f"{len(entries)} entries")
        all_entries.extend(entries)
    
    print(f"\nTotal allotment entries: {len(all_entries)}")
    
    # Derive closing ranks
    closing = derive_closing_ranks(all_entries)
    print(f"Derived closing ranks: {len(closing)} rows")
    
    # Save derived closing ranks
    out_path = OUT_DIR / "kea_2023_derived_closing_ranks.csv"
    fieldnames = ["year", "round", "college_code", "college_name", "course", "seat_type", "category", "closing_rank"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(closing)
    print(f"Saved: {out_path}")
    
    # Summary by round
    from collections import Counter
    rounds = Counter(e["round"] for e in all_entries)
    print(f"\nEntries by round: {dict(rounds)}")
    
    colleges = set(e["college_code"] for e in all_entries)
    print(f"Unique colleges: {len(colleges)}")
    
    # Fee data extraction
    fee_data = {}
    for e in all_entries:
        if e["fees"]:
            key = (e["college_code"], e["course"])
            if key not in fee_data:
                fee_data[key] = e["fees"]
    
    print(f"\nFee data: {len(fee_data)} college-course combinations")
    # Show sample
    for (code, course), fee in list(fee_data.items())[:5]:
        print(f"  {code} {course}: {fee}")


if __name__ == "__main__":
    main()
