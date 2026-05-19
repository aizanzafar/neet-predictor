"""Tests for data loading utilities."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from neet_predictor.dataio.loader import (
    DataNotFoundError,
    InsufficientDataError,
    load_csv,
    load_marks_rank_points,
    load_exam_years,
    check_data_availability,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test CSVs."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestLoadCsv:

    def test_load_valid_csv(self, temp_dir):
        csv_path = temp_dir / "test.csv"
        csv_path.write_text("col1,col2\n1,a\n2,b\n", encoding="utf-8")
        df = load_csv(csv_path)
        assert len(df) == 2
        assert list(df.columns) == ["col1", "col2"]

    def test_file_not_found(self, temp_dir):
        with pytest.raises(DataNotFoundError):
            load_csv(temp_dir / "nonexistent.csv")

    def test_empty_file(self, temp_dir):
        """Zero-byte file should raise DataNotFoundError or similar."""
        csv_path = temp_dir / "empty.csv"
        csv_path.write_text("", encoding="utf-8")
        with pytest.raises((DataNotFoundError, Exception)):
            load_csv(csv_path)

    def test_headers_only(self, temp_dir):
        """File with headers but no data rows → empty DataFrame → raises."""
        csv_path = temp_dir / "header_only.csv"
        csv_path.write_text("col1,col2\n", encoding="utf-8")
        with pytest.raises((DataNotFoundError, InsufficientDataError)):
            load_csv(csv_path)

    def test_utf8_encoding(self, temp_dir):
        csv_path = temp_dir / "unicode.csv"
        csv_path.write_text("name\nVellore Institute – Tamil\n", encoding="utf-8")
        df = load_csv(csv_path)
        assert "Vellore" in df.iloc[0, 0]


class TestLoadMarksRankPoints:

    def test_returns_dataframe_when_data_exists(self, temp_dir, monkeypatch):
        csv_path = temp_dir / "marks_rank_points.csv"
        csv_path.write_text(
            "year,marks_min,marks_max,rank_min,rank_max,source_id,confidence\n"
            "2024,700,700,50,100,1,high\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "neet_predictor.dataio.loader.CURATED_FILES",
            {"marks_rank_points": csv_path},
        )
        df = load_marks_rank_points()
        assert len(df) == 1

    def test_raises_when_missing(self, temp_dir, monkeypatch):
        monkeypatch.setattr(
            "neet_predictor.dataio.loader.CURATED_FILES",
            {"marks_rank_points": temp_dir / "missing.csv"},
        )
        # required=False means it returns None, not raises
        result = load_marks_rank_points()
        assert result is None


class TestCheckDataAvailability:

    def test_all_files_present(self, temp_dir, monkeypatch):
        files = {}
        for name in ["marks_rank_points", "allotments", "closing_ranks"]:
            p = temp_dir / f"{name}.csv"
            p.write_text(f"col1\nval\n", encoding="utf-8")
            files[name] = p
        source_file = temp_dir / "data_sources.csv"
        source_file.write_text("col1\nval\n", encoding="utf-8")
        monkeypatch.setattr("neet_predictor.dataio.loader.CURATED_FILES", files)
        monkeypatch.setattr("neet_predictor.dataio.loader.SOURCE_FILE", source_file)
        report = check_data_availability()
        assert all(v["exists"] for v in report.values())

    def test_missing_files(self, temp_dir, monkeypatch):
        files = {
            "marks_rank_points": temp_dir / "missing1.csv",
            "allotments": temp_dir / "missing2.csv",
        }
        source_file = temp_dir / "missing_sources.csv"
        monkeypatch.setattr("neet_predictor.dataio.loader.CURATED_FILES", files)
        monkeypatch.setattr("neet_predictor.dataio.loader.SOURCE_FILE", source_file)
        report = check_data_availability()
        assert not any(v["exists"] for v in report.values())
