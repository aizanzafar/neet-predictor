"""Quick test: parse first 20 pages of KEA eligible list PDF."""
import pdfplumber
import re

pdf_path = "data/raw/kea_karnataka/2020/Provisional_R1_FinalNEET_2020.pdf"

candidates = []
with pdfplumber.open(pdf_path) as pdf:
    for i in range(20):
        page = pdf.pages[i]
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
            if any(kw in upper for kw in [
                "KARNATAKA EXAMINATIONS", "PROVISIONAL VERIFIED", "SAMPIGE ROAD",
                "NEET ROLL NO", "NEET SCORE", "NEET AI_RANK",
                "DOWNLOAD THE", "DURING THE PROCESS", "PLEASE NOTE",
                "MERE LISTING", "PUBLICATION OF", "CADIDATE FINDS",
                "KEEP VISITING", "ELIGIBLE CANDIDATE NAME", "ORDER OF PREFERENCE"
            ]):
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

            # Line1 should have NEET roll (27XXXXXXXX)
            roll_match = re.search(r"\b(27\d{8})\b", line1)
            if not roll_match:
                j += 1
                continue

            # Line2: first token is score
            score_match = re.match(r"(\d{2,3})\b", line2.strip())
            # Line3: first token is rank
            rank_match = re.match(r"(\d+)\b", line3.strip())

            if score_match and rank_match:
                score = int(score_match.group(1))
                rank = int(rank_match.group(1))
                # Extract category from line3
                cat = ""
                for pat in [r"(General Merit)", r"(Category-[123][AB]?)", r"(SC\b)", r"(ST\b)", r"(Category-1)"]:
                    cm = re.search(pat, line3, re.IGNORECASE)
                    if cm:
                        cat = cm.group(1)
                        break
                # HK from line1
                hk_m = re.search(r"Indian\s+(Yes|No)\s+(Yes|No)", line1)
                hk = hk_m.group(1) if hk_m else ""

                candidates.append({"score": score, "rank": rank, "category": cat, "hk": hk})
            j += 3

print(f"Candidates from first 20 pages: {len(candidates)}")
scores = [c["score"] for c in candidates]
ranks = [c["rank"] for c in candidates]
print(f"Score range: {min(scores)} - {max(scores)}")
print(f"Rank range: {min(ranks)} - {max(ranks)}")
print()
print("Sample (first 15):")
for c in candidates[:15]:
    print(f"  Score={c['score']:>3}  Rank={c['rank']:>6}  Cat={c['category']:<15} HK={c['hk']}")
print()
cats = {}
for c in candidates:
    cats[c["category"]] = cats.get(c["category"], 0) + 1
print(f"Categories: {cats}")
