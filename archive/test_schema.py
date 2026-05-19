"""Tests for database schema creation and integrity."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from neet_predictor.dataio.database import get_connection, init_db, table_exists, row_count


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    init_db(db_path)
    yield db_path
    db_path.unlink(missing_ok=True)


class TestSchemaCreation:
    """Test that all tables are created correctly."""

    EXPECTED_TABLES = [
        "data_sources",
        "exam_years",
        "marks_rank_points",
        "tie_breaking_rules",
        "colleges",
        "allotments",
        "closing_ranks",
        "seat_matrix",
        "college_aliases",
        "counselling_rules",
    ]

    def test_all_tables_created(self, temp_db):
        conn = get_connection(temp_db)
        try:
            for table in self.EXPECTED_TABLES:
                assert table_exists(conn, table), f"Table '{table}' not created"
        finally:
            conn.close()

    def test_tables_are_empty(self, temp_db):
        conn = get_connection(temp_db)
        try:
            for table in self.EXPECTED_TABLES:
                assert row_count(conn, table) == 0
        finally:
            conn.close()

    def test_foreign_keys_enabled(self, temp_db):
        conn = get_connection(temp_db)
        try:
            result = conn.execute("PRAGMA foreign_keys").fetchone()
            assert result[0] == 1
        finally:
            conn.close()

    def test_marks_rank_check_constraints(self, temp_db):
        """marks_min must be <= marks_max, rank_min must be <= rank_max."""
        conn = get_connection(temp_db)
        try:
            # First insert a valid source
            conn.execute(
                "INSERT INTO data_sources (source_type, source_name, confidence) "
                "VALUES ('OFFICIAL_NTA', 'test', 'high')"
            )
            # Invalid: marks_min > marks_max
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO marks_rank_points (year, marks_min, marks_max, rank_min, rank_max, source_id, confidence) "
                    "VALUES (2024, 650, 600, 100, 200, 1, 'high')"
                )
        finally:
            conn.close()

    def test_marks_range_check(self, temp_db):
        """marks must be between 0 and 720."""
        conn = get_connection(temp_db)
        try:
            conn.execute(
                "INSERT INTO data_sources (source_type, source_name, confidence) "
                "VALUES ('OFFICIAL_NTA', 'test', 'high')"
            )
            # Invalid: marks_max > 720
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO marks_rank_points (year, marks_min, marks_max, rank_min, rank_max, source_id, confidence) "
                    "VALUES (2024, 700, 750, 1, 10, 1, 'high')"
                )
        finally:
            conn.close()

    def test_rank_min_positive(self, temp_db):
        """rank_min must be >= 1."""
        conn = get_connection(temp_db)
        try:
            conn.execute(
                "INSERT INTO data_sources (source_type, source_name, confidence) "
                "VALUES ('OFFICIAL_NTA', 'test', 'high')"
            )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO marks_rank_points (year, marks_min, marks_max, rank_min, rank_max, source_id, confidence) "
                    "VALUES (2024, 700, 720, 0, 10, 1, 'high')"
                )
        finally:
            conn.close()

    def test_allotment_air_positive(self, temp_db):
        """air must be >= 1 in allotments."""
        conn = get_connection(temp_db)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO allotments (year, round, authority, counselling_scope, rank_raw, air, allotted_quota, course, seat_category) "
                    "VALUES (2024, 'R1', 'MCC', 'AIQ', '0.0', 0, 'Open', 'MBBS', 'Open')"
                )
        finally:
            conn.close()

    def test_allotment_year_range(self, temp_db):
        """year must be between 2020 and 2025."""
        conn = get_connection(temp_db)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO allotments (year, round, authority, counselling_scope, rank_raw, air, allotted_quota, course, seat_category) "
                    "VALUES (2019, 'R1', 'MCC', 'AIQ', '1.0', 1, 'Open', 'MBBS', 'Open')"
                )
        finally:
            conn.close()

    def test_valid_insert(self, temp_db):
        """A valid row should insert without error."""
        conn = get_connection(temp_db)
        try:
            conn.execute(
                "INSERT INTO data_sources (source_type, source_name, confidence) "
                "VALUES ('OFFICIAL_NTA', 'NTA 2024 Result', 'high')"
            )
            conn.execute(
                "INSERT INTO marks_rank_points (year, marks_min, marks_max, rank_min, rank_max, source_id, confidence) "
                "VALUES (2024, 650, 650, 5000, 5500, 1, 'high')"
            )
            conn.commit()
            assert row_count(conn, "marks_rank_points") == 1
        finally:
            conn.close()
