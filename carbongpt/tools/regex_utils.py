"""
regex_utils.py — Regex-based field detection utilities for CarbonGPT.

Provides a single function that checks whether any pattern from a list
matches anywhere in the given text.  Patterns are compiled once and
cached for performance.
"""

import re
from functools import lru_cache


@lru_cache(maxsize=256)
def _compile(pattern: str) -> re.Pattern:
    """Compile and cache a regex pattern (case-insensitive)."""
    return re.compile(pattern, re.IGNORECASE | re.DOTALL)


def any_pattern_matches(text: str, patterns: list[str]) -> bool:
    """
    Return True if at least one *pattern* matches anywhere in *text*.

    Parameters
    ----------
    text:
        Body text of a document section.
    patterns:
        List of regex strings.  Each is compiled with IGNORECASE.

    Returns
    -------
    bool
    """
    for pat_str in patterns:
        try:
            if _compile(pat_str).search(text):
                return True
        except re.error:
            continue
    return False
