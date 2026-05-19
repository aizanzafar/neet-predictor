"""Parse MCC allotment PDFs into structured CSV.

Supports:
- Standard 8-column format (2020, 2022–2024): SNo, Rank, Allotted Quota,
  Allotted Institute, Course, Alloted Category, Candidate Category, Remarks
- 2021 admitted-list format (11 columns): handled separately

Usage:
    python -m pipelines.parse_mcc_pdf --input <pdf_path> --output <csv_path> --year 2024 --round R1 --source-id 17

Batch mode:
    python -m pipelines.parse_mcc_pdf --batch
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[0].parent / "src"))

from neet_predictor.config import VALID_COURSES, VALID_ROUNDS
from neet_predictor.dataio.normalizer import normalize_college_name, parse_mcc_rank


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# Header patterns to skip
_HEADER_PATTERNS = re.compile(
    r"^(SNo|S\.?\s*No\.?|Rank|Allotted|Course|Alloted|Candidate|Remarks|Description|"
    r"Abbreviation|Quota Name|Category|Institute|Subject)",
    re.IGNORECASE,
)

# Rank patterns: "1.01", "1(A)", "27", "139000"
_RANK_PATTERN = re.compile(r"^\d+(\.\d+)?(\([A-Z]\))?$")


def _clean_cell(val) -> str:
    """Clean a cell value: strip whitespace, replace newlines with spaces."""
    if not val:
        return ""
    return re.sub(r"\s+", " ", str(val)).strip()


# 2020 MCC category abbreviation → standard name mapping
_MCC_2020_CATEGORY_MAP = {
    # Concatenated forms
    "GN": "Open",
    "GNNO": "General",
    "GNPH": "PwD Open",
    "OBC": "OBC",
    "OBCPH": "PwD OBC",
    "SC": "SC",
    "SCPH": "PwD SC",
    "ST": "ST",
    "STPH": "PwD ST",
    "EWS": "EWS",
    "EWPH": "PwD EWS",
    "EWNO": "EWS",
    # Space-separated forms (after newline→space cleanup)
    "GN PwD": "PwD Open",
    "GN NO": "General",
    "OBC PwD": "PwD OBC",
    "SC PwD": "PwD SC",
    "ST PwD": "PwD ST",
    "EW PwD": "PwD EWS",
    "EW NO": "EWS",
    "EWS PwD": "PwD EWS",
}

_MCC_2020_QUOTA_MAP = {
    "AI": "All India",
    "AIQ": "All India",
    "OS": "Open Seat Quota",
    "IP": "Internal",
}


def _normalize_mcc_category(cat: str, year: int) -> str:
    """Normalize MCC seat_category, handling 2020 abbreviations."""
    if not cat:
        return ""
    cat = cat.strip()
    if year <= 2020:
        # Strip priority suffix: "GN (Priority: 5B)" → "GN"
        base = re.sub(r"\s*\(Priority:.*?\)", "", cat).strip()
        return _MCC_2020_CATEGORY_MAP.get(base, base)
    return cat


def _normalize_mcc_quota(quota: str, year: int) -> str:
    """Normalize MCC allotted_quota, handling 2020 abbreviations."""
    if not quota:
        return ""
    quota = quota.strip()
    if year <= 2020:
        return _MCC_2020_QUOTA_MAP.get(quota, quota)
    return quota


def _is_header_row(row: list) -> bool:
    """Detect if a row is a table header or abbreviation legend."""
    if not row or not row[0]:
        return True
    first = str(row[0]).strip()
    if _HEADER_PATTERNS.match(first):
        return True
    # Legend rows (abbreviation tables)
    if any(kw in first.lower() for kw in ["abbreviation", "description", "quota name"]):
        return True
    return False


def _detect_rank_col(row: list) -> int:
    """Detect whether rank is at col 1 (8-col) or col 2 (9-col with RollNo).

    Returns the 0-based index of the Rank column.
    """
    if len(row) >= 9:
        # If col 2 looks like a valid rank AND col 1 looks like a roll number (long digit string)
        col1 = str(row[1]).strip() if row[1] else ""
        col2 = str(row[2]).strip() if row[2] else ""
        if col1 and len(col1) >= 8 and col1.isdigit():
            # col1 is likely a roll number (8+ digits)
            if col2 and re.match(r"^\d+(\.\d+)?(\([A-Za-z]\))?$", col2):
                return 2
    return 1


def _is_data_row(row: list) -> bool:
    """Check if row looks like valid allotment data."""
    if not row or len(row) < 6:
        return False
    # First col should be a serial number
    try:
        int(str(row[0]).strip())
    except (ValueError, TypeError):
        return False
    # Rank could be at col 1 (standard) or col 2 (9-col with RollNo)
    rank_col = _detect_rank_col(row)
    rank_str = str(row[rank_col]).strip() if row[rank_col] else ""
    if not rank_str:
        return False
    # Allow rank patterns: pure int, float, or int(letter)
    if re.match(r"^\d+(\.\d+)?(\([A-Za-z]\))?$", rank_str):
        return True
    return False


def _parse_rank_string(rank_str: str) -> tuple[str, int]:
    """Parse various MCC rank formats into (rank_raw, air).

    Formats:
      "1.01" → ("1.01", 1)   [2024 decimal ties]
      "1(A)" → ("1(A)", 1)   [2023 letter ties]
      "27"   → ("27", 27)    [plain integer]
    """
    rank_str = str(rank_str).strip()

    # Handle letter-tie format: "1(A)" → air=1
    letter_match = re.match(r"^(\d+)\([A-Za-z]\)$", rank_str)
    if letter_match:
        return rank_str, int(letter_match.group(1))

    # Handle decimal or plain integer
    try:
        rank_float = float(rank_str)
        return rank_str, int(rank_float)
    except (ValueError, TypeError):
        raise ValueError(f"Cannot parse MCC rank: '{rank_str}'")


def _normalize_course(course_raw: str) -> str:
    """Normalize course name."""
    if not course_raw:
        return ""
    c = course_raw.strip().upper()
    if "MBBS" in c:
        return "MBBS"
    if "BDS" in c:
        return "BDS"
    return course_raw.strip()


def _normalize_status(remarks: str) -> str:
    """Normalize the Remarks/Status column."""
    if not remarks:
        return ""
    r = remarks.strip()
    # Common values: "Allotted", "Not Reported", "Cancelled"
    if "allot" in r.lower():
        return "Allotted"
    if "not reported" in r.lower() or "not joined" in r.lower():
        return "Not Reported"
    if "cancel" in r.lower():
        return "Cancelled"
    if "upgrade" in r.lower():
        return "Upgraded"
    if "resign" in r.lower():
        return "Resigned"
    return r


def parse_mcc_standard_pdf(
    pdf_path: Path,
    year: int,
    round_name: str,
    source_id: int,
) -> tuple[pd.DataFrame, dict]:
    """Parse a standard 8-column MCC allotment PDF.

    Returns:
        (DataFrame of allotments, stats dict with parse metrics)
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
                    if _is_header_row(row):
                        continue
                    if not _is_data_row(row):
                        stats["rows_skipped"] += 1
                        continue

                    try:
                        # Detect column layout: 8-col vs 9-col (with RollNo)
                        rank_col = _detect_rank_col(row)
                        offset = rank_col - 1  # 0 for standard, 1 for 9-col

                        # Standard 8-col: SNo, Rank, Quota, Institute, Course, SeatCat, CandCat, Remarks
                        # 9-col variant:  SNo, RollNo, Rank, Quota, Institute, Course, SeatCat, CandCat, Remarks
                        rank_raw, air = _parse_rank_string(row[rank_col])
                        course = _normalize_course(row[4 + offset]) if len(row) > (4 + offset) else ""

                        # Filter: only MBBS and BDS per BLUEPRINT
                        if course not in ("MBBS", "BDS"):
                            stats["rows_skipped"] += 1
                            continue

                        record = {
                            "year": year,
                            "round": round_name,
                            "authority": "MCC",
                            "counselling_scope": "AIQ",
                            "rank_raw": rank_raw,
                            "air": air,
                            "rank_type": "AIR",
                            "allotted_quota": _normalize_mcc_quota(_clean_cell(row[2 + offset]), year),
                            "college_raw": _clean_cell(row[3 + offset]),
                            "course": course,
                            "seat_category": _normalize_mcc_category(_clean_cell(row[5 + offset]), year) if len(row) > (5 + offset) else "",
                            "candidate_category": _normalize_mcc_category(_clean_cell(row[6 + offset]), year) if len(row) > (6 + offset) else "",
                            "status": _normalize_status(row[7 + offset] if len(row) > (7 + offset) else ""),
                            "source_id": source_id,
                        }
                        all_records.append(record)
                        stats["rows_extracted"] += 1

                    except (ValueError, IndexError) as e:
                        stats["errors"].append(f"Page {page_num}, row {row[:3]}: {e}")
                        stats["rows_skipped"] += 1

    if not all_records:
        return pd.DataFrame(), stats

    df = pd.DataFrame(all_records)
    return df, stats


def parse_mcc_2021_format(
    pdf_path: Path,
    year: int,
    round_name: str,
    source_id: int,
) -> tuple[pd.DataFrame, dict]:
    """Parse 2021-style MCC PDF with 11 columns (Roll No, Name, AIR, etc.).

    Columns: S.No, Roll No, Name, Quota Name, AIR, Category, Institute Name,
             Subject, Allotted Category, Allotted ph, Admitted Round
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
                    if not row or len(row) < 8:
                        stats["rows_skipped"] += 1
                        continue

                    # Skip header
                    first = str(row[0]).strip() if row[0] else ""
                    if not first or not first.isdigit():
                        continue

                    try:
                        # Col indices: 0=SNo, 1=RollNo, 2=Name, 3=QuotaName, 4=AIR,
                        # 5=Category, 6=InstituteName, 7=Subject, 8=AllottedCat, 9=AllottedPH, 10=AdmittedRound
                        air_str = str(row[4]).strip() if row[4] else ""
                        if not air_str or not air_str.isdigit():
                            stats["rows_skipped"] += 1
                            continue

                        air = int(air_str)
                        course = _normalize_course(row[7]) if len(row) > 7 else ""

                        if course not in ("MBBS", "BDS"):
                            stats["rows_skipped"] += 1
                            continue

                        record = {
                            "year": year,
                            "round": round_name,
                            "authority": "MCC",
                            "counselling_scope": "AIQ",
                            "rank_raw": air_str,
                            "air": air,
                            "rank_type": "AIR",
                            "allotted_quota": _clean_cell(row[3]),
                            "college_raw": _clean_cell(row[6]),
                            "course": course,
                            "seat_category": _clean_cell(row[8]) if len(row) > 8 else "",
                            "candidate_category": _clean_cell(row[5]),
                            "status": "Allotted",  # 2021 admitted list = all allotted
                            "source_id": source_id,
                        }
                        all_records.append(record)
                        stats["rows_extracted"] += 1

                    except (ValueError, IndexError) as e:
                        stats["errors"].append(f"Page {page_num}: {e}")
                        stats["rows_skipped"] += 1

    if not all_records:
        return pd.DataFrame(), stats

    df = pd.DataFrame(all_records)
    return df, stats


# ── Batch configuration: maps source_id → (pdf_path, year, round, parser) ──
BATCH_CONFIG = [
    # 2020
    (1, "data/raw/mcc_aiq/2020/2022072721-1.pdf", 2020, "R1", "standard"),
    (2, "data/raw/mcc_aiq/2020/2022072916.pdf", 2020, "R2", "standard"),
    # 2021
    (3, "data/raw/mcc_aiq/2021/2022060614.pdf", 2021, "R1", "2021"),  # Admitted list format
    (4, "data/raw/mcc_aiq/2021/2022061436.pdf", 2021, "R2", "standard"),
    (5, "data/raw/mcc_aiq/2021/2022061461.pdf", 2021, "R1", "standard"),
    # Skip 6 (provisional duplicate of R1)
    # 2022
    (7, "data/raw/mcc_aiq/2022/2023053114.pdf", 2022, "MOPUP", "standard"),
    (8, "data/raw/mcc_aiq/2022/2023053124.pdf", 2022, "STRAY", "standard"),
    (9, "data/raw/mcc_aiq/2022/2023053188-1.pdf", 2022, "R1", "standard"),
    (10, "data/raw/mcc_aiq/2022/2023053196.pdf", 2022, "R2", "standard"),
    # 2023
    (11, "data/raw/mcc_aiq/2023/2023073062.pdf", 2023, "R1", "standard"),
    (12, "data/raw/mcc_aiq/2023/2023081882.pdf", 2023, "R2", "standard"),
    (13, "data/raw/mcc_aiq/2023/2023090732.pdf", 2023, "R3", "standard"),
    (14, "data/raw/mcc_aiq/2023/2023092765.pdf", 2023, "STRAY", "standard"),
    # Skip 15, 16 (small BDS/nursing-specific)
    # 2024
    (17, "data/raw/mcc_aiq/2024/2024082536.pdf", 2024, "R1", "standard"),
    (18, "data/raw/mcc_aiq/2024/2024092017.pdf", 2024, "R2", "standard"),
    (19, "data/raw/mcc_aiq/2024/2024103043.pdf", 2024, "MOPUP", "standard"),
    (20, "data/raw/mcc_aiq/2024/2024112362.pdf", 2024, "STRAY", "standard"),
    # Skip 22 (duplicate R2), skip 23 (R3 - FinalAllotmentStatus format may differ)
    # 2025
    (25, "data/raw/mcc_aiq/2025/202511141694474556.pdf", 2025, "STRAY", "standard"),
    (26, "data/raw/mcc_aiq/2025/20250813289226788.pdf", 2025, "R1", "standard"),
    # R2 and R3 use wide multi-round format — need dedicated parsers
    # (27, "data/raw/mcc_aiq/2025/202509182057444522.pdf", 2025, "R2", "wide_r2"),
    # (28, "data/raw/mcc_aiq/2025/202510231856675154.pdf", 2025, "R3", "wide_r3"),
    # 2020 / 2021 additions
    (30, "data/raw/mcc_aiq/2020/2022072982.pdf", 2020, "MOPUP", "standard"),
    (31, "data/raw/mcc_aiq/2021/20220614100.pdf", 2021, "STRAY", "standard"),
]


def run_batch(project_root: Path):
    """Parse all configured MCC PDFs in batch."""
    output_dir = project_root / "data" / "parsed" / "mcc_allotments"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_stats = []

    for source_id, pdf_rel, year, round_name, parser_type in BATCH_CONFIG:
        pdf_path = project_root / pdf_rel
        if not pdf_path.exists():
            print(f"SKIP (not found): {pdf_rel}")
            continue

        out_name = f"mcc_{year}_{round_name}.csv"
        out_path = output_dir / out_name

        print(f"\nParsing: {pdf_rel} → {out_name}")
        print(f"  Year={year}, Round={round_name}, Source_ID={source_id}")

        try:
            if parser_type == "2021":
                df, stats = parse_mcc_2021_format(pdf_path, year, round_name, source_id)
            else:
                df, stats = parse_mcc_standard_pdf(pdf_path, year, round_name, source_id)

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
                print(f"  First error: {stats['errors'][0]}")

            all_stats.append(stats)

        except Exception as e:
            print(f"  ERROR: {e}")
            all_stats.append({"source_id": source_id, "file": pdf_rel, "error": str(e)})

    # Save parse summary
    summary_path = output_dir / "_parse_summary.json"
    import json
    with open(summary_path, "w") as f:
        json.dump(all_stats, f, indent=2, default=str)
    print(f"\nSummary saved to: {summary_path}")

    return all_stats


def main():
    parser = argparse.ArgumentParser(description="Parse MCC allotment PDF to CSV")
    parser.add_argument("--input", help="Path to MCC allotment PDF")
    parser.add_argument("--output", help="Output CSV path")
    parser.add_argument("--year", type=int, help="Counselling year")
    parser.add_argument("--round", choices=VALID_ROUNDS, help="Round name")
    parser.add_argument("--source-id", type=int, default=1, help="data_sources.source_id")
    parser.add_argument("--batch", action="store_true", help="Run batch processing on all configured PDFs")
    parser.add_argument("--format", choices=["standard", "2021"], default="standard", help="PDF format")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]

    if args.batch:
        run_batch(project_root)
        return

    if not args.input or not args.output or not args.year or not args.round:
        parser.error("--input, --output, --year, and --round are required for single-file mode")

    pdf_path = Path(args.input)
    output_path = Path(args.output)

    print(f"Parsing: {pdf_path}")
    print(f"Year: {args.year}, Round: {args.round}")
    print(f"SHA256: {compute_sha256(pdf_path)}")

    if args.format == "2021":
        df, stats = parse_mcc_2021_format(pdf_path, args.year, args.round, args.source_id)
    else:
        df, stats = parse_mcc_standard_pdf(pdf_path, args.year, args.round, args.source_id)

    if df.empty:
        print("No data extracted. Check PDF format.")
        print(f"Stats: {stats}")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Saved {len(df)} rows to {output_path}")
        print(f"Stats: pages={stats['total_pages']}, extracted={stats['rows_extracted']}, skipped={stats['rows_skipped']}")


if __name__ == "__main__":
    main()
