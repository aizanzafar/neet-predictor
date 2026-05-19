"""
Parse KEA 2025 candidate list PDF to extract NEET RANK ↔ SCORE pairs.

The PDF (1,256 pages) contains ALL Karnataka candidates who appeared in NEET 2025.
Format: two-column layout with SL.NO, NEET Roll No, NEET RANK, NEET SCORE per entry.
This gives us tens of thousands of exact rank-to-score calibration data points.
"""

import re
import csv
import sys
from pathlib import Path
from collections import defaultdict

import pdfplumber

PDF_PATH = Path("data/raw/kea_karnataka/2025/1752575800phpdTztcM.pdf")

# Regex for data lines: matches one or two entries per line
# Single entry: SL_NO ROLL_NO RANK SCORE
# Double entry: SL_NO ROLL_NO RANK SCORE SL_NO ROLL_NO RANK SCORE
DOUBLE_PAT = re.compile(
    r"^\s*(\d+)\s+(\d{10})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d{10})\s+(\d+)\s+(\d+)\s*$"
)
SINGLE_PAT = re.compile(
    r"^\s*(\d+)\s+(\d{10})\s+(\d+)\s+(\d+)\s*$"
)


def parse_candidates(pdf_path: Path, progress_every: int = 100):
    """Extract all (rank, score) pairs from the candidate list PDF."""
    pairs = []  # list of (rank, score) tuples

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Processing {total_pages} pages...")

        for i, page in enumerate(pdf.pages):
            if (i + 1) % progress_every == 0:
                print(f"  Page {i+1}/{total_pages} ({len(pairs)} pairs so far)")

            text = page.extract_text(x_tolerance=1)
            if not text:
                continue

            for line in text.split("\n"):
                # Try double entry first
                m = DOUBLE_PAT.match(line)
                if m:
                    rank1, score1 = int(m.group(3)), int(m.group(4))
                    rank2, score2 = int(m.group(7)), int(m.group(8))
                    pairs.append((rank1, score1))
                    pairs.append((rank2, score2))
                    continue

                # Try single entry
                m = SINGLE_PAT.match(line)
                if m:
                    rank, score = int(m.group(3)), int(m.group(4))
                    pairs.append((rank, score))

    print(f"Extracted {len(pairs)} total (rank, score) pairs")
    return pairs


def aggregate_by_score(pairs):
    """Aggregate pairs into score bands: for each score, find min/max rank."""
    score_ranks = defaultdict(list)
    for rank, score in pairs:
        score_ranks[score].append(rank)

    aggregated = []
    for score in sorted(score_ranks.keys(), reverse=True):
        ranks = score_ranks[score]
        aggregated.append({
            "score": score,
            "rank_min": min(ranks),
            "rank_max": max(ranks),
            "candidate_count": len(ranks),
        })

    return aggregated


def write_calibration_csv(aggregated, output_path: Path):
    """Write aggregated data to a CSV for reference."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["score", "rank_min", "rank_max", "candidate_count"])
        writer.writeheader()
        writer.writerows(aggregated)
    print(f"Wrote {len(aggregated)} score bands to {output_path}")


def update_marks_rank_points(aggregated, marks_rank_path: Path):
    """Append 2025 calibration data to marks_rank_points.csv, replacing old 2025 web_table entries."""
    # Read existing data
    with open(marks_rank_path) as f:
        reader = csv.DictReader(f)
        existing = list(reader)
        fieldnames = reader.fieldnames

    # Remove existing 2025 entries (we'll replace with much better data)
    kept = [r for r in existing if r["year"] != "2025"]
    removed_count = len(existing) - len(kept)
    print(f"Removed {removed_count} existing 2025 entries")

    # Find max point_id
    max_id = max(int(r["point_id"]) for r in existing) if existing else 0

    # Add new 2025 entries from the candidate list
    new_rows = []
    for item in aggregated:
        max_id += 1
        new_rows.append({
            "point_id": str(max_id),
            "year": "2025",
            "marks_min": str(item["score"]),
            "marks_max": str(item["score"]),
            "rank_min": str(item["rank_min"]),
            "rank_max": str(item["rank_max"]),
            "rank_median": "",
            "candidate_count": str(item["candidate_count"]),
            "percentile": "",
            "data_granularity": "exact",
            "extraction_method": "kea_candidate_list",
            "source_id": "43",
            "confidence": "high",
            "notes": "Extracted from KEA 2025 Karnataka candidate list PDF (87K+ candidates)",
        })

    all_rows = kept + new_rows
    # Sort: by year desc, then rank_min asc
    all_rows.sort(key=lambda r: (-int(r["year"]), int(r["rank_min"])))

    # Reassign point_ids sequentially
    for i, row in enumerate(all_rows, 1):
        row["point_id"] = str(i)

    with open(marks_rank_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Updated {marks_rank_path}: {len(all_rows)} total rows ({len(new_rows)} new 2025 entries)")


if __name__ == "__main__":
    # Step 1: Parse PDF
    pairs = parse_candidates(PDF_PATH)

    # Step 2: Aggregate by score
    aggregated = aggregate_by_score(pairs)
    print(f"\nAggregated into {len(aggregated)} distinct score values")
    print(f"Score range: {aggregated[-1]['score']} to {aggregated[0]['score']}")
    print(f"Rank range: {aggregated[0]['rank_min']} to {aggregated[-1]['rank_max']}")

    # Step 3: Write reference CSV
    ref_path = Path("data/analysis/kea_2025_rank_score_calibration.csv")
    write_calibration_csv(aggregated, ref_path)

    # Step 4: Update marks_rank_points.csv
    if "--update" in sys.argv:
        marks_path = Path("data/curated/marks_rank_points.csv")
        update_marks_rank_points(aggregated, marks_path)
    else:
        print("\nDry run. Use --update to write to marks_rank_points.csv")
