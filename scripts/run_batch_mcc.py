"""Batch parse all MCC and KEA PDFs."""
import sys, time
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT / "src"))
sys.path.insert(0, str(_PROJECT))

project_root = _PROJECT
start = time.time()

# MCC batch
print("=" * 60)
print("MCC AIQ BATCH PARSE")
print("=" * 60)
from pipelines.parse_mcc_pdf import run_batch as run_mcc_batch
mcc_stats = run_mcc_batch(project_root)
mcc_rows = sum(s.get("rows_extracted", 0) for s in mcc_stats)
print(f"\nMCC: {len(mcc_stats)} files, {mcc_rows} total rows")

# KEA batch
print("\n" + "=" * 60)
print("KEA KARNATAKA BATCH PARSE")
print("=" * 60)
from pipelines.parse_kea_pdf import run_batch as run_kea_batch
kea_stats = run_kea_batch(project_root)
kea_rows = sum(s.get("rows_extracted", 0) for s in kea_stats)
print(f"\nKEA: {len(kea_stats)} files, {kea_rows} total rows")

elapsed = time.time() - start
print(f"\n{'=' * 60}")
print(f"GRAND TOTAL: {mcc_rows + kea_rows} rows in {elapsed:.1f}s")
