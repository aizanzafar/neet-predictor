-- NEET Predictor SQLite Schema
-- Source: BLUEPRINT.md Part C3
-- Run: sqlite3 neet_predictor.db < db/schema.sql

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================
-- Source provenance for every data point
-- ============================================================
CREATE TABLE IF NOT EXISTS data_sources (
    source_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type     TEXT NOT NULL
        CHECK(source_type IN (
            'OFFICIAL_NTA', 'OFFICIAL_MCC', 'OFFICIAL_KEA',
            'VERIFIED_SCORECARD', 'SECONDARY_PORTAL'
        )),
    source_name     TEXT NOT NULL,
    source_url      TEXT,
    source_file     TEXT,
    sha256          TEXT,
    publisher       TEXT,
    published_date  TEXT,
    accessed_date   TEXT,
    confidence      TEXT NOT NULL CHECK(confidence IN ('high', 'medium', 'low')),
    parse_quality   TEXT CHECK(parse_quality IN ('clean', 'minor_issues', 'major_issues', 'unverified')),
    verified_by     TEXT,
    verified_at     TEXT,
    row_count       INTEGER,
    notes           TEXT
);

-- ============================================================
-- MODULE 1: MARKS-TO-RANK
-- ============================================================

CREATE TABLE IF NOT EXISTS exam_years (
    year                    INTEGER PRIMARY KEY,
    max_marks               INTEGER DEFAULT 720,
    registered_candidates   INTEGER,
    appeared_candidates     INTEGER,
    qualified_candidates    INTEGER,
    highest_marks           INTEGER,
    toppers_at_highest      INTEGER,
    cutoff_ur               INTEGER,
    cutoff_obc              INTEGER,
    cutoff_sc               INTEGER,
    cutoff_st               INTEGER,
    cutoff_ews              INTEGER,
    result_date             TEXT,
    source_id               INTEGER REFERENCES data_sources(source_id),
    notes                   TEXT
);

CREATE TABLE IF NOT EXISTS marks_rank_points (
    point_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    year               INTEGER NOT NULL,
    marks_min          INTEGER NOT NULL,
    marks_max          INTEGER NOT NULL,
    rank_min           INTEGER NOT NULL,
    rank_max           INTEGER NOT NULL,
    rank_median        INTEGER,
    candidate_count    INTEGER,
    percentile         REAL,
    data_granularity   TEXT CHECK(data_granularity IN ('exact', 'range', 'bucket', 'estimated')),
    extraction_method  TEXT CHECK(extraction_method IN (
        'manual', 'pdf_table', 'web_table', 'scorecard', 'derived', 'official_published'
    )),
    source_id          INTEGER REFERENCES data_sources(source_id),
    confidence         TEXT NOT NULL CHECK(confidence IN ('high', 'medium', 'low')),
    notes              TEXT,
    UNIQUE(year, marks_min, marks_max, source_id),
    CHECK(marks_min <= marks_max),
    CHECK(marks_min >= 0 AND marks_max <= 720),
    CHECK(rank_min >= 1 AND rank_min <= rank_max)
);

CREATE TABLE IF NOT EXISTS tie_breaking_rules (
    rule_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    year        INTEGER NOT NULL,
    priority    INTEGER NOT NULL,
    criterion   TEXT NOT NULL,
    source_id   INTEGER REFERENCES data_sources(source_id),
    notes       TEXT
);

-- ============================================================
-- MODULE 2: COLLEGE PREDICTION
-- ============================================================

CREATE TABLE IF NOT EXISTS colleges (
    college_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    college_code    TEXT,
    college_name    TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    state           TEXT NOT NULL,
    city            TEXT,
    ownership       TEXT NOT NULL CHECK(ownership IN (
        'government', 'private', 'deemed', 'central', 'AIIMS', 'JIPMER'
    )),
    counselling     TEXT NOT NULL CHECK(counselling IN ('MCC', 'KEA', 'BOTH')),
    courses         TEXT,
    annual_intake   INTEGER,
    fee_govt_quota  INTEGER,
    fee_private     INTEGER,
    nmc_approved    INTEGER DEFAULT 1,
    source_id       INTEGER REFERENCES data_sources(source_id),
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS allotments (
    allotment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    year              INTEGER NOT NULL,
    round             TEXT NOT NULL CHECK(round IN ('R1', 'R2', 'R3', 'MOPUP', 'STRAY')),
    authority         TEXT NOT NULL CHECK(authority IN ('MCC', 'KEA')),
    counselling_scope TEXT NOT NULL CHECK(counselling_scope IN ('AIQ', 'STATE_KA')),
    rank_raw          TEXT NOT NULL,
    air               INTEGER NOT NULL CHECK(air >= 1),
    rank_type         TEXT DEFAULT 'AIR' CHECK(rank_type IN ('AIR', 'STATE_RANK')),
    allotted_quota    TEXT NOT NULL,
    college_id        INTEGER REFERENCES colleges(college_id),
    college_raw       TEXT,
    course            TEXT NOT NULL CHECK(course IN ('MBBS', 'BDS')),
    seat_category     TEXT NOT NULL,
    candidate_category TEXT,
    seat_type         TEXT,
    fee               INTEGER,
    status            TEXT,
    source_id         INTEGER REFERENCES data_sources(source_id),
    notes             TEXT,
    CHECK(year BETWEEN 2020 AND 2025)
);

CREATE TABLE IF NOT EXISTS closing_ranks (
    closing_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    year              INTEGER NOT NULL,
    round             TEXT NOT NULL,
    authority         TEXT NOT NULL CHECK(authority IN ('MCC', 'KEA')),
    counselling_scope TEXT NOT NULL,
    college_id        INTEGER REFERENCES colleges(college_id),
    course            TEXT NOT NULL,
    quota             TEXT NOT NULL,
    category          TEXT NOT NULL,
    seat_type         TEXT,
    opening_rank      INTEGER,
    closing_rank      INTEGER NOT NULL,
    seats_total       INTEGER,
    seats_filled      INTEGER,
    derivation_method TEXT CHECK(derivation_method IN (
        'derived_from_allotments', 'direct_from_cutoff_pdf'
    )),
    statuses_included TEXT,
    source_id         INTEGER REFERENCES data_sources(source_id),
    notes             TEXT,
    UNIQUE(year, round, authority, college_id, course, quota, category, seat_type),
    CHECK(closing_rank >= opening_rank OR opening_rank IS NULL),
    CHECK(seats_filled <= seats_total OR seats_total IS NULL)
);

CREATE TABLE IF NOT EXISTS seat_matrix (
    matrix_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    year              INTEGER NOT NULL,
    round             TEXT NOT NULL,
    authority         TEXT NOT NULL,
    counselling_scope TEXT NOT NULL,
    college_id        INTEGER REFERENCES colleges(college_id),
    course            TEXT NOT NULL,
    quota             TEXT NOT NULL,
    category          TEXT NOT NULL,
    seat_type         TEXT,
    seats_available   INTEGER NOT NULL,
    fee               INTEGER,
    source_id         INTEGER REFERENCES data_sources(source_id),
    notes             TEXT
);

CREATE TABLE IF NOT EXISTS college_aliases (
    alias_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id       INTEGER NOT NULL REFERENCES colleges(college_id),
    alias_name       TEXT NOT NULL,
    alias_normalized TEXT NOT NULL,
    authority        TEXT,
    year             INTEGER,
    source_id        INTEGER REFERENCES data_sources(source_id),
    notes            TEXT
);

CREATE TABLE IF NOT EXISTS counselling_rules (
    rule_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    year        INTEGER NOT NULL,
    authority   TEXT NOT NULL,
    rule_type   TEXT NOT NULL,
    description TEXT NOT NULL,
    applies_to  TEXT,
    source_id   INTEGER REFERENCES data_sources(source_id),
    notes       TEXT
);

-- ============================================================
-- Indexes for common queries
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_marks_rank_year ON marks_rank_points(year);
CREATE INDEX IF NOT EXISTS idx_allotments_year_round ON allotments(year, round, authority);
CREATE INDEX IF NOT EXISTS idx_allotments_college ON allotments(college_id);
CREATE INDEX IF NOT EXISTS idx_closing_ranks_lookup ON closing_ranks(year, authority, college_id, course, category);
CREATE INDEX IF NOT EXISTS idx_college_aliases_norm ON college_aliases(alias_normalized);
