"""
config.py — Application-level configuration for CarbonGPT.

Centralises paths and runtime settings so every module reads
from a single source of truth.  Add new settings here rather
than scattering hard-coded values across the codebase.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------

# Absolute path to the repo root (one level above this file's package)
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

# Where uploaded .docx files will be written to disk
UPLOAD_DIR: Path = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Where YAML rule files live
RULES_DIR: Path = BASE_DIR / "carbongpt" / "rules"

# ---------------------------------------------------------------------------
# API settings
# ---------------------------------------------------------------------------

APP_TITLE: str = "CarbonGPT"
APP_VERSION: str = "0.1.0"
APP_DESCRIPTION: str = (
    "Modular carbon compliance analysis tool. "
    "Upload a monitoring-report document and receive structured findings."
)

# Uvicorn host / port (consumed by main.py when run directly)
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "3000"))
