"""Quick test of MCC parser on small PDF."""
import sys
sys.path.insert(0, "src")
sys.path.insert(0, ".")
from pathlib import Path
from pipelines.parse_mcc_pdf import parse_mcc_standard_pdf

# Test on small PDF (45 pages - MOPUP 2024)
pdf = Path("mcc_aiq/2024/2024103043.pdf")
df, stats = parse_mcc_standard_pdf(pdf, 2024, "MOPUP", 19)

print(f"Rows extracted: {len(df)}")
print(f"Stats: pages={stats['total_pages']}, extracted={stats['rows_extracted']}, skipped={stats['rows_skipped']}")
print(f"Errors (first 5): {stats['errors'][:5]}")
print()
if not df.empty:
    print("First 5 rows:")
    print(df[["air", "allotted_quota", "college_raw", "course", "seat_category", "status"]].head().to_string())
    print()
    print(f"Courses: {df['course'].value_counts().to_dict()}")
    print(f"Statuses: {df['status'].value_counts().to_dict()}")
    print(f"AIR range: {df['air'].min()} to {df['air'].max()}")
else:
    print("NO DATA EXTRACTED")
