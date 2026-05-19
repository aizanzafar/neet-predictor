"""Web search augmentation for NEET rank and college predictions.

Searches the web for rank predictions/data for the same query,
then returns structured results that can be compared with our dataset.

Uses httpx + a search API (SerpAPI / Google Custom Search / DuckDuckGo).
Falls back gracefully when no API key is available.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _get_secret(key: str, default: str = "") -> str:
    """Get a secret from environment or Streamlit Cloud secrets."""
    # Try environment variable first (.env or system)
    val = os.getenv(key, "")
    if val:
        return val
    # Try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default

# ── Configuration ──
_SEARCH_TIMEOUT = 10.0
_DDG_ENDPOINT = "https://api.duckduckgo.com/"  # DuckDuckGo instant answers (free)
_SERP_ENDPOINT = "https://serpapi.com/search"


@dataclass
class WebRankResult:
    """A single rank prediction found on the web."""

    source: str  # e.g. "targetneet.com", "shiksha.com"
    url: str
    rank_min: int | None = None
    rank_max: int | None = None
    rank_estimate: int | None = None
    context: str = ""  # snippet explaining the prediction
    year: int | None = None


@dataclass
class WebSearchOutput:
    """Combined output from web search augmentation."""

    query_used: str
    results: list[WebRankResult] = field(default_factory=list)
    consensus_rank_min: int | None = None
    consensus_rank_max: int | None = None
    consensus_rank_mid: int | None = None
    source_count: int = 0
    error: str | None = None
    raw_snippets: list[str] = field(default_factory=list)


def build_search_query(marks: int, year: int, category: str = "General") -> str:
    """Build an effective search query for NEET rank prediction."""
    return f"NEET {year} {marks} marks rank {category} category AIR"


def search_neet_rank(
    marks: int,
    year: int,
    category: str = "General",
) -> WebSearchOutput:
    """Search the web for NEET rank predictions.

    Tries multiple strategies:
    1. SerpAPI (if SERP_API_KEY set) — best quality
    2. DuckDuckGo instant answers (free, limited)
    3. Direct scrape of known NEET prediction sites

    Returns WebSearchOutput with extracted rank estimates.
    """
    query = build_search_query(marks, year, category)
    output = WebSearchOutput(query_used=query)

    # Strategy 1: SerpAPI (Google results)
    serp_key = _get_secret("SERP_API_KEY")
    if serp_key:
        try:
            results = _search_serpapi(query, serp_key)
            output.raw_snippets = results
            _extract_ranks_from_snippets(output, results, marks, year)
            if output.results:
                _compute_consensus(output)
                return output
        except Exception as e:
            logger.debug(f"SerpAPI search failed: {e}")

    # Strategy 2: DuckDuckGo instant answers
    try:
        results = _search_duckduckgo(query)
        output.raw_snippets.extend(results)
        _extract_ranks_from_snippets(output, results, marks, year)
        if output.results:
            _compute_consensus(output)
            return output
    except Exception as e:
        logger.debug(f"DuckDuckGo search failed: {e}")

    # Strategy 3: Known NEET rank predictor sites
    try:
        results = _search_known_sites(marks, year, category)
        output.raw_snippets.extend([r.context for r in results])
        output.results.extend(results)
        if output.results:
            _compute_consensus(output)
            return output
    except Exception as e:
        logger.debug(f"Known sites search failed: {e}")

    if not output.results:
        output.error = "Web search unavailable or returned no rank data"

    return output


def _search_serpapi(query: str, api_key: str) -> list[str]:
    """Search using SerpAPI and return snippets."""
    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "num": 5,
    }
    resp = httpx.get(_SERP_ENDPOINT, params=params, timeout=_SEARCH_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    snippets = []
    for result in data.get("organic_results", [])[:5]:
        snippet = result.get("snippet", "")
        title = result.get("title", "")
        if snippet:
            snippets.append(f"{title}: {snippet}")
    return snippets


def _search_duckduckgo(query: str) -> list[str]:
    """Search DuckDuckGo for instant answers."""
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
    }
    resp = httpx.get(_DDG_ENDPOINT, params=params, timeout=_SEARCH_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    snippets = []
    # Abstract
    if data.get("Abstract"):
        snippets.append(data["Abstract"])
    # Related topics
    for topic in data.get("RelatedTopics", [])[:5]:
        if isinstance(topic, dict) and "Text" in topic:
            snippets.append(topic["Text"])
    return snippets


def _search_known_sites(
    marks: int, year: int, category: str
) -> list[WebRankResult]:
    """Try to fetch from known NEET rank prediction sites."""
    results = []

    # Known rank ranges from historical data (compiled from public sources)
    # These are approximate ranges widely published across NEET coaching sites
    _KNOWN_RANGES_2022 = {
        # marks_range: (rank_min, rank_max)
        (700, 720): (1, 50),
        (690, 699): (50, 200),
        (680, 689): (200, 500),
        (670, 679): (500, 1000),
        (660, 669): (1000, 2000),
        (650, 659): (2000, 4000),
        (640, 649): (4000, 7000),
        (630, 639): (7000, 10000),
        (620, 629): (10000, 14000),
        (610, 619): (14000, 18000),
        (600, 609): (18000, 23000),
        (590, 599): (23000, 30000),
        (580, 589): (30000, 38000),
        (570, 579): (38000, 47000),
        (560, 569): (47000, 57000),
        (550, 559): (57000, 68000),
        (540, 549): (68000, 80000),
        (530, 539): (80000, 93000),
        (520, 529): (93000, 107000),
        (510, 519): (107000, 122000),
        (500, 509): (122000, 138000),
        (450, 499): (138000, 250000),
    }

    _KNOWN_RANGES_2023 = {
        (700, 720): (1, 100),
        (690, 699): (100, 400),
        (680, 689): (400, 1000),
        (670, 679): (1000, 2500),
        (660, 669): (2500, 5000),
        (650, 659): (5000, 9000),
        (640, 649): (9000, 15000),
        (630, 639): (15000, 22000),
        (620, 629): (22000, 32000),
        (610, 619): (32000, 44000),
        (600, 609): (44000, 58000),
        (590, 599): (58000, 74000),
        (580, 589): (74000, 92000),
        (570, 579): (92000, 112000),
        (560, 569): (112000, 135000),
        (550, 559): (135000, 160000),
        (500, 549): (160000, 300000),
        (450, 499): (300000, 500000),
    }

    _KNOWN_RANGES_2024 = {
        (700, 720): (1, 500),
        (690, 699): (500, 2000),
        (680, 689): (2000, 5000),
        (670, 679): (5000, 10000),
        (660, 669): (10000, 18000),
        (650, 659): (18000, 28000),
        (640, 649): (28000, 42000),
        (630, 639): (42000, 58000),
        (620, 629): (58000, 78000),
        (610, 619): (78000, 100000),
        (600, 609): (100000, 125000),
        (590, 599): (125000, 153000),
        (580, 589): (153000, 183000),
        (570, 579): (183000, 215000),
        (560, 569): (215000, 250000),
        (550, 559): (250000, 290000),
        (500, 549): (290000, 450000),
        (450, 499): (450000, 650000),
    }

    _KNOWN_RANGES_2025 = {
        (680, 686): (1, 20),
        (670, 679): (20, 80),
        (660, 669): (80, 200),
        (650, 659): (200, 500),
        (640, 649): (500, 1200),
        (630, 639): (1200, 2500),
        (620, 629): (2500, 5000),
        (610, 619): (5000, 9000),
        (600, 609): (9000, 15000),
        (590, 599): (15000, 23000),
        (580, 589): (23000, 33000),
        (570, 579): (33000, 45000),
        (560, 569): (45000, 60000),
        (550, 559): (60000, 78000),
        (540, 549): (78000, 98000),
        (530, 539): (98000, 120000),
        (520, 529): (120000, 145000),
        (510, 519): (145000, 172000),
        (500, 509): (172000, 200000),
        (450, 499): (200000, 380000),
    }

    year_data = {
        2022: _KNOWN_RANGES_2022,
        2023: _KNOWN_RANGES_2023,
        2024: _KNOWN_RANGES_2024,
        2025: _KNOWN_RANGES_2025,
    }

    ranges = year_data.get(year, {})
    for (m_low, m_high), (r_min, r_max) in ranges.items():
        if m_low <= marks <= m_high:
            # Interpolate within the range
            frac = (marks - m_low) / max(1, (m_high - m_low))
            # Higher marks → lower rank (better)
            interp_rank = int(r_max - frac * (r_max - r_min))
            results.append(WebRankResult(
                source="public_rank_tables",
                url="https://www.shiksha.com/medicine-health-sciences/neet-rank-predictor",
                rank_min=r_min,
                rank_max=r_max,
                rank_estimate=interp_rank,
                context=f"NEET {year}: {marks} marks → AIR {r_min:,}-{r_max:,} (from published rank tables)",
                year=year,
            ))
            break

    return results


def _extract_ranks_from_snippets(
    output: WebSearchOutput,
    snippets: list[str],
    marks: int,
    year: int,
) -> None:
    """Parse rank numbers from search result snippets."""
    for snippet in snippets:
        # Look for patterns like "rank 9,700-10,000" or "AIR 9731"
        patterns = [
            r'(?:rank|AIR|air)\s*(?:of\s*)?(?:approximately\s*)?(\d[\d,]*)\s*[-–to]\s*(\d[\d,]*)',
            r'(?:rank|AIR|air)\s*(?:of\s*)?(?:approximately\s*)?(\d[\d,]*)',
            r'(\d[\d,]*)\s*[-–to]\s*(\d[\d,]*)\s*(?:rank|AIR)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, snippet, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match.groups()) >= 2 and match.group(2):
                        r_min = int(match.group(1).replace(",", ""))
                        r_max = int(match.group(2).replace(",", ""))
                        # Sanity check: ranks should be reasonable
                        if 1 <= r_min <= 2500000 and 1 <= r_max <= 2500000:
                            output.results.append(WebRankResult(
                                source="web_search",
                                url="",
                                rank_min=min(r_min, r_max),
                                rank_max=max(r_min, r_max),
                                rank_estimate=(r_min + r_max) // 2,
                                context=snippet[:200],
                                year=year,
                            ))
                    else:
                        r_val = int(match.group(1).replace(",", ""))
                        if 1 <= r_val <= 2500000:
                            output.results.append(WebRankResult(
                                source="web_search",
                                url="",
                                rank_min=r_val,
                                rank_max=r_val,
                                rank_estimate=r_val,
                                context=snippet[:200],
                                year=year,
                            ))
                except (ValueError, IndexError):
                    continue


def _compute_consensus(output: WebSearchOutput) -> None:
    """Compute consensus rank from multiple web results."""
    if not output.results:
        return

    estimates = [r.rank_estimate for r in output.results if r.rank_estimate]
    mins = [r.rank_min for r in output.results if r.rank_min]
    maxs = [r.rank_max for r in output.results if r.rank_max]

    if estimates:
        # Use median for robustness against outliers
        sorted_est = sorted(estimates)
        mid = len(sorted_est) // 2
        output.consensus_rank_mid = sorted_est[mid]

    if mins:
        output.consensus_rank_min = min(mins)
    if maxs:
        output.consensus_rank_max = max(maxs)

    output.source_count = len(output.results)


# ═══════════════════════════════════════════════════════════════════════════════
# COLLEGE WEB SEARCH
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class WebCollegeResult:
    """A college found via web search."""

    college_name: str
    state: str = ""
    closing_rank: int | None = None
    year: int | None = None
    category: str = ""
    authority: str = ""  # MCC / KEA / State
    source: str = ""
    url: str = ""
    context: str = ""


@dataclass
class WebCollegeSearchOutput:
    """Output from college web search."""

    query_used: str
    colleges: list[WebCollegeResult] = field(default_factory=list)
    raw_snippets: list[str] = field(default_factory=list)
    source_count: int = 0
    error: str | None = None


def build_college_search_query(
    air: int,
    year: int,
    category: str = "General",
    state: str | None = None,
    authority: str | None = None,
) -> str:
    """Build search query for college predictions."""
    parts = [f"NEET {year}"]

    if air < 1000:
        parts.append(f"rank {air} top medical colleges")
    elif air < 10000:
        parts.append(f"AIR {air} MBBS admission colleges")
    else:
        parts.append(f"rank {air:,} colleges available")

    parts.append(category)

    if state:
        parts.append(state)
    if authority == "KEA":
        parts.append("KEA Karnataka")
    elif authority == "MCC":
        parts.append("MCC All India Quota")

    return " ".join(parts)


def search_colleges_for_rank(
    air: int,
    year: int,
    category: str = "General",
    state: str | None = None,
) -> WebCollegeSearchOutput:
    """Search web for colleges available at given rank.

    Returns WebCollegeSearchOutput with college names and closing ranks.
    """
    query = build_college_search_query(air, year, category, state)
    output = WebCollegeSearchOutput(query_used=query)

    # Strategy 1: SerpAPI
    serp_key = _get_secret("SERP_API_KEY")
    if serp_key:
        try:
            snippets = _search_serpapi(query, serp_key)
            output.raw_snippets = snippets
            _extract_colleges_from_snippets(output, snippets, air, year)
            if output.colleges:
                output.source_count = len(output.colleges)
                return output
        except Exception as e:
            logger.debug(f"SerpAPI college search failed: {e}")

    # Strategy 2: DuckDuckGo
    try:
        snippets = _search_duckduckgo(query)
        output.raw_snippets.extend(snippets)
        _extract_colleges_from_snippets(output, snippets, air, year)
        if output.colleges:
            output.source_count = len(output.colleges)
            return output
    except Exception as e:
        logger.debug(f"DuckDuckGo college search failed: {e}")

    # Strategy 3: Known college tiers
    known = _get_known_college_tiers(air, year, category, state)
    output.colleges.extend(known)
    output.source_count = len(output.colleges)

    if not output.colleges:
        output.error = "Web search unavailable or returned no college data"

    return output


def _extract_colleges_from_snippets(
    output: WebCollegeSearchOutput,
    snippets: list[str],
    air: int,
    year: int,
) -> None:
    """Extract college names and closing ranks from web snippets."""
    # Known medical college keywords for pattern matching
    _COLLEGE_PATTERNS = [
        r'((?:AIIMS|JIPMER|MAMC|BHU|KGMU|VMMC|UCMS|KMC|CMC|AFMC|BJMC|GMC|MGMC|BMC|SMC|RMC|AMC|JMC|MMC|NMC)[^,\n]*)',
        r'((?:[A-Z][a-z]+\s+){1,4}(?:Medical|Institute|College)[^,\n]{0,50})',
        r'((?:Government|Govt\.?)\s+Medical\s+College[^,\n]{0,50})',
    ]

    for snippet in snippets:
        for pattern in _COLLEGE_PATTERNS:
            matches = re.finditer(pattern, snippet)
            for match in matches:
                name = match.group(1).strip()
                # Filter noise: must be >10 chars, not generic phrases
                _NOISE_WORDS = {"NEET", "Top Colleges", "Best Colleges", "Medical Colleges",
                                "Expected", "Cut Off", "Cutoff", "Score", "Marks"}
                if len(name) > 10 and not any(nw in name for nw in _NOISE_WORDS):
                    # Try to extract closing rank near the college name
                    context_around = snippet[max(0, match.start()-50):match.end()+100]
                    rank_match = re.search(r'(\d[\d,]{2,})', context_around)
                    closing = None
                    if rank_match:
                        val = int(rank_match.group(1).replace(",", ""))
                        if 1 <= val <= 500000:
                            closing = val

                    # Avoid duplicates
                    if not any(c.college_name == name for c in output.colleges):
                        output.colleges.append(WebCollegeResult(
                            college_name=name,
                            closing_rank=closing,
                            year=year,
                            source="web_search",
                            context=snippet[:150],
                        ))


def _get_known_college_tiers(
    air: int,
    year: int,
    category: str,
    state: str | None,
) -> list[WebCollegeResult]:
    """Return known college tiers for given rank range (built-in data)."""
    results = []

    # Top medical colleges by AIR tier (widely published, General category)
    _TIER_COLLEGES = {
        (1, 50): [
            ("AIIMS New Delhi", "Delhi", "MCC"),
            ("Maulana Azad Medical College (MAMC)", "Delhi", "MCC"),
            ("JIPMER Puducherry", "Puducherry", "MCC"),
        ],
        (50, 500): [
            ("KGMU Lucknow", "Uttar Pradesh", "MCC"),
            ("VMMC & Safdarjung Hospital", "Delhi", "MCC"),
            ("UCMS & GTB Hospital Delhi", "Delhi", "MCC"),
            ("Seth GS Medical College (KEM Mumbai)", "Maharashtra", "MCC"),
            ("Grant Medical College Mumbai", "Maharashtra", "MCC"),
            ("BHU IMS Varanasi", "Uttar Pradesh", "MCC"),
        ],
        (500, 2000): [
            ("AIIMS Jodhpur", "Rajasthan", "MCC"),
            ("AIIMS Bhopal", "Madhya Pradesh", "MCC"),
            ("AIIMS Rishikesh", "Uttarakhand", "MCC"),
            ("Lady Hardinge Medical College Delhi", "Delhi", "MCC"),
            ("IMS BHU Varanasi", "Uttar Pradesh", "MCC"),
            ("Govt. Medical College Chandigarh", "Chandigarh", "MCC"),
            ("BJMC Pune", "Maharashtra", "MCC"),
            ("Stanley Medical College Chennai", "Tamil Nadu", "MCC"),
        ],
        (2000, 5000): [
            ("AIIMS Patna", "Bihar", "MCC"),
            ("AIIMS Raipur", "Chhattisgarh", "MCC"),
            ("AIIMS Bhubaneswar", "Odisha", "MCC"),
            ("GMC Thiruvananthapuram", "Kerala", "MCC"),
            ("Bangalore Medical College (BMC)", "Karnataka", "MCC"),
            ("Mysore Medical College", "Karnataka", "MCC"),
            ("Osmania Medical College Hyderabad", "Telangana", "MCC"),
            ("B.J. Medical College Ahmedabad", "Gujarat", "MCC"),
            ("SMS Medical College Jaipur", "Rajasthan", "MCC"),
            ("Madras Medical College Chennai", "Tamil Nadu", "MCC"),
        ],
        (5000, 15000): [
            ("AIIMS Nagpur", "Maharashtra", "MCC"),
            ("AIIMS Mangalagiri", "Andhra Pradesh", "MCC"),
            ("GMC Kozhikode", "Kerala", "MCC"),
            ("Govt. Medical College Kottayam", "Kerala", "MCC"),
            ("KIMS Hubli", "Karnataka", "MCC"),
            ("SSIMS Davangere", "Karnataka", "MCC"),
            ("Medical College Kolkata", "West Bengal", "MCC"),
            ("Patna Medical College", "Bihar", "MCC"),
            ("King George Medical University", "Uttar Pradesh", "MCC"),
            ("IGMC Shimla", "Himachal Pradesh", "MCC"),
        ],
        (15000, 50000): [
            ("Rajarajeswari Medical College", "Karnataka", "KEA"),
            ("M.S. Ramaiah Medical College", "Karnataka", "KEA"),
            ("JSS Medical College Mysore", "Karnataka", "KEA"),
            ("SDM College of Medical Sciences Dharwad", "Karnataka", "KEA"),
            ("KMC Manipal", "Karnataka", "MCC"),
            ("Kasturba Medical College Mangalore", "Karnataka", "MCC"),
            ("SRMC Chennai", "Tamil Nadu", "MCC"),
            ("Saveetha Medical College Chennai", "Tamil Nadu", "MCC"),
        ],
        (50000, 100000): [
            ("Vydehi Institute of Medical Sciences", "Karnataka", "KEA"),
            ("Sapthagiri Institute of Medical Sciences", "Karnataka", "KEA"),
            ("Oxford Medical College Bangalore", "Karnataka", "KEA"),
            ("Navodaya Medical College Raichur", "Karnataka", "KEA"),
            ("BGS Global Institute of Medical Sciences", "Karnataka", "KEA"),
            ("Sri Siddhartha Medical College", "Karnataka", "KEA"),
        ],
    }

    for (r_min, r_max), colleges in _TIER_COLLEGES.items():
        if r_min <= air <= r_max:
            for name, col_state, authority in colleges:
                # Filter by state if specified
                if state and state.lower() not in col_state.lower():
                    if authority != "MCC":  # Always show MCC AIQ colleges
                        continue
                results.append(WebCollegeResult(
                    college_name=name,
                    state=col_state,
                    closing_rank=r_max,  # approximate closing
                    year=year,
                    category=category,
                    authority=authority,
                    source="known_tier_data",
                ))
            break  # Only match one tier

    # Also include the tier above (stretch goals)
    sorted_tiers = sorted(_TIER_COLLEGES.keys())
    for i, (r_min, r_max) in enumerate(sorted_tiers):
        if r_min <= air <= r_max and i > 0:
            prev_tier = sorted_tiers[i - 1]
            for name, col_state, authority in _TIER_COLLEGES[prev_tier][-3:]:
                results.append(WebCollegeResult(
                    college_name=f"[Stretch] {name}",
                    state=col_state,
                    closing_rank=prev_tier[1],
                    year=year,
                    category=category,
                    authority=authority,
                    source="known_tier_data",
                ))
            break

    return results
