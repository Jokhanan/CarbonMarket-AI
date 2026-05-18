"""
POST /v1/calculate — endpoint stateless pour le calculateur Navigator.

Pas de base de données requise. Reçoit les paramètres du frontend React,
route vers le bon calculateur Python, retourne les résultats multi-année.

Conversion unités :
  Navigator envoie baseline_consumption / project_consumption en t/stove/an
  (le frontend convertit Pb t/jour × 365 avant d'appeler cet endpoint).
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["calculate"])

# Alias de méthodologie → identifiant interne
_METH_ALIASES = {
    "GS_RECH_V5": "RECH",
    "GS-RECH-V5": "RECH",
    "GS-RECH": "RECH",
    "RECH": "RECH",
    "GS_TPDDTEC_V4": "TPDDTEC",
    "GS-TPDDTEC-V4": "TPDDTEC",
    "GS-TPDDTEC": "TPDDTEC",
    "TPDDTEC": "TPDDTEC",
    "VM0050_V1": "VM0050",
    "VM0050-V1": "VM0050",
    "VM0050": "VM0050",
    "GS_MECD_V2": "MECD",
    "GS-MECD": "MECD",
    "MECD": "MECD",
}


class CalculateRequest(BaseModel):
    methodology: str
    params: dict[str, Any]
    crediting_years: int = 5
    start_year: int = 2025
    method_id: str | None = None   # pour TPDDTEC : "method_1" | "method_2" | "method_3"


@router.post("/calculate")
def calculate(req: CalculateRequest):
    """
    Calcule les réductions d'émissions pour une méthodologie donnée.

    Paramètres communs (dans req.params) :
      fNRB               : float  — fraction biomasse non-renouvelable
      baseline_consumption: float  — t/stove/an (Pb_Navigator × 365)
      project_consumption : float  — t/stove/an (Pp_Navigator × 365)
      N_distributed      : int    — foyers distribués
      adoption_rate      : float  — taux d'adoption base (0–1)
      stacking_factor    : float  — fraction gardant l'ancien foyer (0–1)
      HNb                : float  — personnes par foyer
      baseline_fuel      : str    — "wood" | "charcoal"
      project_fuel       : str    — "wood" | "charcoal"

    Paramètres spécifiques RECH v5 :
      DAF                : float  — NetZero Ambition Factor (GS Tool 05)
      embodied           : float  — tCO2e/unité (défaut 0.017)
      n_units            : int    — unités pour LE embodied

    Retourne l'enveloppe standard CarbonGPT :
      { calculation_steps, years, summary, parameters_used, warnings }
    """
    meth_key = req.methodology.upper().replace(" ", "_").replace("-", "_")
    meth_key_dash = req.methodology.upper().replace(" ", "-").replace("_", "-")
    meth = _METH_ALIASES.get(meth_key) or _METH_ALIASES.get(meth_key_dash)

    if not meth:
        raise HTTPException(
            status_code=400,
            detail=f"Méthodologie '{req.methodology}' non supportée. "
                   f"Valeurs acceptées : {list(set(_METH_ALIASES.values()))}",
        )

    p = req.params
    cy = max(1, min(req.crediting_years, 10))
    sy = req.start_year

    try:
        if meth == "RECH":
            from carbongpt.core.gs_rech_v5 import calculate_gs_rech_v5_er
            return calculate_gs_rech_v5_er(p, crediting_years=cy, start_year=sy)

        elif meth == "TPDDTEC":
            from carbongpt.core.er_simulator import calculate_cookstove_er
            return calculate_cookstove_er(
                p, crediting_years=cy, start_year=sy,
                methodology="TPDDTEC", method_id=req.method_id,
            )

        elif meth == "VM0050":
            from carbongpt.core.er_simulator import calculate_cookstove_er
            return calculate_cookstove_er(
                p, crediting_years=cy, start_year=sy, methodology="VM0050",
            )

        elif meth == "MECD":
            from carbongpt.core.mecd_simulator import calculate_mecd_er
            from carbongpt.core.er_simulator import _normalize_mecd_result
            raw = calculate_mecd_er(p, crediting_years=cy, start_year=sy)
            return _normalize_mecd_result(raw, cy, sy)

    except Exception as exc:
        logger.exception("Erreur calcul %s", req.methodology)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
