"""
regex_utils.py — Regex-based field detection utilities for CarbonGPT.

Provides helpers for pattern matching and date-format validation used
by the rule engine.
"""

import re
from functools import lru_cache


@lru_cache(maxsize=256)
def _compile(pattern: str, flags: int = re.IGNORECASE | re.DOTALL) -> re.Pattern:
    """Compile and cache a regex pattern."""
    return re.compile(pattern, flags)


def any_pattern_matches(text: str, patterns: list[str]) -> bool:
    """
    Return True if at least one *pattern* matches anywhere in *text*.
    """
    for pat_str in patterns:
        try:
            if _compile(pat_str).search(text):
                return True
        except re.error:
            continue
    return False


def find_all_matches(text: str, patterns: list[str]) -> list[str]:
    """
    Return every substring in *text* matched by any pattern in *patterns*.
    """
    results: list[str] = []
    for pat_str in patterns:
        try:
            results.extend(_compile(pat_str).findall(text))
        except re.error:
            continue
    return results


_DD_MM_YYYY = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def is_ddmmyyyy(date_str: str) -> bool:
    """Return True if *date_str* exactly matches DD/MM/YYYY."""
    return bool(_DD_MM_YYYY.match(date_str.strip()))
