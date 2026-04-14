# PROMPT REPLIT AI — CarbonGPT : Refactorisation des moteurs de calcul carbone

## CONSIGNES GÉNÉRALES

Tu travailles sur une application existante **CarbonGPT** (FastAPI + Streamlit).
**RÈGLES ABSOLUES :**
1. Ne crée aucun nouveau fichier sauf si demandé explicitement.
2. Ne supprime aucun fichier existant.
3. Modifie uniquement les fichiers indiqués ci-dessous.
4. Garde toutes les routes FastAPI, toutes les classes Streamlit et toute la structure de dossiers intacte.
5. Tes modifications remplacent UNIQUEMENT la logique de calcul à l'intérieur des fonctions existantes, pas leurs signatures externes.

## FICHIERS À MODIFIER

- `carbongpt/core/parameter_engine.py` — Remplace les blocs de paramètres par méthodologie
- `carbongpt/core/er_simulator.py` — Remplace les fonctions de calcul ER par méthodologie
- `carbongpt/core/methodology_rules.py` — Remplace les arbres de décision et validations

---

## PARTIE 1 — ARBRE DE DÉCISION GLOBAL (methodology_rules.py)

L'utilisateur choisit d'abord le **standard** puis la **méthodologie** :

```
Standard choisi ?
├── Gold Standard → Type de projet ?
│   ├── Foyers biomasse / solaire / rétention (PAS mesuré en continu)
│   │   → TPDDTEC v4.0
│   └── Appareils mesurés en continu (LPG metré, induction, EPC, biogas, bioéthanol)
│       → GS-MECD v1.2
└── Verra (VCS)
    → VM0050 v1.0
```

### Règle TPDDTEC vs MECD (Gold Standard)

| Critère | TPDDTEC v4.0 | MECD v1.2 |
|---|---|---|
| Combustible projet mesuré en continu | NON | OUI (obligatoire) |
| Technologie projet | Foyers biomasse améliorés, rétention, solaire, non-solaire | LPG metré, induction, EPC, biogas, bioéthanol |
| Efficacité thermique projet ≥ | 20% | 40% |
| Puissance max | < 150 kW | < 150 kW |
| Fuel switch seul (sans tech switch) | Non créditable | Non créditable |

---

## PARTIE 2 — TPDDTEC v4.0 (Gold Standard)

### 2.1 — Choix de méthode de calcul (dans methodology_rules.py)

```python
def select_tpddtec_method(baseline_fuel: str, project_fuel: str, project_scale: str) -> str:
    """
    Retourne 'method_1', 'method_2' ou 'method_3'.
    
    Method 1 : même combustible baseline et projet, réduction par efficacité uniquement
               → applicable à toutes les échelles
               → nécessite BFT + PFT (Kitchen Performance Test terrain)
    
    Method 2 : même combustible (BOIS UNIQUEMENT), réduction par efficacité,
               consommation baseline par DÉFAUT (0.5 t/capita/an)
               → UNIQUEMENT micro (≤ 10 000 tCO2e/an) ou small (≤ 60 GWh/an économies)
               → nécessite uniquement PFT
    
    Method 3 : combustibles différents (fuel switch) OU même combustible avec
               facteurs d'émission différents
               → applicable à toutes les échelles
               → si projet introduit combustible fossile : UNIQUEMENT crédit efficacité
                 (EF_p = EF_b dans les calculs)
               → nécessite BFT + PFT
    """
    if baseline_fuel == project_fuel:
        if baseline_fuel == 'wood' and project_scale in ('micro', 'small'):
            return 'method_2'  # peut utiliser méthode 1 ou 2; méthode 2 si défaut appliqué
        return 'method_1'
    else:
        return 'method_3'
```

### 2.2 — Définition de l'échelle (dans methodology_rules.py)

```python
def classify_tpddtec_scale(annual_er_tco2e: float, annual_energy_savings_gwh: float) -> str:
    """
    Micro  : ER annuel ≤ 10 000 tCO2e/an (calculé ex-ante)
    Small  : économies d'énergie ≤ 60 GWh/an (ou ≤ 180 GWhth/an en thermique)
    Large  : économies d'énergie > 60 GWh/an (= > 180 GWhth/an)
    Note : Large ne peut PAS utiliser la suppressed demand baseline.
    """
    if annual_er_tco2e <= 10_000:
        return 'micro'
    elif annual_energy_savings_gwh <= 60:
        return 'small'
    else:
        return 'large'
```

### 2.3 — Paramètres TPDDTEC (dans parameter_engine.py)

```python
TPDDTEC_DEFAULTS = {
    # Combustibles — valeurs par défaut IPCC/Méthodologie
    'NCV_wood_TJ_per_ton': 0.0156,           # TJ/tonne (bois)
    'NCV_charcoal_TJ_per_ton': 0.0295,       # TJ/tonne (charbon de bois)
    
    'EF_CO2_wood_tCO2_per_TJ': 112.0,        # tCO2/TJ bois (IPCC)
    'EF_CO2_charcoal_combustion_tCO2_per_TJ': 112.0,   # combustion seule
    'EF_CO2_charcoal_with_prod_tCO2_per_TJ': 165.22,   # avec production (défaut)
    'EF_CO2_charcoal_cap_tCO2_per_TJ': 197.15,          # plafond absolu

    'EF_nonCO2_wood_AR5_tCO2e_per_TJ': 9.46,      # AR5
    'EF_nonCO2_wood_AR4_tCO2e_per_TJ': 8.692,     # AR4
    
    'EF_nonCO2_charcoal_combustion_AR5': 5.865,    # combustion seule, AR5
    'EF_nonCO2_charcoal_with_prod_AR5': 44.83,     # avec production, AR5 (défaut)
    'EF_nonCO2_charcoal_cap_AR5': 92.29,           # plafond AR5
    
    'EF_nonCO2_charcoal_combustion_AR4': 5.298,
    'EF_nonCO2_charcoal_with_prod_AR4': 40.26,
    'EF_nonCO2_charcoal_cap_AR4': 82.90,

    # Consommation baseline par défaut (Method 2 uniquement)
    'SFC_b_default_wood_t_per_capita_year': 0.5,   # tonnes/capita/an
    
    # Plafonds sur P_b,y (consommation baseline mesurée)
    'Pb_threshold_t_per_person_year': 0.75,  # au-delà → justification tierce requise
    'Pb_cap_t_per_person_year': 0.95,        # plafond absolu
    
    # Leakage Option 1
    'leakage_default_factor': 0.95,   # multiplier sur ER brut
    
    # Limites de Scale
    'micro_threshold_tCO2e_per_year': 10_000,
    'small_threshold_energy_GWh_per_year': 60,
    'small_threshold_thermal_GWhth_per_year': 180,
    
    # Efficacité minimale projet
    'min_project_efficiency_fraction': 0.20,  # 20%
    'max_device_power_kW': 150,
}
```

### 2.4 — Paramètres saisis par l'utilisateur (TPDDTEC)

```python
TPDDTEC_USER_INPUTS = {
    # --- Projet ---
    'baseline_fuel': str,           # 'wood', 'charcoal', 'lpg', 'kerosene', 'coal'
    'project_fuel': str,            # idem
    'baseline_technology': str,     # ex: 'three_stone_fire', 'traditional_charcoal_stove'
    'project_technology': str,      # ex: 'improved_biomass_stove', 'solar_cooker'
    
    # --- Taille du projet ---
    'num_devices_total': int,        # nombre total d'appareils distribués
    'avg_household_size': float,     # personnes par ménage (pour convertir t/capita → t/device)
    'deployment_schedule': dict,     # {year: devices_deployed} ou mode 'upfront'/'monthly'/'s_curve'
    'tech_lifetime_years': int,      # durée de vie technique (ICS 3)
    'crediting_period_years': int,   # 5, 7 ou 10 ans
    
    # --- Performance ---
    # Method 1 : Économies spécifiques (issues du KPT terrain)
    'SFS_p_b_y_kg_per_tech_day': float,  # économies de combustible en kg/appareil/jour
                                          # = P_b,y - P_p,y convertis en /jour
    
    # Method 2 : Consommation projet seulement (défaut pour baseline)
    'SFC_p_kg_per_tech_day': float,      # consommation projet en kg/appareil/jour (issue PFT)
    # SFC_b calculé auto depuis 0.5 t/capita/an ÷ household_size ÷ 365
    
    # Method 3 : Émissions spécifiques (issues du KPT terrain)
    'SE_b_CO2_tCO2_per_tech_day': float,     # = P_b,y × NCV_b × EF_CO2_b / 365
    'SE_b_nonCO2_tCO2e_per_tech_day': float, # = P_b,y × NCV_b × EF_nonCO2_b / 365
    'SE_p_CO2_tCO2_per_tech_day': float,     # = P_p,y × NCV_p × EF_CO2_p / 365
    'SE_p_nonCO2_tCO2e_per_tech_day': float, # = P_p,y × NCV_p × EF_nonCO2_p / 365
    # ATTENTION: si projet fossil fuel → SE_p,CO2 calculé avec EF_b,CO2 (pas EF_p)
    
    # --- Émissions ---
    'EF_b_CO2_tCO2_per_TJ': float,    # défaut selon fuel (voir table ci-dessus)
    'EF_b_nonCO2_tCO2e_per_TJ': float,
    'EF_p_CO2_tCO2_per_TJ': float,
    'EF_p_nonCO2_tCO2e_per_TJ': float,
    'NCV_b_TJ_per_ton': float,         # défaut selon fuel
    'NCV_p_TJ_per_ton': float,
    
    # --- fNRB ---
    'fNRB': float,                     # 0.0 à 1.0 (ex : 0.65)
    'fNRB_fixed_ex_ante': bool,        # True = fixé pour toute la période; False = biennial
    # Omis si baseline fossil fuel
    
    # --- Usage rate ---
    'usage_rate_year1': float,         # fraction, ex: 0.90 (issu usage survey)
    'usage_rate_decay_per_year': float, # ex: 0.03 = -3%/an
    'usage_rate_floor': float,         # plancher, ex: 0.50
    
    # --- Leakage ---
    'leakage_option': int,             # 1 = default 0.95; 2 = leakage quantifié
    'leakage_tCO2e_per_year': float,   # si option 2, valeur annuelle estimée
    
    # --- GWP ---
    'gwp_version': str,                # 'AR4' ou 'AR5'
    
    # --- Charbon de bois (si applicable) ---
    'charcoal_include_production_emissions': bool,  # True = EF 165.22; False = EF 112
}
```

### 2.5 — Équations TPDDTEC (dans er_simulator.py)

**IMPORTANT — Unités centrales :**
- `N_b_p_y` = technology-days = Σ des appareils actifs × jours calendaires dans l'année y
- `U_p_y` = fraction pondérée d'utilisation (moyenne par cohorte d'âge, issue usage survey)
- `SFS`, `SE` = valeurs par appareil et par JOUR

```python
def compute_N_b_p_y(devices_by_year: dict, year: int, tech_lifetime: int) -> float:
    """
    Calcule le nombre de technology-days pour l'année y.
    
    = Somme sur tous les appareils actifs (non périmés) de leur nombre de jours
      présents chez l'utilisateur final dans l'année y.
    
    Approche simplifiée :
    N_b_p_y = active_devices_in_year_y × 365
    
    où active_devices_in_year_y = appareils déployés depuis ≤ tech_lifetime_years
    """
    active = 0
    for deploy_year, qty in devices_by_year.items():
        age = year - deploy_year
        if 0 <= age < tech_lifetime:
            active += qty
    return active * 365  # jours/an


def compute_U_p_y(usage_rate_year1: float, decay: float, floor: float, year: int) -> float:
    """
    Taux d'utilisation cumulatif pondéré pour l'année y.
    En pratique ex-ante : décroissance linéaire avec plancher.
    U_p_y = max(usage_rate_year1 - (year - 1) × decay, floor)
    """
    return max(usage_rate_year1 - (year - 1) * decay, floor)


def calculate_ER_tpddtec_method1(
    N_b_p_y: float,   # technology-days
    U_p_y: float,     # fraction
    SFS_p_b_y: float, # kg/technology*day — économies spécifiques issues KPT
    NCV_b: float,     # TJ/tonne (défaut 0.0156 pour bois)
    fNRB: float,      # fraction
    EF_b_CO2: float,  # tCO2/TJ
    EF_b_nonCO2: float, # tCO2e/TJ (0 si fossil fuel)
    leakage_option: int,
    LE_p_y: float = 0.0,  # si option 2
) -> float:
    """
    TPDDTEC Eq. 1 — Même combustible, efficacité uniquement.
    
    ER_y = Σ(b,p) [N_b,p,y × U_p,y × SFS_p,b,y × NCV_b,fuel
                   × (fNRB_b,y × EF_b,f,CO2 + EF_b,f,nonCO2)] − Σ LE_p,y
    
    SFS_p_b_y converti : kg/tech/day → tonnes/tech/day = SFS_p_b_y / 1000
    NCV_b en TJ/tonne
    Résultat : tCO2e/an
    """
    SFS_tonnes = SFS_p_b_y / 1000.0  # kg → tonnes par tech*day
    
    gross_ER = N_b_p_y * U_p_y * SFS_tonnes * NCV_b * (fNRB * EF_b_CO2 + EF_b_nonCO2)
    
    if leakage_option == 1:
        return gross_ER * 0.95
    else:
        return gross_ER - LE_p_y


def calculate_ER_tpddtec_method2(
    N_b_p_y: float,    # technology-days
    U_p_y: float,      # fraction
    SFC_b_y: float,    # tonnes/technology*day — DÉFAUT: 0.5 t/cap/an ÷ hh_size ÷ 365
    SFC_p_y: float,    # tonnes/technology*day — mesuré (PFT)
    NCV_b: float,      # TJ/tonne (défaut 0.0156)
    fNRB: float,
    EF_b_CO2: float,   # défaut 112 tCO2/TJ
    EF_b_nonCO2: float, # défaut 9.46 tCO2e/TJ (AR5)
    leakage_option: int,
    LE_p_y: float = 0.0,
) -> float:
    """
    TPDDTEC Eq. 2 — Bois uniquement, consommation baseline par défaut.
    UNIQUEMENT micro ou small scale.
    
    ER_y = N_b,p,y × U_p,y × (SFC_b,y − SFC_p,y)
           × (fNRB_y × EF_b,f,CO2 + EF_b,f,nonCO2) × NCV_b,fuel − Σ LE_p,y
    
    SFC_b_y par défaut = 0.5 / household_size / 365  (tonnes/tech/day)
    """
    fuel_savings = SFC_b_y - SFC_p_y  # tonnes/tech/day
    gross_ER = N_b_p_y * U_p_y * fuel_savings * (fNRB * EF_b_CO2 + EF_b_nonCO2) * NCV_b
    
    if leakage_option == 1:
        return gross_ER * 0.95
    else:
        return gross_ER - LE_p_y


def calculate_ER_tpddtec_method3(
    N_b_p_y: float,
    U_p_y: float,
    SE_b_CO2: float,      # tCO2/technology*day (P_b × NCV_b × EF_b_CO2 / 365)
    SE_b_nonCO2: float,   # tCO2e/technology*day
    SE_p_CO2: float,      # tCO2/technology*day
    SE_p_nonCO2: float,   # tCO2e/technology*day
    fNRB_b: float,         # fNRB du BASELINE (pas du projet)
    project_uses_fossil: bool,  # True = LPG, kérosène, charbon fossile
    leakage_option: int,
    LE_p_y: float = 0.0,
) -> float:
    """
    TPDDTEC Eq. 3, 4, 5 — Combustibles différents.
    
    BE_y = Σ(b,p) [N × U × (fNRB_b × SE_b,CO2 + SE_b,nonCO2)]
    PE_y = Σ(b,p) [N × U × (fNRB_b × SE_p,CO2 + SE_p,nonCO2)]
    
    RÈGLE CRITIQUE :
    - Si projet introduit combustible FOSSILE :
        → EF_p = EF_b (même facteur) : SE_p,CO2 calculé avec EF_b,CO2
        → fNRB_b appliqué dans PE aussi (car baseline était biomasse)
        → seule l'efficacité est créditée, pas le fuel switch
    - Si projet utilise combustible fossile en projet :
        → EF_b,f,nonCO2 OMIS du côté PE (fossil fuel : pas de non-CO2)
        → fNRB EXCLU de PE (fossil fuel n'a pas de fNRB)
        → Mais fNRB_b INCLUS dans BE (baseline biomasse)
    
    ER_y = BE_y − PE_y − Σ LE_p,y
    """
    BE_y = N_b_p_y * U_p_y * (fNRB_b * SE_b_CO2 + SE_b_nonCO2)
    
    if project_uses_fossil:
        # Combustible fossile projet : fNRB exclu de PE, nonCO2 exclu
        PE_y = N_b_p_y * U_p_y * SE_p_CO2
    else:
        # Biomasse renouvelable / biogas → fNRB_b appliqué côté PE aussi
        # (pour biogas/renouvelable : SE_p,CO2 = 0 si EF_CO2 = 0)
        PE_y = N_b_p_y * U_p_y * (fNRB_b * SE_p_CO2 + SE_p_nonCO2)
    
    net_ER = BE_y - PE_y
    
    if leakage_option == 1:
        return net_ER * 0.95
    else:
        return net_ER - LE_p_y


def calculate_SFC_b_default(household_size: float) -> float:
    """
    Calcule SFC_b par défaut pour Method 2.
    Défaut: 0.5 tonnes/capita/an de bois.
    = 0.5 / household_size / 365 en tonnes/tech/day.
    """
    return 0.5 / household_size / 365.0


def validate_SFC_b_caps(Pb_t_per_person_year: float) -> dict:
    """
    Vérifie les plafonds sur la consommation baseline mesurée.
    Retourne warnings et flags.
    """
    result = {'value': Pb_t_per_person_year, 'warnings': [], 'capped': False}
    if Pb_t_per_person_year > 0.95:
        result['warnings'].append("ERREUR: P_b dépasse le plafond absolu de 0.95 t/pers/an. Valeur plafonnée à 0.95.")
        result['value'] = 0.95
        result['capped'] = True
    elif Pb_t_per_person_year > 0.75:
        result['warnings'].append("ATTENTION: P_b > 0.75 t/pers/an. Justification par étude tierce requise.")
    return result
```

---

## PARTIE 3 — VM0050 v1.0 (Verra/VCS)

### 3.1 — Paramètres utilisateur VM0050

```python
VM0050_DEFAULTS = {
    # Consommation baseline par défaut
    'BC_b_wood_t_per_capita_year': 0.50,     # bois : 0.5 t/capita/an
    'BC_b_charcoal_t_per_capita_year': 0.13, # charbon de bois : 0.13 t/capita/an
    
    # NCV
    'NCV_wood_TJ_per_ton': 0.0156,
    'NCV_charcoal_TJ_per_ton': 0.0295,
    
    # EF CO2 (tCO2/TJ)
    'EF_CO2_wood': 112.0,
    'EF_CO2_charcoal_combustion': 112.0,
    'EF_CO2_charcoal_with_prod': 165.22,
    
    # EF nonCO2 (tCO2e/TJ, AR5)
    'EF_nonCO2_wood_AR5': 9.46,
    'EF_nonCO2_charcoal_combustion_AR5': 5.865,
    
    # Leakage
    'leakage_factor': 0.95,   # Eq. 11: (BE - PE) × 0.95 − LERB
    
    # TDL électricité (valeur défaut — à personnaliser)
    'TDL_default': 0.05,   # 5% pertes T&D
    
    # Transport : seuil 200 km
    'transport_distance_threshold_km': 200,
    
    # fNRB incertitude (si TOOL30 Tier 3)
    'fNRB_TOOL30_uncertainty_discount': 0.26,  # 26% de réduction sur fNRB TOOL30
}

VM0050_USER_INPUTS = {
    # --- Appareils ---
    'baseline_device_types': list,     # liste de dicts: {id, fuel, NCV, EF_CO2, EF_nonCO2}
    'project_device_types': list,      # liste de dicts: {id, fuel, type}
    'num_devices_by_batch': dict,      # {batch_k: N_j_k}
    'avg_household_size': float,
    'tech_lifetime_years': int,
    'crediting_period_years': int,
    
    # --- Consommation baseline ---
    'BC_b_method': str,                # 'measurement' ou 'default'
    'BC_b_t_per_device_year': float,   # si measurement; sinon calculé depuis défauts
    
    # --- Consommation projet ---
    'BC_p_t_per_device_year': float,   # KPT ou mesure directe ou achat (fossile)
    'NCV_p_TJ_per_ton': float,
    
    # --- Efficacités (pour cross-check stove stacking) ---
    'eta_new_avg': float,  # efficacité moyenne projet
    'eta_old_avg': float,  # efficacité moyenne baseline
    
    # --- fNRB ---
    'fNRB': float,
    'fNRB_source': str,   # 'IPCC_Tier1', 'national_Tier2', 'TOOL33_Tier2', 'TOOL30_Tier3'
    # Si TOOL30_Tier3 → appliquer discount 26%: fNRB_applied = fNRB × (1 - 0.26)
    
    # --- Électricité (si projet électrique) ---
    'EC_p_MWh_per_device_year': float, # consommation élec mesurée
    'EF_el_tCO2e_per_MWh': float,      # facteur émission réseau
    'TDL': float,                       # pertes T&D (fraction)
    
    # --- LPG spécifique ---
    'project_uses_LPG': bool,
    'LPG_upstream_leakage_tCO2e': float,  # calculé via CDM TOOL15
    'LPG_monitoring_end_date': date,       # doit être ≤ 31/12/2045
    
    # --- Leakage renouvelable ---
    'LERB_y_tCO2e': float,   # leakage biomasse renouvelable (CDM TOOL16)
    
    # --- PE autres ---
    'PE_transport_tCO2e': float,    # si distance > 200 km (CDM TOOL12)
    'PE_production_tCO2e': float,   # biomasse renouvelable (CDM TOOL16)
    'PE_fugitive_tCO2e': float,
    'PE_backup_tCO2e': float,
    
    # --- Usage ---
    'adoption_rate_n_j_k_y': float,  # fraction d'appareils encore actifs année y
}
```

### 3.2 — Équations VM0050 (dans er_simulator.py)

```python
def calculate_BE_vm0050(
    EC_i_y: float,      # TJ — énergie baseline = BC_b × NCV_b (par appareil)
    N_j_k_y: int,       # nombre d'appareils projet (batch k, type j)
    n_j_k_y: float,     # fraction en fonctionnement année y
    EF_b_CO2: float,    # tCO2/TJ
    EF_b_nonCO2: float, # tCO2e/TJ
    fNRB: float,        # 0 si fossil fuel baseline
) -> float:
    """
    VM0050 Eq. 1 — Émissions baseline.
    BE_y = Σ_i,j,k [EC_i,y × N_j,k,y × n_j,k,y × (EF_b,i,CO2 × fNRB_y + EF_b,i,nonCO2)]
    
    EC_i,y = BC_b,i,y × NCV_b,i  (Eq. 2)
    """
    return EC_i_y * N_j_k_y * n_j_k_y * (EF_b_CO2 * fNRB + EF_b_nonCO2)


def calculate_EC_baseline_vm0050(BC_b: float, NCV_b: float) -> float:
    """VM0050 Eq. 2 : EC_i,y = BC_b,i,y × NCV_b,i"""
    return BC_b * NCV_b


def stove_stacking_cap_vm0050(
    EC_i_y: float,    # consommation baseline calculée
    EC_p_y: float,    # énergie projet (TJ)
    eta_new: float,   # efficacité moyenne projet
    eta_old: float,   # efficacité moyenne baseline
) -> float:
    """
    VM0050 Eq. 3 — Cross-check stove stacking.
    EC_est,y = EC_p,y × (eta_new_avg_y / eta_old_avg)
    
    Si EC_i_y > EC_est_y → cap = EC_est_y
    EXCEPTION: appareils électriques ≥ 70% efficacité → référence, pas cap obligatoire.
    
    Retourne la valeur plafonnée à utiliser dans BE.
    """
    EC_est_y = EC_p_y * (eta_new / eta_old)
    if EC_i_y > EC_est_y:
        return EC_est_y  # cap appliqué
    return EC_i_y


def calculate_PE_biomass_vm0050(
    BC_p: float,        # tonnes/appareil/an
    N_j_k_y: int,
    NCV_p: float,       # TJ/tonne
    n_j_k_y: float,
    EF_p_CO2: float,
    EF_p_nonCO2: float,
    fNRB: float,        # même fNRB que baseline
) -> float:
    """
    VM0050 Eq. 7 — Émissions projet (biomasse, fossile, bioéthanol).
    PE_energy,y = Σ_j,k [BC_p,j,k,y × N_j,k,y × NCV_p,j × n_j,k,y
                          × (EF_p,j,CO2 × fNRB + EF_p,j,nonCO2)]
    
    Note: Pour biomasse renouvelable → EF_CO2 = 0 (pas fNRB = 0)
    """
    return BC_p * N_j_k_y * NCV_p * n_j_k_y * (EF_p_CO2 * fNRB + EF_p_nonCO2)


def calculate_PE_electric_vm0050(
    EC_p_MWh: float,    # MWh/appareil/an (mesuré)
    N_j_k_y: int,
    n_j_k_y: float,
    EF_el: float,       # tCO2e/MWh
    TDL: float,         # fraction (ex: 0.05 pour 5%)
) -> float:
    """
    VM0050 Eq. 8 — Émissions projet électrique.
    PE_energy,y = Σ_j,k [EC_p,j,k,y × N_j,k,y × n_j,k,y × EF_el,y × (1 + TDL_j,y)]
    
    CRITIQUE: (1 + TDL) — additionner les pertes, PAS soustraire!
    TDL représente l'électricité supplémentaire à produire pour compenser les pertes.
    """
    return EC_p_MWh * N_j_k_y * n_j_k_y * EF_el * (1.0 + TDL)


def calculate_net_ER_vm0050(
    BE_y: float,
    PE_y: float,          # PE_energy + PE_others
    LERB_y: float = 0.0,  # leakage biomasse renouvelable (CDM TOOL16)
) -> float:
    """
    VM0050 Eq. 11 — Réductions nettes.
    ER_y = (BE_y − PE_y) × 0.95 − LERB_y
    
    CRITIQUE: LERB est SOUSTRAIT, pas ajouté — c'est une émission de fuite!
    """
    return (BE_y - PE_y) * 0.95 - LERB_y


def apply_fNRB_uncertainty_discount(fNRB_raw: float, source: str) -> float:
    """
    Si fNRB calculé via CDM TOOL30 (Tier 3):
    fNRB appliqué = fNRB_raw × (1 - 0.26)
    Exemple: fNRB TOOL30 = 0.60 → fNRB appliqué = 0.60 × 0.74 = 0.444
    
    Pour autres sources (Tier 1, 2): pas de discount.
    """
    if source == 'TOOL30_Tier3':
        return fNRB_raw * (1.0 - 0.26)
    return fNRB_raw


def validate_LPG_sunset_vm0050(monitoring_end_date) -> dict:
    """
    VM0050 §4 cond. 11c : crédits impossibles pour périodes de monitoring
    se terminant après le 31 décembre 2045.
    """
    from datetime import date
    sunset = date(2045, 12, 31)
    if monitoring_end_date > sunset:
        return {
            'eligible': False,
            'error': f"Crédits LPG impossibles: fin de monitoring ({monitoring_end_date}) "
                     f"dépasse la date limite du 31/12/2045 (VM0050 §4 cond. 11c)."
        }
    return {'eligible': True, 'error': None}
```

---

## PARTIE 4 — GS-MECD v1.2 (Gold Standard)

### 4.1 — Choix du cas (dans methodology_rules.py)

```python
def select_mecd_case(project_device_type: str) -> str:
    """
    Case 1 : Efficacité thermique déterminable → TOUS appareils sauf EPC.
             Inclut: induction, plaques électriques, LPG metré, biogas, bioéthanol.
    Case 2 : Facteurs autres qu'efficacité affectent l'énergie (pression).
             UNIQUEMENT: Electric Pressure Cooker (EPC) ou assimilé.
    """
    EPC_devices = ['electric_pressure_cooker', 'epc', 'pressure_cooker']
    if project_device_type.lower() in EPC_devices:
        return 'case_2'
    return 'case_1'
```

### 4.2 — Paramètres MECD

```python
MECD_USER_INPUTS = {
    # --- Appareils ---
    'project_device_type': str,   # 'induction', 'epc', 'lpg_metered', 'biogas', 'bioethanol'
    'num_devices': int,
    'tech_lifetime_years': int,
    'crediting_period_years': int,
    
    # --- Panier baseline (fuel basket) ---
    # Liste de dicts : chaque entry = un combustible dans le baseline
    'baseline_fuels': list,  # [{
                             #    'fuel': 'wood',
                             #    'share_pct': 70,        # % de ce combustible dans le mix
                             #    'P_b_kg_per_HH_day': 2.5, # consommation mesurée (KPT)
                             #    'NCV_TJ_per_ton': 0.0156,
                             #    'EF_CO2_tCO2_per_TJ': 112.0,
                             #    'EF_nonCO2_tCO2e_per_TJ': 9.46,
                             #    'fNRB': 0.65,
                             #    'eta_baseline_device': 0.12,  # efficacité appareil baseline
                             # }, {...}]
    # Note: sum(share_pct) doit = 100%
    
    # --- Case 2 seulement (EPC) ---
    'SC_b_TJ_per_test_per_person': float,  # consommation spécifique baseline (CCT)
    'SC_p_TJ_per_test_per_person': float,  # consommation spécifique projet (CCT)
    
    # --- Projet --- 
    'project_fuel': str,          # 'electricity', 'lpg', 'biogas', 'bioethanol'
    
    # Si projet électrique (Case 1):
    'EG_p_d_y_MWh_per_device_year': float,  # électricité mesurée/appareil/an
    'eta_p': float,                           # efficacité projet (fraction)
    'EF_el_tCO2e_per_MWh': float,            # facteur émission réseau (CDM TOOL05)
    'TDL': float,                             # pertes T&D (fraction)
    
    # Si projet combustible (LPG/biogas/bioéthanol, Case 1):
    'P_p_d_y_kg_per_device_year': float,    # fuel mesuré/appareil/an
    'NCV_p_TJ_per_ton': float,
    'EF_p_tCO2e_per_TJ': float,            # EF du combustible projet
    'eta_p': float,
    
    # --- fNRB ---
    'fNRB': float,
    'fNRB_update_mode': str,   # 'ex_ante_fixed' ou 'biennial'
    
    # --- Usage ---
    'usage_rate_year1': float,
    'usage_rate_decay_per_year': float,
    'usage_rate_floor': float,
}
```

### 4.3 — Équations MECD (dans er_simulator.py)

```python
def calculate_EF_b_useful_mecd(baseline_fuels: list) -> float:
    """
    MECD Eq. 1 — Facteur d'émission baseline par unité d'énergie UTILE.
    
    EF_b,useful = Σ_k Σ_i,j [P_b,i,j × %fuel_i × (EF_CO2_i × fNRB_i + EF_nonCO2_i) × NCV_i]
                  ÷ Σ_k Σ_i,j [P_b,i,j × %fuel_i × NCV_i × η_b,i,j]
    
    baseline_fuels: liste de dicts (voir VM0050_USER_INPUTS['baseline_fuels'] ci-dessus)
    
    Résultat: tCO2e / TJ d'énergie utile
    """
    numerator = 0.0
    denominator = 0.0
    
    for fuel in baseline_fuels:
        P = fuel['P_b_kg_per_HH_day'] / 1000.0  # kg → tonnes
        share = fuel['share_pct'] / 100.0
        NCV = fuel['NCV_TJ_per_ton']
        EF_CO2 = fuel['EF_CO2_tCO2_per_TJ']
        EF_nonCO2 = fuel['EF_nonCO2_tCO2e_per_TJ']
        fNRB = fuel.get('fNRB', 0.0)  # 0 si fossil fuel
        eta = fuel['eta_baseline_device']
        
        numerator += P * share * (EF_CO2 * fNRB + EF_nonCO2) * NCV
        denominator += P * share * NCV * eta
    
    if denominator == 0:
        raise ValueError("Dénominateur nul dans EF_b_useful — vérifier les données baseline")
    
    return numerator / denominator  # tCO2e/TJ utile


def calculate_EF_b_input_mecd_case2(baseline_fuels: list) -> float:
    """
    MECD Eq. 2 — Facteur d'émission baseline par unité d'énergie INPUT (Case 2: EPC).
    
    EF_b,input = Σ_k Σ_i,j [P_b,i,j × (EF_CO2_i × fNRB_i + EF_nonCO2_i) × NCV_i]
                 ÷ Σ_k Σ_i,j [P_b,i,j × NCV_i]
    
    Résultat: tCO2e / TJ d'énergie en entrée
    """
    numerator = 0.0
    denominator = 0.0
    
    for fuel in baseline_fuels:
        P = fuel['P_b_kg_per_HH_day'] / 1000.0
        NCV = fuel['NCV_TJ_per_ton']
        EF_CO2 = fuel['EF_CO2_tCO2_per_TJ']
        EF_nonCO2 = fuel['EF_nonCO2_tCO2e_per_TJ']
        fNRB = fuel.get('fNRB', 0.0)
        
        numerator += P * (EF_CO2 * fNRB + EF_nonCO2) * NCV
        denominator += P * NCV
    
    return numerator / denominator


def calculate_EG_p_useful_electric_mecd(
    EG_p_d_y_MWh: float,  # MWh mesurés/appareil/an
    eta_p: float,           # efficacité projet
) -> float:
    """
    MECD Eq. 6 — Énergie utile projet (appareil électrique, Case 1).
    EG_p,useful,y = Σ_d [EG_p,d,y × 0.0036 × η_p,d,y]
    0.0036 = facteur de conversion MWh → TJ
    """
    return EG_p_d_y_MWh * 0.0036 * eta_p


def calculate_EG_p_useful_fuel_mecd(
    P_p_d_y_kg: float,   # fuel mesuré kg/appareil/an
    NCV_p: float,         # TJ/tonne
    eta_p: float,
) -> float:
    """
    MECD Eq. 7 — Énergie utile projet (appareil combustible, Case 1).
    EG_p,useful,y = Σ_d [P_p,d,y × NCV_p,i × η_p,d,y]
    """
    P_tonnes = P_p_d_y_kg / 1000.0
    return P_tonnes * NCV_p * eta_p


def calculate_BE_mecd_case1(
    EG_p_useful_y_TJ: float,  # TJ d'énergie utile projet (Eq. 6 ou 7)
    EF_b_useful: float,        # tCO2e/TJ utile (Eq. 1)
    num_devices: int,
    U_p_y: float,
) -> float:
    """
    MECD Eq. 3 — Émissions baseline (Case 1).
    BE_y = EG_p,useful,y × EF_b,useful
    
    Où EG_p,useful,y est déjà la SOMME sur tous les appareils actifs.
    L'architecture : BE est indexée sur l'énergie utile LIVRÉE par le projet.
    """
    # EG_p_useful_y est par appareil, multiplié par les appareils actifs et usage
    return EG_p_useful_y_TJ * num_devices * U_p_y * EF_b_useful


def calculate_BE_mecd_case2(
    EG_p_d_y_MWh: float,   # élec mesurée/appareil/an
    SC_b: float,             # TJ/test/personne (baseline, CCT)
    SC_p: float,             # TJ/test/personne (projet, CCT)
    EF_b_input: float,       # tCO2e/TJ input (Eq. 2)
    num_devices: int,
    U_p_y: float,
) -> float:
    """
    MECD Eq. 4 — Émissions baseline (Case 2: EPC).
    BE_y = Σ_d [EG_p,d,y × (SC_b/SC_p) × 0.0036 × EF_b,input]
    """
    return EG_p_d_y_MWh * (SC_b / SC_p) * 0.0036 * EF_b_input * num_devices * U_p_y


def calculate_PE_electric_mecd(
    EG_p_d_y_MWh: float,   # élec mesurée/appareil/an
    EF_el: float,            # tCO2e/MWh (CDM TOOL05)
    TDL: float,              # fraction pertes T&D
    num_devices: int,
    U_p_y: float,
) -> float:
    """
    MECD Eq. 8 — Émissions projet (appareil électrique).
    PE_y = Σ_d [EG_p,d,y × EF_el,y × (1 + TDL_j,y)]
    
    CRITIQUE: (1 + TDL) — les pertes AUGMENTENT les émissions côté production.
    """
    return EG_p_d_y_MWh * EF_el * (1.0 + TDL) * num_devices * U_p_y


def calculate_PE_fossil_fuel_mecd(
    P_p_d_y_kg: float,    # fuel mesuré/appareil/an
    NCV_p: float,          # TJ/tonne
    EF_p: float,           # tCO2e/TJ
    num_devices: int,
    U_p_y: float,
) -> float:
    """
    MECD Eq. 9 — Émissions projet (combustible fossile: LPG).
    PE_y = Σ_d [P_p,d,y × NCV_p,i × EF_p,i]
    """
    P_tonnes = P_p_d_y_kg / 1000.0
    return P_tonnes * NCV_p * EF_p * num_devices * U_p_y


def calculate_ER_mecd(
    BE_y: float,
    PE_y: float,
    LE_y: float,   # leakage calculé per TPDDTEC v4.0 §3.11 (Option 1: × 0.95)
) -> float:
    """
    MECD Eq. 10 — Réductions d'émissions.
    ER_y = BE_y − PE_y − LE_y
    
    Note: Pour leakage Option 1 TPDDTEC: LE_y = (BE_y - PE_y) × 0.05
    donc ER_y = (BE_y - PE_y) × 0.95
    """
    return BE_y - PE_y - LE_y
```

---

## PARTIE 5 — MOTEUR DE SIMULATION ANNUEL (er_simulator.py)

### 5.1 — Classe principale

```python
class ERSimulator:
    """
    Calcule les réductions d'émissions année par année pour une méthodologie donnée.
    Remplace et corrige l'implémentation existante.
    NE PAS renommer cette classe — garder le nom existant.
    """
    
    def simulate(
        self,
        methodology: str,      # 'TPDDTEC', 'VM0050', 'MECD'
        method: str,           # Pour TPDDTEC: 'method_1'/'method_2'/'method_3'
        mecd_case: str,        # Pour MECD: 'case_1'/'case_2'
        params: dict,          # Tous les paramètres utilisateur
        crediting_period_years: int,
        start_year: int = 2024,
    ) -> dict:
        """
        Retourne:
        {
          'annual_ER': {year: tCO2e},
          'cumulative_ER': float,
          'avg_annual_ER': float,
          'scale_classification': str,   # TPDDTEC seulement
          'warnings': list[str],
          'vintage_ER': {year: tCO2e},  # identique à annual_ER
        }
        """
        results = {}
        warnings = []
        
        for i in range(crediting_period_years):
            year = start_year + i
            
            # 1. Calculer appareils actifs (technology-days ou N_j_k_y)
            active_devices = self._active_devices(params, i + 1)
            U_p_y = self._usage_rate(params, i + 1)
            
            # 2. Appeler la bonne fonction de calcul
            if methodology == 'TPDDTEC':
                N_b_p_y = active_devices * 365
                er = self._calc_tpddtec(method, N_b_p_y, U_p_y, params, i + 1)
            elif methodology == 'VM0050':
                er = self._calc_vm0050(active_devices, U_p_y, params)
            elif methodology == 'MECD':
                er = self._calc_mecd(mecd_case, active_devices, U_p_y, params)
            
            results[year] = max(0.0, er)  # les ER ne peuvent pas être négatives
        
        cumulative = sum(results.values())
        avg = cumulative / crediting_period_years
        
        return {
            'annual_ER': results,
            'cumulative_ER': cumulative,
            'avg_annual_ER': avg,
            'warnings': warnings,
            'vintage_ER': results.copy(),
        }
    
    def _active_devices(self, params: dict, year_num: int) -> int:
        """Nombre d'appareils actifs non périmés en année year_num."""
        total = 0
        lifetime = params.get('tech_lifetime_years', 10)
        for deploy_year_num, qty in params.get('deployment_schedule', {1: params.get('num_devices', 0)}).items():
            age = year_num - deploy_year_num
            if 0 <= age < lifetime:
                total += qty
        return total
    
    def _usage_rate(self, params: dict, year_num: int) -> float:
        """U_p_y avec décroissance et plancher."""
        u0 = params.get('usage_rate_year1', 0.90)
        decay = params.get('usage_rate_decay_per_year', 0.03)
        floor = params.get('usage_rate_floor', 0.50)
        return max(u0 - (year_num - 1) * decay, floor)
```

---

## PARTIE 6 — VALIDATIONS CRITIQUES (methodology_rules.py)

```python
def validate_inputs(methodology: str, params: dict) -> list:
    """
    Retourne une liste d'erreurs bloquantes et warnings à afficher à l'utilisateur.
    À appeler AVANT tout calcul.
    """
    errors = []
    warnings = []
    
    # --- COMMUN ---
    if params.get('tech_lifetime_years', 0) <= 0:
        errors.append("La durée de vie technique doit être positive.")
    
    if params.get('usage_rate_year1', 0) > 1.0:
        errors.append("Le taux d'utilisation ne peut pas dépasser 1.0 (100%).")
    
    # --- TPDDTEC ---
    if methodology == 'TPDDTEC':
        method = params.get('calculation_method', '')
        
        if method == 'method_2':
            if params.get('baseline_fuel') != 'wood':
                errors.append("Method 2 est réservée au bois uniquement (pas charbon, LPG, etc.).")
            scale = params.get('project_scale', '')
            if scale == 'large':
                errors.append("Method 2 n'est pas applicable aux projets large scale.")
        
        if method == 'method_3':
            if params.get('project_fuel') in ('lpg', 'kerosene', 'coal') :
                warnings.append("Projet fossile détecté (Method 3): seul le crédit efficacité "
                                "est éligible — EF_p = EF_b dans les calculs.")
        
        # Validation fNRB requis si baseline biomasse
        if params.get('baseline_fuel') in ('wood', 'charcoal'):
            if params.get('fNRB') is None:
                errors.append("fNRB requis pour baseline biomasse/charbon.")
        
        # Plafond P_b
        Pb = params.get('Pb_t_per_person_year', 0)
        if Pb > 0.95:
            errors.append(f"P_b ({Pb} t/pers/an) dépasse le plafond absolu de 0.95 t/pers/an.")
        elif Pb > 0.75:
            warnings.append("P_b > 0.75 t/pers/an: justification par étude tierce requise (ICS 18).")
        
        # EF charbon : cohérence
        if 'charcoal' in (params.get('baseline_fuel',''), params.get('project_fuel','')):
            warnings.append("Charbon de bois détecté: vérifier que l'EF choisi (combustion seule: "
                           "112 tCO2/TJ, ou avec production: 165.22 tCO2/TJ) est cohérent. "
                           "Le plafond absolu est 197.15 tCO2/TJ.")
    
    # --- VM0050 ---
    if methodology == 'VM0050':
        if params.get('project_uses_LPG'):
            end_date = params.get('LPG_monitoring_end_date')
            if end_date and end_date.year > 2045:
                errors.append("VM0050 §4: crédits LPG impossibles pour périodes "
                             "se terminant après le 31/12/2045.")
            warnings.append("LPG: CDM TOOL15 requis pour leakage amont combustible fossile.")
        
        if params.get('fNRB_source') == 'TOOL30_Tier3':
            warnings.append("fNRB TOOL30 Tier 3: réduction d'incertitude de 26% appliquée "
                           "automatiquement (VM0050 fn.22).")
        
        if params.get('project_device') in ('electric', 'induction', 'hot_plate'):
            TDL = params.get('TDL', 0)
            if TDL < 0 or TDL > 0.5:
                errors.append(f"TDL ({TDL}) hors plage valide [0, 0.5].")
    
    # --- MECD ---
    if methodology == 'MECD':
        if params.get('project_uses_LPG') or params.get('project_fuel') in ('kerosene',):
            warnings.append("Projet fossile MECD: seul le crédit efficacité est éligible.")
        
        if params.get('fuel_switch_only', False):
            errors.append("MECD: le fuel switch seul n'est pas éligible. "
                         "Un changement de technologie est obligatoire.")
        
        baseline_shares = [f.get('share_pct', 0) for f in params.get('baseline_fuels', [])]
        if abs(sum(baseline_shares) - 100) > 0.01:
            errors.append(f"Les parts du panier baseline doivent sommer à 100% "
                         f"(actuel: {sum(baseline_shares):.1f}%).")
        
        fNRB_mode = params.get('fNRB_update_mode', '')
        if fNRB_mode not in ('ex_ante_fixed', 'biennial'):
            errors.append("fNRB_update_mode doit être 'ex_ante_fixed' ou 'biennial'.")
    
    return {'errors': errors, 'warnings': warnings}
```

---

## PARTIE 7 — INTERFACE UTILISATEUR (Streamlit — ne pas toucher la structure existante)

Dans les composants Streamlit existants, remplace uniquement les sections de formulaire correspondant à chaque méthodologie pour afficher les bons champs avec les bonnes valeurs par défaut :

### Flux de saisie Gold Standard / TPDDTEC :
1. Standard = Gold Standard → Type de projet ?
2. Si biomasse/solaire/rétention → TPDDTEC
   - Combustible baseline → choix parmi: bois, charbon, fossile (LPG/kérosène/charbon)
   - Combustible projet → idem
   - → Méthode auto-sélectionnée (1, 2 ou 3)
3. Afficher les champs selon la méthode :
   - Method 1 : SFS_p_b_y (kg/tech/day), fNRB, EF, NCV, usage
   - Method 2 : SFC_p_y seulement (SFC_b calculé auto), fNRB
   - Method 3 : SE_b_CO2, SE_b_nonCO2, SE_p_CO2, SE_p_nonCO2, fNRB_b
4. Valeurs par défaut pré-remplies depuis `TPDDTEC_DEFAULTS`
5. Warning affiché si charbon → demander si EF inclut production

### Flux de saisie Verra / VM0050 :
1. Standard = Verra → VM0050 directement
2. Type d'appareil projet : biomasse / fossile (LPG) / électrique / bioéthanol
3. Champs selon type:
   - Biomasse: BC_b, BC_p, NCV, EF, fNRB (source à spécifier)
   - Électrique: EC_p_MWh, EF_el, TDL (1+TDL dans calcul)
   - LPG: + date fin monitoring (validation ≤ 2045), + TOOL15
4. Stove stacking cross-check : demander eta_new et eta_old

### Flux de saisie Gold Standard / MECD :
1. Standard = Gold Standard → appareils mesurés en continu → MECD
2. Type d'appareil : induction, EPC, LPG metré, biogas, bioéthanol
3. Case auto-détecté (1 si non-EPC, 2 si EPC)
4. Panier baseline : interface pour saisir N combustibles avec shares
5. Validation sum(shares) = 100%
6. Case 1 : saisir EG_p,d,y (MWh), eta_p, EF_el, TDL
7. Case 2 (EPC) : saisir SC_b, SC_p via CCT

---

## PARTIE 8 — TESTS À RÉALISER APRÈS MODIFICATION

Ajoute des tests unitaires dans `tests/test_er_simulator.py` (garder le fichier existant, ajouter à la fin) :

```python
# Test TPDDTEC Method 1 — exemple numérique de validation
def test_tpddtec_method1_basic():
    # 1000 appareils × 365 jours = 365 000 tech-days
    # SFS = 1 kg/tech/day = 0.001 tonnes/tech/day
    # NCV_wood = 0.0156 TJ/tonne
    # fNRB = 0.80, EF_CO2 = 112, EF_nonCO2 = 9.46
    # U_p_y = 0.90
    # Gross ER = 365000 × 0.90 × 0.001 × 0.0156 × (0.80×112 + 9.46)
    #          = 328500 × 0.001 × 0.0156 × (89.6 + 9.46)
    #          = 328.5 × 0.0156 × 99.06
    #          = 328.5 × 1.5453...
    #          ≈ 507.6 tCO2e
    # Net ER (option 1, ×0.95) ≈ 482.2 tCO2e
    result = calculate_ER_tpddtec_method1(
        N_b_p_y=365000, U_p_y=0.90, SFS_p_b_y=1.0,
        NCV_b=0.0156, fNRB=0.80, EF_b_CO2=112.0, EF_b_nonCO2=9.46,
        leakage_option=1
    )
    assert abs(result - 482.2) < 5.0  # tolérance 5 tCO2e

# Test VM0050 TDL — vérifier que (1+TDL) est bien appliqué
def test_vm0050_pe_electric_TDL_positive():
    pe_with_TDL = calculate_PE_electric_vm0050(
        EC_p_MWh=100, N_j_k_y=1, n_j_k_y=1.0,
        EF_el=0.5, TDL=0.10
    )
    pe_without_TDL = 100 * 1 * 1.0 * 0.5  # = 50
    assert pe_with_TDL > pe_without_TDL  # TDL augmente les émissions
    assert abs(pe_with_TDL - 55.0) < 0.01  # 50 × 1.10 = 55

# Test VM0050 Eq.11 — LERB soustrait
def test_vm0050_net_ER_LERB_subtracted():
    er = calculate_net_ER_vm0050(BE_y=1000, PE_y=400, LERB_y=50)
    assert er == (1000 - 400) * 0.95 - 50  # = 570 - 50 = 520

# Test MECD EF_b_useful — panier 100% bois
def test_mecd_EF_b_useful_wood_only():
    fuels = [{
        'fuel': 'wood', 'share_pct': 100,
        'P_b_kg_per_HH_day': 3.0,
        'NCV_TJ_per_ton': 0.0156,
        'EF_CO2_tCO2_per_TJ': 112.0,
        'EF_nonCO2_tCO2e_per_TJ': 9.46,
        'fNRB': 0.80,
        'eta_baseline_device': 0.12
    }]
    ef = calculate_EF_b_useful_mecd(fuels)
    # EF_b_useful = (EF_CO2×fNRB + EF_nonCO2) / eta = (112×0.8 + 9.46) / 0.12
    #             = (89.6 + 9.46) / 0.12 = 99.06 / 0.12 = 825.5 tCO2e/TJ utile
    assert abs(ef - 825.5) < 1.0

# Test MECD PE électrique — (1+TDL) correct
def test_mecd_pe_electric_TDL():
    pe = calculate_PE_electric_mecd(
        EG_p_d_y_MWh=500, EF_el=0.4, TDL=0.05,
        num_devices=10, U_p_y=0.85
    )
    expected = 500 * 0.4 * 1.05 * 10 * 0.85
    assert abs(pe - expected) < 0.01
```

---

## RÉSUMÉ DES CORRECTIONS PRIORITAIRES

1. **TPDDTEC** : Supprimer Methods 4-8. Implémenter Method 1/2/3 uniquement. Unité = technology-days (N × 365). Method 2 = bois uniquement + micro/small. Method 3 fossil = EF_p := EF_b.

2. **VM0050** : Corriger TDL de `(1-TDL)` à `(1+TDL)`. Corriger signe LERB : `-LERB` pas `+LERB`. Ajouter stove stacking cross-check. Ajouter fNRB discount 26% si TOOL30. Ajouter validation LPG sunset 2045.

3. **MECD** : Refaire entièrement l'architecture baseline : `EF_b,useful` → `BE_y = EG_p,useful × EF_b,useful`. Corriger TDL de `(1-TDL)` à `(1+TDL)`. Case 1 = efficacité déterminable (ALL sauf EPC). Case 2 = EPC uniquement.

4. **COMMUN** : fNRB dans Method 3 PE = fNRB_BASELINE, pas zéro. Charbon = EF direct (165.22 inclut déjà production), pas CF séparé.
