"""
section_mapper.py — Fuzzy heading matcher for CarbonGPT.

Normalises heading text (lowercase, strip punctuation, collapse whitespace)
and uses rapidfuzz to find the best match for each expected section among
the headings actually found in a document.

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


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_MULTI_SPACE_RE = re.compile(r"\s+")


def normalize_heading(text: str) -> str:
    """
    Lowercase, strip accents, remove punctuation, and collapse whitespace.

    Examples
    --------
    >>> normalize_heading("B.1  Monitoring Period")
    'b1 monitoring period'
    >>> normalize_heading("  Project Description!!! ")
    'project description'
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = _PUNCT_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Fuzzy matching
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLD: int = 85


def map_sections(
    expected: list[str],
    found: list[str],
    threshold: int = DEFAULT_THRESHOLD,
) -> dict[str, str | None]:
    """
    For each *expected* heading, find the best fuzzy match among *found*.

    Parameters
    ----------
    expected:
        List of section names the document should contain.
    found:
        List of headings actually present in the document.
    threshold:
        Minimum similarity score (0-100) to accept a match.  Defaults to 85.

    Returns
    -------
    Mapping of ``{expected_section: matched_heading_or_None}``.
    A value of ``None`` means no heading in *found* met the threshold.
    """
    if not found:
        return {name: None for name in expected}

    normalised_found = {normalize_heading(h): h for h in found}
    norm_keys = list(normalised_found.keys())

    mapping: dict[str, str | None] = {}

    for exp in expected:
        norm_exp = normalize_heading(exp)

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
