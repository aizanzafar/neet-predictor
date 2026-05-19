"""Build and maintain the PDF manifest (JSONL) for all downloaded source documents.

Usage:
    python -m pipelines.manifest --scan

Scans raw data directories and produces/updates the manifest JSONL file.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neet_predictor.config import RAW_MCC_DIR, RAW_KEA_DIR, RAW_NTA_DIR, ALL_YEARS


MANIFEST_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "manifest.jsonl"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_metadata_from_path(filepath: Path) -> dict:
    """Infer authority, year, doc_type from file path structure."""
    parts = filepath.parts
    meta = {
        "authority": None,
        "year": None,
        "doc_type": "unknown",
    }

    # Detect authority from parent dirs
    path_str = str(filepath).lower()
    if "mcc" in path_str:
        meta["authority"] = "MCC"
        meta["counselling_scope"] = "AIQ"
    elif "kea" in path_str or "karnataka" in path_str:
        meta["authority"] = "KEA"
        meta["counselling_scope"] = "STATE_KA"
    elif "nta" in path_str:
        meta["authority"] = "NTA"
        meta["counselling_scope"] = None

    # Detect year from path
    for year in ALL_YEARS:
        if str(year) in path_str:
            meta["year"] = year
            break

    return meta


def scan_directory(base_dir: Path) -> list[dict]:
    """Scan a directory for PDFs and generate manifest entries."""
    entries = []
    if not base_dir.exists():
        return entries

    for pdf_path in sorted(base_dir.rglob("*.pdf")):
        meta = infer_metadata_from_path(pdf_path)
        entry = {
            "authority": meta["authority"],
            "counselling_scope": meta.get("counselling_scope"),
            "year": meta["year"],
            "doc_type": "allotment_result",  # default; can be overridden
            "local_path": str(pdf_path.relative_to(base_dir.parent.parent)),
            "filename": pdf_path.name,
            "sha256": compute_sha256(pdf_path),
            "bytes": pdf_path.stat().st_size,
            "scanned_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        entries.append(entry)

    return entries


def build_manifest():
    """Scan all raw directories and write manifest."""
    all_entries = []

    for directory in [RAW_MCC_DIR, RAW_KEA_DIR, RAW_NTA_DIR]:
        entries = scan_directory(directory)
        all_entries.extend(entries)
        print(f"  {directory.name}: {len(entries)} PDFs")

    # Also scan legacy locations (existing PDFs in neet-predictor/mcc_aiq/)
    legacy_mcc = Path(__file__).resolve().parents[1] / "data/raw/mcc_aiq"
    if legacy_mcc.exists():
        entries = scan_directory(legacy_mcc)
        all_entries.extend(entries)
        print(f"  legacy mcc_aiq/: {len(entries)} PDFs")

    legacy_ka = Path(__file__).resolve().parents[1] / "data" / "raw" / "kea_karnataka"
    if legacy_ka.exists():
        entries = scan_directory(legacy_ka)
        all_entries.extend(entries)
        print(f"  data/raw/kea_karnataka/: {len(entries)} PDFs")

    # Write JSONL
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        for entry in all_entries:
            f.write(json.dumps(entry) + "\n")

    print(f"\nManifest written: {MANIFEST_PATH}")
    print(f"Total entries: {len(all_entries)}")
    return all_entries


def main():
    print("Scanning raw data directories for PDFs...")
    build_manifest()


if __name__ == "__main__":
    main()
