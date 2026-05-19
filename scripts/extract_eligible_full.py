"""Full extraction: parse all pages of KEA eligible list PDF into rank calibration CSV."""
import pdfplumber
import re
import csv
import time
from pathlib import Path

pdf_path = Path("data/raw/kea_karnataka/2020/Provisional_R1_FinalNEET_2020.pdf")
out_dir = Path("data/parsed/rank_calibration")
out_dir.mkdir(parents=True, exist_ok=True)

SKIP_KEYWORDS = [
    "KARNATAKA EXAMINATIONS", "PROVISIONAL VERIFIED", "SAMPIGE ROAD",
    "NEET ROLL NO", "NEET SCORE", "NEET AI_RANK",
    "DOWNLOAD THE", "DURING THE PROCESS", "PLEASE NOTE",
    "MERE LISTING", "PUBLICATION OF", "CADIDATE FINDS",
    "KEEP VISITING", "ELIGIBLE CANDIDATE NAME", "ORDER OF PREFERENCE"
]

start = time.time()
candidates = []
errors = 0

with pdfplumber.open(str(pdf_path)) as pdf:
    total_pages = len(pdf.pages)
    print(f"Parsing {total_pages} pages...")

    for i, page in enumerate(pdf.pages):
        if i % 500 == 0:
            elapsed = time.time() - start
            rate = (i / elapsed) if elapsed > 0 and i > 0 else 0
            eta = ((total_pages - i) / rate / 60) if rate > 0 else 0
            print(f"  Page {i+1}/{total_pages} | {len(candidates)} candidates | {rate:.1f} pg/s | ETA {eta:.1f} min")

        text = page.extract_text()
        if not text:
            continue

        lines = text.split("\n")
        data_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.count("-") > len(stripped) * 0.7 and len(stripped) > 10:
                continue
            upper = stripped.upper()
            if any(kw in upper for kw in SKIP_KEYWORDS):
                continue
            if re.match(r"^\d+ / \d+$", stripped):
                continue
            if stripped.startswith(":") or stripped.startswith("Note"):
                continue
            data_lines.append(stripped)

        # Process in groups of 3
        j = 0
        while j + 2 < len(data_lines):
            line1 = data_lines[j]
            line2 = data_lines[j + 1]
            line3 = data_lines[j + 2]

            roll_match = re.search(r"\b(27\d{8})\b", line1)
            if not roll_match:
                j += 1
                continue

            score_match = re.match(r"(\d{2,3})\b", line2.strip())
            rank_match = re.match(r"(\d+)\b", line3.strip())

            if score_match and rank_match:
                score = int(score_match.group(1))
                rank = int(rank_match.group(1))

                # Sanity checks
                if score < 50 or score > 720 or rank < 1 or rank > 2000000:
                    errors += 1
                    j += 3
                    continue

                # Category from line3
                cat = ""
                for pat in [r"(General Merit)", r"(Category-[123][AB]?)", r"(SC\b)", r"(ST\b)"]:
                    cm = re.search(pat, line3, re.IGNORECASE)
                    if cm:
                        cat = cm.group(1)
                        break

                # HK from line1
                hk_m = re.search(r"Indian\s+(Yes|No)\s+(Yes|No)", line1)
                hk = hk_m.group(1) if hk_m else ""

                # Karnataka status
                karnataka = "Yes" if "Karnataka" in line1 and "Non-Kar" not in line1 else "No"

                candidates.append({
                    "neet_roll_no": roll_match.group(1),
                    "neet_score": score,
                    "neet_ai_rank": rank,
                    "category": cat,
                    "hk": hk,
                    "karnataka": karnataka,
                })
            else:
                errors += 1
            j += 3

elapsed = time.time() - start
print(f"\nDone in {elapsed:.1f}s")
print(f"Total candidates extracted: {len(candidates)}")
print(f"Parse errors/skipped: {errors}")

if candidates:
    scores = [c["neet_score"] for c in candidates]
    ranks = [c["neet_ai_rank"] for c in candidates]
    print(f"Score range: {min(scores)} - {max(scores)}")
    print(f"Rank range: {min(ranks)} - {max(ranks)}")

    # Category distribution
    cats = {}
    for c in candidates:
        cats[c["category"]] = cats.get(c["category"], 0) + 1
    print(f"\nCategory distribution:")
    for k, v in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {k or '(unknown)'}: {v}")

    # Write full eligible list CSV
    full_path = out_dir / "kea_2020_eligible_full.csv"
    with open(full_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["neet_roll_no", "neet_score", "neet_ai_rank", "category", "hk", "karnataka"])
        writer.writeheader()
        writer.writerows(candidates)
    print(f"\nFull list saved: {full_path} ({len(candidates)} rows)")

    # Write deduplicated score-rank pairs for calibration
    seen = set()
    unique_pairs = []
    for c in sorted(candidates, key=lambda x: x["neet_ai_rank"]):
        key = (c["neet_score"], c["neet_ai_rank"])
        if key not in seen:
            seen.add(key)
            unique_pairs.append({"neet_score": c["neet_score"], "neet_ai_rank": c["neet_ai_rank"]})

    cal_path = out_dir / "neet_2020_score_rank.csv"
    with open(cal_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["neet_score", "neet_ai_rank"])
        writer.writeheader()
        writer.writerows(unique_pairs)
    print(f"Score-Rank pairs saved: {cal_path} ({len(unique_pairs)} unique pairs)")
