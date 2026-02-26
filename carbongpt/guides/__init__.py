"""
Guide registry for CarbonGPT AI review.

Maps (standard, doc_type) pairs to the appropriate guide module
for AI-powered section-by-section document review.
"""

import importlib
from typing import Any

GUIDE_REGISTRY: dict[tuple[str, str], str] = {
    ("GoldStandard", "MR"): "carbongpt.guides.gs_mr_perfcert_v1_2",
    ("GoldStandard", "PDD"): "carbongpt.guides.gs_pdd_v1_5",
    ("GoldStandard", "PoA-DD"): "carbongpt.guides.gs_poa_dd_v2_2",
    ("GoldStandard", "VPA-DD"): "carbongpt.guides.gs_vpa_dd_v2_3",
    ("Verra", "VCS-PD"): "carbongpt.guides.vcs_pd_v4_4",
    ("Verra", "VCS-MR"): "carbongpt.guides.vcs_mr_v4_4",
    ("Verra", "VCS-ValVer"): "carbongpt.guides.vcs_valver_v4_4",
}

DOC_TYPE_LABELS: dict[str, str] = {
    "MR": "Monitoring Report",
    "PDD": "Project Design Document",
    "PoA-DD": "Programme of Activity Design Document",
    "VPA-DD": "VPA Design Document",
    "VCS-PD": "VCS Project Description",
    "VCS-MR": "VCS Monitoring Report",
    "VCS-ValVer": "VCS Joint Validation & Verification Report",
}


def load_guide(standard: str, doc_type: str) -> Any:
    key = (standard, doc_type)
    module_path = GUIDE_REGISTRY.get(key)
    if module_path is None:
        raise ValueError(
            f"No AI review guide registered for standard={standard!r}, "
            f"doc_type={doc_type!r}. Available: {list(GUIDE_REGISTRY.keys())}"
        )
    return importlib.import_module(module_path)


def list_supported_doc_types(standard: str) -> list[str]:
    return sorted(dt for (std, dt) in GUIDE_REGISTRY if std == standard)


def is_ai_review_supported(standard: str, doc_type: str) -> bool:
    return (standard, doc_type) in GUIDE_REGISTRY
