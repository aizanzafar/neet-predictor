"""Parse KEA 2022 seat matrix PDFs into structured CSV.

Seat matrix shows available seats per category per college.
Files: medical_g.pdf (govt general), medical_g_hk.pdf (govt HK),
       medical_g_spl.pdf (govt special), medical_p.pdf (private),
       medical_n.pdf (NRI), medical_q.pdf (others)
"""
import pdfplumber
import csv
import re
from pathlib import Path

GEN_CATEGORIES = ["1G", "1K", "1R", "2AG", "2AK", "2AR", "2BG", "2BK", "2BR",
                  "3AG", "3AK", "3AR", "3BG", "3BK", "3BR", "GM", "GMK", "GMR",
                  "SCG", "SCK", "SCR", "STG", "STK", "STR"]

HK_CATEGORIES = ["1H", "1KH", "1RH", "2AH", "2AKH", "2ARH", "2BH", "2BKH", "2BRH",
                 "3AH", "3AKH", "3ARH", "3BH", "3BKH", "3BRH", "GMH", "GMKH", "GMRH",
                 "SCH", "SCKH", "SCRH", "STH", "STKH", "STRH"]


def parse_seat_matrix_pdf(pdf_path: Path, seat_type: str, round_name: str) -> list[dict]:
    """Parse a seat matrix PDF using table extraction."""
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                # Find header row
                header_row = None
                data_start = 0
                for idx, row in enumerate(table):
                    if row and any(c and "COLLEGE" in str(c) for c in row):
                        header_row = row
                        data_start = idx + 1
                        break
                if not header_row:
                    continue

                # Extract category columns from header
                cats = []
                for cell in header_row[1:]:  # skip first col (college)
                    if cell and cell.strip() and cell.strip() != "TOTAL":
                        cats.append(cell.strip())
                    elif cell is None:
                        # Skip None columns (formatting artifact)
                        continue

                # Parse data rows
                for row in table[data_start:]:
                    if not row or not row[0]:
                        continue
                    college_cell = row[0].strip()
                    # Extract code and name: M001MG College Name
                    m = re.match(r"^(M\d{3}|D\d{3})(\w*)\s+(.+)$", college_cell)
                    if not m:
                        continue
                    code = m.group(1)
                    quota_suffix = m.group(2)  # MG, MP, MN, etc.
                    name = m.group(3).strip()

                    # Get values, skipping None columns
                    values = []
                    for cell in row[1:]:
                        if cell is None:
                            continue
                        values.append(cell.strip() if cell else "")

                    # Last value is TOTAL
                    total = 0
                    if values and values[-1].isdigit():
                        total = int(values[-1])
                        values = values[:-1]

                    # Map values to categories
                    for i, val in enumerate(values):
                        if val and val.isdigit() and int(val) > 0 and i < len(cats):
                            rows.append({
                                "year": 2022,
                                "round": round_name,
                                "college_code": code,
                                "college_name": name,
                                "seat_type": seat_type,
                                "category": cats[i],
                                "seats": int(val),
                            })
                    # Also store total
                    if total > 0:
                        rows.append({
                            "year": 2022,
                            "round": round_name,
                            "college_code": code,
                            "college_name": name,
                            "seat_type": seat_type,
                            "category": "TOTAL",
                            "seats": total,
                        })
    return rows


def main():
    base = Path("data/raw/kea_karnataka/2022")
    out_dir = Path("data/parsed/kea_seat_matrix")
    out_dir.mkdir(parents=True, exist_ok=True)

    configs = [
        (base / "R1" / "medical_g.pdf", "GOVT", "R1"),
        (base / "R1" / "medical_g_hk.pdf", "GOVT_HK", "R1"),
        (base / "R1" / "medical_g_spl.pdf", "GOVT_SPL", "R1"),
        (base / "R1" / "medical_p.pdf", "PRIVATE", "R1"),
        (base / "R1" / "medical_n.pdf", "NRI", "R1"),
        (base / "R1" / "medical_q.pdf", "OTHERS", "R1"),
        (base / "R2" / "medical_g.pdf", "GOVT", "R2"),
        (base / "R2" / "medical_g_hk.pdf", "GOVT_HK", "R2"),
        (base / "R2" / "medical_g_spl.pdf", "GOVT_SPL", "R2"),
        (base / "R2" / "medical_p.pdf", "PRIVATE", "R2"),
        (base / "R2" / "medical_n.pdf", "NRI", "R2"),
        (base / "R2" / "medical_q.pdf", "OTHERS", "R2"),
    ]

    all_rows = []
    for pdf_path, seat_type, round_name in configs:
        if not pdf_path.exists():
            print(f"SKIP: {pdf_path}")
            continue
        rows = parse_seat_matrix_pdf(pdf_path, seat_type, round_name)
        print(f"{pdf_path.name} ({round_name} {seat_type}): {len(rows)} entries")
        all_rows.extend(rows)

    print(f"\nTotal: {len(all_rows)} seat entries")

    out_path = out_dir / "kea_2022_seat_matrix.csv"
    fieldnames = ["year", "round", "college_code", "college_name", "seat_type", "category", "seats"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Saved: {out_path}")

    # Summary
    colleges = set(r["college_code"] for r in all_rows)
    print(f"Colleges: {len(colleges)}")
    for st in sorted(set(r["seat_type"] for r in all_rows)):
        st_rows = [r for r in all_rows if r["seat_type"] == st]
        total_seats = sum(r["seats"] for r in st_rows if r["category"] == "TOTAL")
        print(f"  {st}: {total_seats} total seats")


if __name__ == "__main__":
    main()
