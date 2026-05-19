"""Parse KEA 2020 cutoff PDFs into structured closing ranks CSV.

KEA cutoff PDFs have this format per college:
  [serial] [code] [college_name]
  [category_headers: 1G 1K 1R 2AG ... STR (24 cols for gen/HK) or GMP GMPH ... (20 cols for priv)]
  [course-seat_type] [rank1] [rank2] ... [rankN]

Output: Normalized CSV with columns:
  year, round, college_code, college_name, course, seat_type, category, closing_rank

Strategy: Use extract_text(x_tolerance=1) which handles most concatenation cases.
For remaining cases where numbers still run together (>6 digits), split them
knowing valid NEET ranks are 1-820,000 (max 6 digits).
"""
import pdfplumber
import re
import csv
from pathlib import Path

# Category headers for each file type
GEN_CATEGORIES = ["1G", "1K", "1R", "2AG", "2AK", "2AR", "2BG", "2BK", "2BR",
                  "3AG", "3AK", "3AR", "3BG", "3BK", "3BR", "GM", "GMK", "GMR",
                  "SCG", "SCK", "SCR", "STG", "STK", "STR"]

HK_CATEGORIES = ["1H", "1KH", "1RH", "2AH", "2AKH", "2ARH", "2BH", "2BKH", "2BRH",
                 "3AH", "3AKH", "3ARH", "3BH", "3BKH", "3BRH", "GMH", "GMKH", "GMRH",
                 "SCH", "SCKH", "SCRH", "STH", "STKH", "STRH"]

PRIV_CATEGORIES = ["GMP", "GMPH", "MA", "MC", "ME", "MEH", "MK", "MM", "MMH", "MU",
                   "NRI", "OPN", "OTH", "RC2", "RC3", "RC4", "RC5", "RC6", "RC7", "RC8"]

MAX_VALID_RANK = 820000  # NEET 2020 had ~800K candidates


def split_concatenated(token: str, needed: int) -> list[str]:
    """Split a concatenated digit string into `needed` valid rank values.
    
    Each part must be 1-6 digits and <= MAX_VALID_RANK.
    Returns list of parts if successful, or [token] if can't split.
    """
    if needed <= 1:
        return [token]
    
    # Try all valid split points for the first number
    for split_pos in range(1, min(7, len(token))):
        left = token[:split_pos]
        right = token[split_pos:]
        
        # Validate left part
        if left.startswith('0') and len(left) > 1:
            continue
        if int(left) > MAX_VALID_RANK:
            continue
        if int(left) == 0:
            continue
        
        # Recursively split the remainder
        if needed == 2:
            # Right must be a valid single value
            if right.startswith('0') and len(right) > 1:
                continue
            if not right or len(right) > 6:
                continue
            if int(right) > MAX_VALID_RANK or int(right) == 0:
                continue
            return [left, right]
        else:
            # Need to split right into (needed-1) parts
            sub = split_concatenated(right, needed - 1)
            if len(sub) == needed - 1:
                return [left] + sub
    
    return [token]  # Can't split


def expand_tokens(tokens: list[str], expected_count: int) -> list[str]:
    """Expand concatenated tokens to reach expected_count values."""
    if len(tokens) >= expected_count:
        return tokens
    
    deficit = expected_count - len(tokens)
    
    # Find oversized tokens (> 6 digits) and split them
    result = []
    remaining_deficit = deficit
    
    for tok in tokens:
        if remaining_deficit <= 0 or tok == '--' or len(tok) <= 6:
            result.append(tok)
        else:
            # Try to split this token into 2+ parts
            parts_needed = min(remaining_deficit + 1, len(tok) // 3)
            split_done = False
            for n in range(2, parts_needed + 1):
                parts = split_concatenated(tok, n)
                if len(parts) == n:
                    result.extend(parts)
                    remaining_deficit -= (n - 1)
                    split_done = True
                    break
            if not split_done:
                result.append(tok)
    
    return result


def parse_cutoff_pdf(pdf_path: Path, year: int, round_name: str, quota_type: str) -> list[dict]:
    """Parse a KEA cutoff PDF into rows of closing rank data."""
    if quota_type == "GEN":
        categories = GEN_CATEGORIES
    elif quota_type == "HK":
        categories = HK_CATEGORIES
    elif quota_type == "PRIV":
        categories = PRIV_CATEGORIES
    else:
        raise ValueError(f"Unknown quota_type: {quota_type}")
    
    rows = []
    
    with pdfplumber.open(str(pdf_path)) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1)
            if text:
                full_text += text + "\n"
    
    lines = full_text.split("\n")
    current_code = None
    current_name = None
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Skip title/header lines
        if "CUTOFF" in stripped.upper() or "CLOSING RANK" in stripped.upper():
            continue
        
        # Detect college header: starts with number, then code (M001, D001, etc.)
        college_match = re.match(r"^(\d+)\s+(M\d{3}|D\d{3})\s+(.+)$", stripped)
        if college_match:
            current_code = college_match.group(2)
            current_name = college_match.group(3).strip()
            continue
        
        # Skip category header lines
        if stripped.startswith("1G ") or stripped.startswith("1H ") or stripped.startswith("GMP "):
            continue
        
        # Parse data lines
        course_match = re.match(r"^(MBBS|BDS)-(GOVT\.|PRIV\.|NRI|OTHERS)\s+(.*)$", stripped)
        if course_match and current_code:
            course = course_match.group(1)
            seat_type = course_match.group(2).rstrip(".")
            rank_str = course_match.group(3)
            
            # For PRIV NRI/OTHERS: single value
            if quota_type == "PRIV" and seat_type in ("NRI", "OTHERS"):
                tokens = rank_str.split()
                rank_val = tokens[0] if tokens else "--"
                if rank_val != "--":
                    try:
                        rank_int = int(rank_val)
                        if rank_int <= MAX_VALID_RANK:
                            rows.append({
                                "year": year, "round": round_name,
                                "college_code": current_code,
                                "college_name": current_name,
                                "course": course, "seat_type": seat_type,
                                "category": seat_type,
                                "closing_rank": rank_int,
                            })
                    except ValueError:
                        pass
                continue
            
            # Main cutoff line with multiple categories
            tokens = rank_str.split()
            
            # If we have fewer tokens than expected, try to expand concatenated ones
            if len(tokens) < len(categories):
                tokens = expand_tokens(tokens, len(categories))
            
            for idx, cat in enumerate(categories):
                if idx < len(tokens):
                    val = tokens[idx]
                    if val != "--":
                        try:
                            rank_int = int(val)
                            if 0 < rank_int <= MAX_VALID_RANK:
                                rows.append({
                                    "year": year, "round": round_name,
                                    "college_code": current_code,
                                    "college_name": current_name,
                                    "course": course, "seat_type": seat_type,
                                    "category": cat, "closing_rank": rank_int,
                                })
                        except ValueError:
                            pass
    
    return rows


def main():
    base = Path("data/raw/kea_karnataka/2020")
    out_dir = Path("data/parsed/kea_cutoffs")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Define all PDF files to parse
    pdf_configs = [
        (base / "R1" / "medi_cutoff_gen_r1.pdf", 2020, "R1", "GEN"),
        (base / "R1" / "medi_cutoff_hk_r1.pdf", 2020, "R1", "HK"),
        (base / "R1" / "medi_cutoff_priv_r1.pdf", 2020, "R1", "PRIV"),
        (base / "R2" / "medi_cutoff_gen.pdf", 2020, "R2", "GEN"),
        (base / "R2" / "medi_cutoff_hk.pdf", 2020, "R2", "HK"),
        (base / "R2" / "medi_cutoff_priv.pdf", 2020, "R2", "PRIV"),
    ]
    
    all_rows = []
    
    for pdf_path, year, round_name, quota_type in pdf_configs:
        if not pdf_path.exists():
            print(f"SKIP (not found): {pdf_path}")
            continue
        
        print(f"Parsing: {pdf_path.name} (year={year}, round={round_name}, type={quota_type})")
        rows = parse_cutoff_pdf(pdf_path, year, round_name, quota_type)
        print(f"  -> {len(rows)} closing rank entries")
        all_rows.extend(rows)
    
    print(f"\nTotal: {len(all_rows)} closing rank entries")
    
    # Write combined CSV
    out_path = out_dir / "kea_2020_closing_ranks.csv"
    fieldnames = ["year", "round", "college_code", "college_name", "course", "seat_type", "category", "closing_rank"]
    
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"Saved: {out_path}")
    
    # Print summary
    colleges = set(r["college_code"] for r in all_rows)
    rounds = set(r["round"] for r in all_rows)
    courses = set(r["course"] for r in all_rows)
    print(f"\nColleges: {len(colleges)}")
    print(f"Rounds: {rounds}")
    print(f"Courses: {courses}")
    
    for rnd in sorted(rounds):
        rnd_rows = [r for r in all_rows if r["round"] == rnd]
        rnd_colleges = set(r["college_code"] for r in rnd_rows)
        print(f"  {rnd}: {len(rnd_rows)} entries across {len(rnd_colleges)} colleges")


if __name__ == "__main__":
    main()
