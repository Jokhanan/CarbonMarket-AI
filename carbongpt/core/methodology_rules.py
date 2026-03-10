"""
Methodology-driven rules for Setup flow.

Centralizes derivable metadata so the UI can auto-fill fields
instead of asking the user redundant questions.
"""

CREDITING_PERIOD_DEFAULTS = {
    "GoldStandard": 5,
    "Verra": 7,
    "CDM": 7,
}

METHODOLOGY_METADATA = {
    "TPDDTEC": {
        "activity_type": "Energy efficiency",
        "sectoral_scope": "Energy demand",
        "scale_options": ["Micro-scale", "Small-scale"],
        "fuel_field_mode": "methodology_choices",
    },
    "VM0050": {
        "activity_type": "Energy efficiency",
        "sectoral_scope": "Energy demand",
        "scale_options": [],
        "fuel_field_mode": "methodology_choices",
    },
    "ACM0002": {
        "activity_type": "Greenfield",
        "sectoral_scope": "Energy industries (renewable sources)",
        "scale_options": ["Large-scale"],
        "fuel_field_mode": "not_applicable",
    },
    "AMS-I.D.": {
        "activity_type": "Greenfield",
        "sectoral_scope": "Energy industries (renewable sources)",
        "scale_options": ["Small-scale"],
        "fuel_field_mode": "not_applicable",
    },
}


def get_methodology_metadata(code):
    if not code:
        return None
    normalized = code.upper().replace("GS-", "").strip()
    meta = METHODOLOGY_METADATA.get(normalized)
    if meta:
        return dict(meta)
    for key, val in METHODOLOGY_METADATA.items():
        if key.upper() == normalized:
            return dict(val)
    return None


def get_crediting_period_default(standard):
    return CREDITING_PERIOD_DEFAULTS.get(standard, 7)


def has_methodology_fuel_choices(code, meth_parsed=None):
    if meth_parsed:
        context_dims = meth_parsed.get("context_dimensions", [])
        fuel_keys = {"baseline_fuel", "project_fuel"}
        for dim in context_dims:
            if dim.get("dimension_key", "") in fuel_keys:
                return True
        return False
    meta = get_methodology_metadata(code)
    if not meta:
        return False
    return meta.get("fuel_field_mode") == "methodology_choices"
