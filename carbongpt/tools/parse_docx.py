"""
parse_docx.py — Extract structured content from a Word (.docx) document.

The parser walks every paragraph in document order and groups body
text under the most-recently-seen heading.  Heading 1 and Heading 2
styles are both treated as section boundaries.

Returned structure
------------------
{
    "sections": {
        "<Heading text>": "<accumulated paragraph text>",
        ...
    }
}

An implicit "PREAMBLE" key collects any text that appears before
the first heading so that no content is silently dropped.
"""

from pathlib import Path
from docx import Document
from docx.oxml.ns import qn


# Heading styles recognised as section boundaries
_HEADING_STYLES = {"Heading 1", "Heading 2"}

# Fallback bucket for paragraphs before the first heading
_PREAMBLE_KEY = "PREAMBLE"


def _is_heading(paragraph) -> bool:
    """Return True if the paragraph uses a recognised heading style."""
    return paragraph.style.name in _HEADING_STYLES


def parse_docx(file_path: str | Path) -> dict:
    """
    Parse a .docx file and return a sections dictionary.

    Parameters
    ----------
    file_path:
        Absolute or relative path to the .docx file.

    Returns
    -------
    dict with a single key ``"sections"`` whose value is an ordered
    mapping of heading → body-text.

    Raises
    ------
    FileNotFoundError  — if the path does not exist.
    ValueError         — if the file is not a valid .docx document.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    try:
        doc = Document(str(path))
    except Exception as exc:
        raise ValueError(f"Could not open document '{path}': {exc}") from exc

    sections: dict[str, str] = {}
    current_heading: str = _PREAMBLE_KEY
    accumulated_lines: list[str] = []

    def _flush() -> None:
        """Commit accumulated lines to the current heading bucket."""
        text = " ".join(accumulated_lines).strip()
        if current_heading in sections:
            # If the same heading appears more than once, append content
            sections[current_heading] = (sections[current_heading] + " " + text).strip()
        else:
            sections[current_heading] = text
        accumulated_lines.clear()

    for para in doc.paragraphs:
        text = para.text.strip()

        if not text:
            # Skip blank paragraphs but keep accumulated content
            continue

        if _is_heading(para):
            # Flush any body text collected under the previous heading
            _flush()
            current_heading = text
        else:
            accumulated_lines.append(text)

    # Flush the last section
    _flush()

    # Drop the preamble bucket if it ended up empty
    if _PREAMBLE_KEY in sections and not sections[_PREAMBLE_KEY]:
        del sections[_PREAMBLE_KEY]

    return {"sections": sections}
