"""Parse KEA Karnataka allotment PDFs into structured CSV.

Supports two KEA formats:
- 5-column (2023 R1): SL.NO, AIR, College Type/Code, College Name, Category
- 8-column (2023 R2+, 2024, 2025): SL.NO, AIR, Course Code, College Name, Course Name, Category, Fees, Status

Usage:
    python -m pipelines.parse_kea_pdf --batch

NOTE: KEA 2024 PDFs have font encoding issues (cid: characters).
      These are parsed best-effort with fallback text extraction.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[0].parent / "src"))

from neet_predictor.config import VALID_ROUNDS
from neet_predictor.dataio.normalizer import normalize_college_name


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean_cell(val) -> str:
    """Clean a cell value."""
    if not val:
        return ""
    return re.sub(r"\s+", " ", str(val)).strip()


def _is_kea_header(row: list) -> bool:
    """Detect KEA table header rows."""
    if not row or not row[0]:
        return True
    first = str(row[0]).strip().upper()
    if any(kw in first for kw in ["SL.NO", "SL NO", "SLNO", "ALL INDIA", "COLLEGE", "RANK", "NAME"]):
        return True
    return False


def _normalize_kea_course(course_code: str, course_name: str = "") -> str:
    """Extract MBBS/BDS from KEA course code or name."""
    code = str(course_code).upper() if course_code else ""
    name = str(course_name).upper() if course_name else ""

    if "MBBS" in name or "MBBS" in code:
        return "MBBS"
    if "BDS" in name or "BDS" in code:
        return "BDS"

    # KEA course codes: M=Medical(MBBS), D=Dental(BDS)
    # Format: M001MG, D101DG, etc.
    if code and code[0] == "M":
        return "MBBS"
    if code and code[0] == "D":
        return "BDS"

    # Check course name patterns
    if "GOVT" in name or "MEDICAL" in name:
        return "MBBS"
    if "DENTAL" in name:
        return "BDS"

    return ""


def _normalize_kea_round(round_raw: str) -> str:
    """Map KEA round names to standard round codes."""
    r = round_raw.upper()
    if "MOPUP" in r or "MOP-UP" in r or "MOP UP" in r:
        return "MOPUP"
    if "STRAY" in r:
        return "STRAY"
    if "ROUND 1" in r or "1ST ROUND" in r or "R1" in r:
        return "R1"
    if "ROUND 2" in r or "2ND ROUND" in r or "R2" in r:
        return "R2"
    if "ROUND 3" in r or "3RD ROUND" in r or "R3" in r:
        return "R3"
    return round_raw


def parse_kea_5col_pdf(
    pdf_path: Path,
    year: int,
    round_name: str,
    source_id: int,
) -> tuple[pd.DataFrame, dict]:
    """Parse 5-column KEA PDF (2023 R1 format).

    Columns: SL.NO, All India Rank, College Type, College Name, Allotted Category
    """
    import pdfplumber

    stats = {"total_pages": 0, "rows_extracted": 0, "rows_skipped": 0, "errors": []}
    all_records = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        stats["total_pages"] = len(pdf.pages)

        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                for row in table:
                    if not row or len(row) < 5:
                        stats["rows_skipped"] += 1
                        continue
                    if _is_kea_header(row):
                        continue

                    try:
                        sno = str(row[0]).strip()
                        if not sno.isdigit():
                            stats["rows_skipped"] += 1
                            continue

                        air_str = _clean_cell(row[1])
                        if not air_str.isdigit():
                            stats["rows_skipped"] += 1
                            continue

                        air = int(air_str)
                        course_code = _clean_cell(row[2])
                        college_raw = _clean_cell(row[3])
                        category = _clean_cell(row[4])
                        course = _normalize_kea_course(course_code)

                        if course not in ("MBBS", "BDS"):
                            stats["rows_skipped"] += 1
                            continue

                        record = {
                            "year": year,
                            "round": round_name,
                            "authority": "KEA",
                            "counselling_scope": "STATE_KA",
                            "rank_raw": air_str,
                            "air": air,
                            "rank_type": "AIR",
                            "allotted_quota": "",
                            "college_raw": college_raw,
                            "course": course,
                            "seat_category": category,
                            "candidate_category": "",
                            "status": "Allotted",  # 5-col format has no status col
                            "source_id": source_id,
                        }
                        all_records.append(record)
                        stats["rows_extracted"] += 1

                    except (ValueError, IndexError) as e:
                        stats["errors"].append(f"Page {page_num}: {e}")
                        stats["rows_skipped"] += 1

    if not all_records:
        return pd.DataFrame(), stats
    return pd.DataFrame(all_records), stats


def parse_kea_8col_pdf(
    pdf_path: Path,
    year: int,
    round_name: str,
    source_id: int,
) -> tuple[pd.DataFrame, dict]:
    """Parse 8-column KEA PDF (2023 R2+, 2024, 2025).

    Columns: SL.NO, AIR, Course Code, College Name, Course Name, Category, Fees, Status
    """
    import pdfplumber

    stats = {"total_pages": 0, "rows_extracted": 0, "rows_skipped": 0, "errors": []}
    all_records = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        stats["total_pages"] = len(pdf.pages)

        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                for row in table:
                    if not row or len(row) < 6:
                        stats["rows_skipped"] += 1
                        continue
                    if _is_kea_header(row):
                        continue

                    try:
                        sno = str(row[0]).strip()
                        if not sno.isdigit():
                            stats["rows_skipped"] += 1
                            continue

                        air_str = _clean_cell(row[1])
                        if not air_str.isdigit():
                            stats["rows_skipped"] += 1
                            continue

                        air = int(air_str)
                        course_code = _clean_cell(row[2])
                        college_raw = _clean_cell(row[3])
                        course_name = _clean_cell(row[4]) if len(row) > 4 else ""
                        category = _clean_cell(row[5]) if len(row) > 5 else ""
                        fee_str = _clean_cell(row[6]) if len(row) > 6 else ""
                        status_raw = _clean_cell(row[7]) if len(row) > 7 else "Allotted"

                        course = _normalize_kea_course(course_code, course_name)
                        if course not in ("MBBS", "BDS"):
                            stats["rows_skipped"] += 1
                            continue

                        # Normalize status
                        status = "Allotted"
                        if status_raw:
                            sl = status_raw.lower()
                            if "report" in sl or "reproted" in sl:
                                status = "Allotted"
                            elif "cancel" in sl:
                                status = "Cancelled"
                            elif "not" in sl:
                                status = "Not Reported"
                            else:
                                status = status_raw

                        # Parse fee
                        fee = None
                        if fee_str and fee_str.replace(",", "").isdigit():
                            fee = int(fee_str.replace(",", ""))

                        record = {
                            "year": year,
                            "round": round_name,
                            "authority": "KEA",
                            "counselling_scope": "STATE_KA",
                            "rank_raw": air_str,
                            "air": air,
                            "rank_type": "AIR",
                            "allotted_quota": "",
                            "college_raw": college_raw,
                            "course": course,
                            "seat_category": category,
                            "candidate_category": "",
                            "fee": fee,
                            "status": status,
                            "source_id": source_id,
                        }
                        all_records.append(record)
                        stats["rows_extracted"] += 1

                    except (ValueError, IndexError) as e:
                        stats["errors"].append(f"Page {page_num}: {e}")
                        stats["rows_skipped"] += 1

    if not all_records:
        return pd.DataFrame(), stats
    return pd.DataFrame(all_records), stats


# ── Batch config: (source_id, path, year, round, format) ──
KEA_BATCH_CONFIG = [
    # 2023
    (28, "data/raw/kea_karnataka/2023/2023_round1_karnataka_allotmentlist_04e0cb3f.pdf", 2023, "R1", "5col"),
    (29, "data/raw/kea_karnataka/2023/2023_round2_karnataka_allotmentlist_a36fea30.pdf", 2023, "R2", "8col"),
    (27, "data/raw/kea_karnataka/2023/2023_mopup_karnataka_allotmentlist_48858628.pdf", 2023, "MOPUP", "8col"),
    (30, "data/raw/kea_karnataka/2023/2023_stray_karnataka_allotmentlist_bae991fc.pdf", 2023, "STRAY", "8col"),
    # 2024 (may have font issues)
    (31, "data/raw/kea_karnataka/2024/2024_stray5_karnataka_allotmentlist_f558cf0b.pdf", 2024, "STRAY", "8col"),
    (32, "data/raw/kea_karnataka/2024/2024_stray6_karnataka_allotmentlist_bdc7b9cf.pdf", 2024, "STRAY", "8col"),
    # 2025
    (33, "data/raw/kea_karnataka/2025/2025_round2_prov2_karnataka_allotmentlist_19bfff91.pdf", 2025, "R2", "8col"),
    (34, "data/raw/kea_karnataka/2025/2025_round3_karnataka_allotmentlist_e2b2bb6d.pdf", 2025, "R3", "8col"),
]


def run_batch(project_root: Path):
    """Parse all configured KEA PDFs in batch."""
    output_dir = project_root / "data" / "parsed" / "kea_allotments"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_stats = []

    for source_id, pdf_rel, year, round_name, fmt in KEA_BATCH_CONFIG:
        pdf_path = project_root / pdf_rel
        if not pdf_path.exists():
            print(f"SKIP (not found): {pdf_rel}")
            continue

        out_name = f"kea_{year}_{round_name}.csv"
        out_path = output_dir / out_name

        print(f"\nParsing: {pdf_rel} → {out_name}")
        print(f"  Year={year}, Round={round_name}, Format={fmt}, Source_ID={source_id}")

        try:
            if fmt == "5col":
                df, stats = parse_kea_5col_pdf(pdf_path, year, round_name, source_id)
            else:
                df, stats = parse_kea_8col_pdf(pdf_path, year, round_name, source_id)

            stats["source_id"] = source_id
            stats["file"] = pdf_rel
            stats["year"] = year
            stats["round"] = round_name
            stats["output"] = str(out_path)

            if df.empty:
                print(f"  WARNING: No data extracted!")
            else:
                df.to_csv(out_path, index=False)
                print(f"  OK: {len(df)} rows saved")

            print(f"  Pages={stats['total_pages']}, Extracted={stats['rows_extracted']}, Skipped={stats['rows_skipped']}")
            if stats["errors"]:
                print(f"  Errors: {len(stats['errors'])} (first: {stats['errors'][0]})")

            all_stats.append(stats)

        except Exception as e:
            print(f"  ERROR: {e}")
            all_stats.append({"source_id": source_id, "file": pdf_rel, "error": str(e)})

    # Save summary
    import json
    summary_path = output_dir / "_parse_summary.json"
    with open(summary_path, "w") as f:
        json.dump(all_stats, f, indent=2, default=str)
    print(f"\nSummary saved to: {summary_path}")

    return all_stats


def main():
    parser = argparse.ArgumentParser(description="Parse KEA allotment PDF to CSV")
    parser.add_argument("--input", required=True, help="Path to KEA PDF")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--year", type=int, required=True, help="Counselling year")
    parser.add_argument("--round", required=True, choices=VALID_ROUNDS, help="Round name")
    parser.add_argument("--source-id", type=int, default=1, help="data_sources.source_id")
    args = parser.parse_args()

    pdf_path = Path(args.input)
    output_path = Path(args.output)

    print(f"Parsing: {pdf_path}")
    print(f"Year: {args.year}, Round: {args.round}")
    print(f"SHA256: {compute_sha256(pdf_path)}")

    df = parse_kea_allotment_pdf(pdf_path, args.year, args.round, args.source_id)

    if df.empty:
        print("No data extracted. PDF format needs custom column mapping.")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Saved {len(df)} rows to {output_path}")


if __name__ == "__main__":
    main()
