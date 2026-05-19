"""Parse KEA fee structure PDF into structured CSV.

Extracts college-wise, course-wise, quota-wise fee data from the KEA fees PDF.

Usage:
    python scripts/parse_kea_fees.py data/raw/kea_karnataka/2021/R1/fees.pdf --year 2021
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber required. pip install pdfplumber")
    sys.exit(1)

import csv


def parse_fees_pdf(pdf_path: Path, year: int) -> list[dict]:
    """Parse KEA fee structure PDF into list of fee records."""
    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"Parsing: {pdf_path.name} ({len(pdf.pages)} pages)")
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1)
            if text:
                full_text += text + "\n"

    lines = full_text.split("\n")
    current_college_code = None
    current_college_name = None
    current_discipline = "MEDICAL"  # default
    current_quotas = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect discipline header (MEDICAL / DENTAL)
        if line == "MEDICAL":
            current_discipline = "MEDICAL"
            i += 1
            continue
        if line == "DENTAL":
            current_discipline = "DENTAL"
            i += 1
            continue

        # College header: e.g. "M001-Bangalore Medical College,Bangalore"
        college_match = re.match(r"^([MD]\d{3})-(.+)$", line)
        if college_match:
            current_college_code = college_match.group(1)
            current_college_name = college_match.group(2).strip()
            i += 1
            continue

        # Type line with quotas: "Type G-Govt. P-Priv. N-NRI Q-Others"
        if line.startswith("Type "):
            current_quotas = []
            # Parse quota types from this line
            quota_matches = re.findall(r"([GPNQ])-(\w+\.?)", line)
            for code, label in quota_matches:
                quota_map = {"G": "GOVT", "P": "PRIV", "N": "NRI", "Q": "OTHERS"}
                current_quotas.append(quota_map.get(code, code))
            i += 1
            # Skip "Course Quota Quota Quota Quota" header line
            if i < len(lines) and "Course" in lines[i] and "Quota" in lines[i]:
                i += 1
            continue

        # Fee data line: "M-MBBS 59,850" or "M-MBBS 1,41,196 9,94,406 36,87,450 36,87,450"
        # Also handles "D-BDS" prefix
        course_match = re.match(r"^([MD])-(\w+)\s+(.+)$", line)
        if course_match and current_college_code:
            course = course_match.group(2)  # MBBS or BDS
            fees_str = course_match.group(3)
            # Parse Indian comma-separated numbers (e.g., "1,41,196")
            fee_values = re.findall(r"[\d,]+", fees_str)
            fee_amounts = []
            for fv in fee_values:
                try:
                    fee_amounts.append(int(fv.replace(",", "")))
                except ValueError:
                    continue

            # Derive discipline from college code (M=MEDICAL, D=DENTAL)
            discipline = "DENTAL" if current_college_code.startswith("D") else "MEDICAL"

            # Map fees to quotas
            for idx, fee in enumerate(fee_amounts):
                if idx < len(current_quotas):
                    seat_type = current_quotas[idx]
                else:
                    seat_type = "UNKNOWN"
                rows.append({
                    "year": year,
                    "college_code": current_college_code,
                    "college_name": current_college_name,
                    "discipline": discipline,
                    "course": course,
                    "seat_type": seat_type,
                    "fee_per_annum": fee,
                })
            i += 1
            continue

        i += 1

    return rows


def parse_mopup_seats(pdf_path: Path, year: int) -> list[dict]:
    """Parse mop-up seat availability PDF into structured records."""
    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"Parsing: {pdf_path.name} ({len(pdf.pages)} pages)")
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1)
            if text:
                full_text += text + "\n"

    lines = full_text.split("\n")

    for line in lines:
        # Match: M002MQ Dr.AMC, Bangalore 0 20 20 3687450
        match = re.match(
            r"^([MD]\d{3})([A-Z]{2})\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$",
            line.strip()
        )
        if match:
            college_code = match.group(1)
            quota_code = match.group(2)  # MQ = Medical Others(Q)
            college_name = match.group(3).strip().rstrip(",")
            nri_seats = int(match.group(4))
            oth_seats = int(match.group(5))
            total_seats = int(match.group(6))
            fee = int(match.group(7))

            # Determine course from code suffix
            course = "MBBS" if college_code.startswith("M") else "BDS"

            rows.append({
                "year": year,
                "round": "MOPUP",
                "college_code": college_code,
                "college_name": college_name,
                "course": course,
                "seat_type": "OTHERS",
                "nri_seats": nri_seats,
                "other_seats": oth_seats,
                "total_seats": total_seats,
                "fee_per_annum": fee,
            })

    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse KEA fee/mopup PDFs")
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--year", type=int, default=2021)
    parser.add_argument("--type", choices=["fees", "mopup"], default="fees")
    parser.add_argument("--output", "-o", type=Path, default=None)
    args = parser.parse_args()

    if not args.pdf_path.exists():
        print(f"ERROR: {args.pdf_path} not found")
        sys.exit(1)

    if args.type == "fees":
        data = parse_fees_pdf(args.pdf_path, args.year)
        default_out = Path(f"data/parsed/kea_fees/kea_{args.year}_fees.csv")
        fieldnames = ["year", "college_code", "college_name", "discipline", "course", "seat_type", "fee_per_annum"]
    else:
        data = parse_mopup_seats(args.pdf_path, args.year)
        default_out = Path(f"data/parsed/kea_seats/kea_{args.year}_mopup_seats.csv")
        fieldnames = ["year", "round", "college_code", "college_name", "course", "seat_type", "nri_seats", "other_seats", "total_seats", "fee_per_annum"]

    out_path = args.output or default_out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(data)

    print(f"Wrote {len(data)} records to {out_path}")
