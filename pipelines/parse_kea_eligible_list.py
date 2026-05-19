"""Parse KEA "Provisional Verified Final List of Eligible Candidates" PDF.

This script extracts NEET Score ↔ AI Rank pairs (plus category metadata)
from the KEA eligibility verification list. Each candidate entry spans 3 lines:

  Line 1: NEET_Roll_No | Appln_No | Candidate_Name | Nationality | HK(371j) | JK | Karnataka/Non-Kar
  Line 2: NEET_Score   | Income   | Father_Name    | Clause      | Rural    | Special_Category | Linguistic_Minority
  Line 3: NEET_AI_Rank | CET_No   | Mother_Name    | Category    | Kannada  | NRI_WARD | Religious_Minority

Entries are separated by lines of dashes.

Usage:
    python -m pipelines.parse_kea_eligible_list <path_to_pdf> [--output <csv_path>]

    Example:
        python -m pipelines.parse_kea_eligible_list data/raw/kea_karnataka/2020/provisional_verified_list.pdf

Output:
    CSV with columns: neet_roll_no, neet_score, neet_ai_rank, category, hk, rural, clause, karnataka
    Saved to data/parsed/kea_eligible_lists/kea_2020_eligible.csv by default.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber required. Install with: pip install pdfplumber")
    sys.exit(1)


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_separator(line: str) -> bool:
    """Check if line is a dash separator."""
    stripped = line.strip()
    return len(stripped) > 10 and stripped.count("-") > len(stripped) * 0.8


def _is_header(line: str) -> bool:
    """Check if line is a header row."""
    upper = line.upper()
    return "NEET ROLL NO" in upper or "APPLN NO" in upper or "CANDIDATE NAME" in upper


def _extract_neet_roll(text: str) -> str:
    """Extract NEET roll number (10-digit pattern like 27XXXXXXXX)."""
    match = re.search(r"\b(27\d{8})\b", text)
    return match.group(1) if match else ""


def _extract_number(text: str) -> int | None:
    """Extract first number from text."""
    match = re.search(r"\b(\d+)\b", text)
    return int(match.group(1)) if match else None


def parse_eligible_list_text(full_text: str) -> list[dict]:
    """Parse the text content of a KEA eligible candidates list.
    
    Returns list of dicts with candidate data.
    """
    lines = full_text.split("\n")
    candidates = []
    
    # Collect non-separator, non-header lines into groups of 3
    data_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _is_separator(stripped):
            continue
        if _is_header(stripped):
            continue
        # Skip page headers/footers
        if "KARNATAKA EXAMINATIONS AUTHORITY" in stripped.upper():
            continue
        if "PROVISIONAL VERIFIED" in stripped.upper():
            continue
        if "SAMPIGE ROAD" in stripped.upper():
            continue
        if re.match(r"^\d{1,2}-\d{1,2}-\d{4}$", stripped):  # Date lines
            continue
        if stripped.upper().startswith("DATE"):
            continue
        if "DOWNLOAD THE VERIFICATION" in stripped.upper():
            continue
        if "DURING THE PROCESS" in stripped.upper():
            continue
        if stripped.startswith("Page ") or re.match(r"^\d+$", stripped):
            continue
            
        data_lines.append(stripped)
    
    # Process in groups of 3 lines per candidate
    i = 0
    while i + 2 < len(data_lines):
        line1 = data_lines[i]
        line2 = data_lines[i + 1]
        line3 = data_lines[i + 2]
        
        # Validate: line1 should contain a NEET roll number (27XXXXXXXX)
        neet_roll = _extract_neet_roll(line1)
        if not neet_roll:
            # Not a valid candidate start, skip one line
            i += 1
            continue
        
        # Parse line1: NEET_Roll_No | Appln_No | Candidate_Name | Nationality | HK | JK | Karnataka
        parts1 = re.split(r"\s{2,}", line1)
        
        # Parse Karnataka status from line1
        karnataka = "Yes" if "KARNATAKA" in line1.upper() and "NON-KAR" not in line1.upper() else "No"
        if "NON-KAR" in line1.upper():
            karnataka = "No"
        
        # HK status
        hk = "Yes" if re.search(r"\bYes\b.*\bNo\b|\bYes\b", line1) else "No"
        # More precise: HK is typically the 5th field
        hk_match = re.search(r"Indian\s+(Yes|No)\s+(Yes|No)", line1, re.IGNORECASE)
        if hk_match:
            hk = hk_match.group(1)
        
        # Parse line2: NEET_Score | Income | Father_Name | Clause | Rural | Special_Category | Linguistic_Minority
        neet_score = _extract_number(line2)
        
        # Extract clause
        clause = ""
        clause_match = re.search(r"Clause\s*-\s*([a-z])", line2, re.IGNORECASE)
        if clause_match:
            clause = f"Clause-{clause_match.group(1)}"
        
        # Rural status
        rural_match = re.search(r"(Yes|No)\s*$", line2.split("Clause")[1] if "Clause" in line2 else line2)
        rural = "No"
        if "Clause" in line2:
            after_clause = line2.split("Clause")[1]
            rural_parts = re.findall(r"\b(Yes|No)\b", after_clause, re.IGNORECASE)
            if rural_parts:
                rural = rural_parts[0]
        
        # Parse line3: NEET_AI_Rank | CET_No | Mother_Name | Category | Kannada | NRI_WARD | Religious_Minority
        neet_ai_rank = _extract_number(line3)
        
        # Extract category
        category = ""
        cat_patterns = [
            r"(General Merit)",
            r"(Category-[123][ABC]?)",
            r"(Category-[123])",
            r"(SC|ST|OBC|GM)",
            r"(Scheduled Tribe)",
            r"(Scheduled Caste)",
        ]
        for pat in cat_patterns:
            cat_match = re.search(pat, line3, re.IGNORECASE)
            if cat_match:
                category = cat_match.group(1)
                break
        
        # Only add if we have valid score and rank
        if neet_score and neet_ai_rank:
            candidates.append({
                "neet_roll_no": neet_roll,
                "neet_score": neet_score,
                "neet_ai_rank": neet_ai_rank,
                "category": category,
                "hk": hk,
                "rural": rural,
                "clause": clause,
                "karnataka": karnataka,
            })
        
        i += 3
    
    return candidates


def parse_eligible_list_pdf(pdf_path: Path) -> pd.DataFrame:
    """Parse a KEA eligible candidates list PDF into a DataFrame."""
    print(f"Parsing: {pdf_path} ({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"SHA256: {compute_sha256(pdf_path)}")
    
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        
        for i, page in enumerate(pdf.pages):
            if i % 500 == 0:
                print(f"  Processing page {i+1}/{total_pages}...")
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    print(f"Extracted {len(full_text)} characters of text")
    
    candidates = parse_eligible_list_text(full_text)
    df = pd.DataFrame(candidates)
    
    print(f"Parsed {len(df)} candidates with valid Score + Rank")
    
    if not df.empty:
        print(f"\nScore range: {df['neet_score'].min()} - {df['neet_score'].max()}")
        print(f"Rank range: {df['neet_ai_rank'].min()} - {df['neet_ai_rank'].max()}")
        print(f"Categories: {df['category'].value_counts().to_dict()}")
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Parse KEA Provisional Verified Final List of Eligible Candidates PDF"
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the eligible candidates PDF file",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output CSV path (default: data/parsed/kea_eligible_lists/kea_<year>_eligible.csv)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2020,
        help="NEET year (default: 2020)",
    )
    
    args = parser.parse_args()
    
    if not args.pdf_path.exists():
        print(f"ERROR: File not found: {args.pdf_path}")
        sys.exit(1)
    
    df = parse_eligible_list_pdf(args.pdf_path)
    
    if df.empty:
        print("\nWARNING: No candidates extracted. The PDF format may differ from expected.")
        sys.exit(1)
    
    # Determine output path
    if args.output:
        out_path = args.output
    else:
        out_dir = Path("data/parsed/kea_eligible_lists")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"kea_{args.year}_eligible.csv"
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\nSaved {len(df)} rows to: {out_path}")
    
    # Also output a rank calibration subset (just score + rank)
    cal_dir = Path("data/parsed/rank_calibration")
    cal_dir.mkdir(parents=True, exist_ok=True)
    cal_path = cal_dir / f"neet_{args.year}_score_rank.csv"
    
    cal_df = df[["neet_score", "neet_ai_rank"]].drop_duplicates().sort_values("neet_ai_rank")
    cal_df.to_csv(cal_path, index=False)
    print(f"Saved {len(cal_df)} unique score-rank pairs to: {cal_path}")


if __name__ == "__main__":
    main()
