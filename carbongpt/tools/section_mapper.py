"""
section_mapper.py — Fuzzy heading matcher for CarbonGPT.

Normalises heading text (lowercase, strip punctuation, collapse whitespace)
and uses a multi-strategy approach to find the best match:

1. Exact normalized match
2. Prefix/contains match (e.g. "SECTION A" matches "SECTION A. DESCRIPTION OF PROJECT")
3. Fuzzy match via rapidfuzz token_sort_ratio

Public API
----------
normalize_heading(text)
    Return a cleaned version of a heading string.

map_sections(expected, found, threshold=85)
    Return a dict  {expected_name: matched_found_heading | None}.
"""

import re
import unicodedata

from rapidfuzz import fuzz, process


_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_MULTI_SPACE_RE = re.compile(r"\s+")


def normalize_heading(text: str) -> str:
    """
    Lowercase, strip accents, remove punctuation, and collapse whitespace.
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = _PUNCT_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return text


DEFAULT_THRESHOLD: int = 85


def _prefix_match(
    norm_exp: str,
    normalised_found: dict[str, str],
) -> str | None:
    """
    Return the original heading if *norm_exp* is a prefix of (or is
    contained at the start of) any normalised found heading.
    Picks the longest match to prefer more specific sections.
    """
    if not norm_exp:
        return None

    best: str | None = None
    best_norm: str = ""

    for norm_key, original in normalised_found.items():
        if norm_key.startswith(norm_exp) or norm_key.startswith(norm_exp + " "):
            if best is None or len(norm_key) > len(best_norm):
                best = original
                best_norm = norm_key

    return best


def map_sections(
    expected: list[str],
    found: list[str],
    threshold: int = DEFAULT_THRESHOLD,
) -> dict[str, str | None]:
    """
    For each *expected* heading, find the best match among *found*.

    Strategy order:
    1. Exact normalized match
    2. Prefix match (expected is a prefix of a found heading)
    3. Fuzzy match via rapidfuzz
    """
    if not found:
        return {name: None for name in expected}

    normalised_found = {normalize_heading(h): h for h in found}
    norm_keys = list(normalised_found.keys())

    mapping: dict[str, str | None] = {}

    for exp in expected:
        norm_exp = normalize_heading(exp)

        if norm_exp in normalised_found:
            mapping[exp] = normalised_found[norm_exp]
            continue

        prefix_result = _prefix_match(norm_exp, normalised_found)
        if prefix_result is not None:
            mapping[exp] = prefix_result
            continue

        result = process.extractOne(
            norm_exp,
            norm_keys,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=threshold,
        )

        if result is not None:
            best_norm, score, idx = result
            mapping[exp] = normalised_found[best_norm]
        else:
            mapping[exp] = None

    return mapping
