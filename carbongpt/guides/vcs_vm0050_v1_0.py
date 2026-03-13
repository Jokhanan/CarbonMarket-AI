"""
vcs_vm0050_v1_0.py — Verra VCS VM0050 v1.0 writing guide.

Coverage: Energy Efficiency and Fuel-Switch Measures in Thermal Applications of
Non-Renewable Biomass (Cookstoves and Thermal Energy Applications) — VCS VM0050
Version 1.0, published 9 October 2024.

This guide provides section-by-section writing instructions for Project Description (PD),
Monitoring Report (MR), and Validation/Verification (ValVer) documents.

Key references embedded throughout:
  Equations 1–11 (§8.1–§8.4)
  Parameter tables §9.1 (ex-ante) and §9.2 (monitored)
  Applicability conditions §4
  Additionality §5
  Monitoring plan §6
  IPCC 2006 Guidelines for default values
  CDM tools: TOOL05, TOOL07, TOOL16, TOOL30, TOOL33 v3, TOOL36
"""

GUIDE_ID = "Verra_VCS_VM0050_v1_0"

SUBSECTIONS: dict[str, dict] = {

    # ============================================================
    # SECTION 1 — PROJECT DETAILS
    # ============================================================
    "1.1": {
        "title": "Summary Description of the Project",
        "parent_section": "Project Details",
        "must_include": [
            "name and brief description of the project technology (e.g., improved cookstove model)",
            "fuels displaced (baseline) and fuels used (project), with wood/charcoal breakdown",
            "geographic location of the project (country, region, rural/urban context)",
            "explanation of how the project reduces GHG emissions (thermal efficiency improvement, fuel switch, or combination)",
            "brief description of the baseline scenario (e.g., continued use of three-stone fires)",
            "estimated annual average emission reductions (tCO2e/yr) and total over the crediting period",
            "statement that the project applies VM0050 v1.0 under the VCS Program",
        ],
        "examples": [
            (
                "The project distributes 80,000 improved cookstoves across rural Ethiopia, displacing "
                "non-renewable firewood burned in three-stone fires. The project devices achieve a thermal "
                "efficiency of 37% (WBT-certified), compared to 15% for the baseline device. "
                "The project applies VM0050 v1.0 under the Verra VCS Program and is expected to generate "
                "approximately 55,000 tCO2e per year over a 10-year crediting period."
            ),
        ],
        "failure_modes": [
            "summary exceeds one page without clear structure",
            "no explanation of the GHG reduction mechanism (efficiency gain, fuel switch, or leakage discount)",
            "annual and total ER estimate not provided",
            "baseline scenario not described",
            "VM0050 not identified as the applicable methodology",
        ],
        "content_format": "prose",
        "format_instructions": (
            "Write a concise summary (one page maximum). State the project technology, baseline fuel and device, "
            "project fuel and device, host country, GHG reduction mechanism, fNRB source, and estimated ERs. "
            "Always note that VM0050 v1.0 is the applicable VCS methodology."
        ),
    },

    "1.3": {
        "title": "Sectoral Scope and Project Type",
        "parent_section": "Project Details",
        "must_include": [
            "Sectoral Scope: 3 — Energy demand",
            "Project type: Energy efficiency and/or fuel switch in cookstoves or thermal applications",
            "confirmation that the project involves non-renewable biomass displacement",
        ],
        "examples": [
            "Sectoral Scope: 3 (Energy demand). Project type: Improved cookstoves — energy efficiency and non-renewable biomass fuel switch.",
        ],
        "failure_modes": [
            "wrong sectoral scope number cited",
            "project type does not reflect cookstove or thermal energy application",
        ],
        "content_format": "prose",
        "format_instructions": "State sectoral scope 3 and describe the project type in one paragraph.",
    },

    "1.4": {
        "title": "Project Crediting Period",
        "parent_section": "Project Details",
        "must_include": [
            "crediting period start and end dates",
            "crediting period length: 10 years (renewable once for 10 years, or 20-year fixed)",
            "note for LPG project devices: credits cannot be issued for periods after 31 December 2045 (VM0050 §4 cond. 11c)",
        ],
        "examples": [
            "Crediting period: 1 January 2025 to 31 December 2034 (10 years, renewable). "
            "The project does not use LPG as a project fuel, so the 2045 sunset clause is not applicable.",
        ],
        "failure_modes": [
            "crediting period exceeds 10 years for renewable crediting",
            "LPG sunset clause not mentioned for LPG project devices",
        ],
        "content_format": "prose",
        "format_instructions": "State the crediting period start and end dates and confirm whether the 2045 LPG sunset clause applies.",
    },

    # ============================================================
    # SECTION 2 — APPLICABILITY CONDITIONS
    # ============================================================
    "2.0": {
        "title": "Applicability Conditions (VM0050 §4)",
        "parent_section": "Applicability",
        "must_include": [
            "Condition 1: Project displaces non-renewable biomass fuels in thermal applications",
            "Condition 2: Baseline devices are not commercially viable without project support",
            "Condition 4: Project devices are operated in non-OECD countries or regions with per-capita income below World Bank upper-middle-income threshold",
            "Condition 5: Project is not implemented solely by a government decree or regulatory mandate",
            "Condition 6: Baseline devices confirmed as appropriate technology for the region at project start date",
            "Condition 7 (grouped projects): eligibility criteria for new instances defined and applied consistently",
            "Condition 8: Biomass EE or fuel-switch devices — initial thermal efficiency >= 25% (WBT or equivalent CCT)",
            "Condition 9 (LPG/bioethanol devices): initial thermal efficiency >= 30%",
            "Condition 10a (hot plates/electric hobs): initial thermal efficiency >= 40%",
            "Condition 10b (induction/other electric): initial thermal efficiency >= 70%",
            "Condition 11 (LPG): LPG sourced domestically, not used in OECD country, and credits not for periods after 31 Dec 2045",
            "confirmation that no applicability conditions are violated",
        ],
        "examples": [
            (
                "Condition 8 — Thermal Efficiency: The project stove model achieves an initial WBT thermal efficiency "
                "of 37%, which exceeds the VM0050 minimum threshold of 25% for biomass fuel-switch and "
                "energy-efficiency devices."
            ),
            (
                "Condition 10b — Electric (induction): The induction stove achieves an initial thermal efficiency of "
                "75%, exceeding the VM0050 minimum of 70% for induction devices."
            ),
        ],
        "failure_modes": [
            "efficiency threshold not compared to the correct VM0050 condition (conditions 8/9/10a/10b)",
            "LPG sunset clause (condition 11c) not addressed for LPG project devices",
            "grouped project eligibility criteria not defined when the project is structured as a group",
            "condition 6 baseline device appropriateness not confirmed for the project region",
        ],
        "content_format": "prose",
        "format_instructions": (
            "Address each applicability condition in sequence. Confirm compliance or explain why the condition is "
            "not triggered. For efficiency thresholds, cite the WBT test report or manufacturer certification. "
            "For LPG devices, confirm the 2045 sunset date and domestic sourcing."
        ),
    },

    # ============================================================
    # SECTION 3 — PROJECT BOUNDARY
    # ============================================================
    "3.0": {
        "title": "Project Boundary and GHG Sources",
        "parent_section": "Project Boundary",
        "must_include": [
            "geographic boundary of the project (country/region; GPS coordinates or map for grouped project instances)",
            "GHG included — Baseline: CO2 and non-CO2 (CH4, N2O) from combustion of non-renewable biomass",
            "GHG included — Project: CO2 and non-CO2 from combustion of project fuel; CO2 from grid electricity (if applicable)",
            "GHG excluded and justification (e.g., project device manufacturing, transport emissions excluded as conservative)",
            "leakage sources: non-renewable biomass displaced but re-used elsewhere, fossil fuel leakage",
            "table or list format for sources/sinks/reservoirs (SSR), inclusion/exclusion, and justification",
        ],
        "examples": [
            (
                "Baseline GHG sources: CO2 and non-CO2 emissions from combustion of non-renewable biomass in "
                "traditional three-stone fires. EFb,i,CO2 = 112 tCO2/TJ (IPCC 2006), "
                "EFb,i,nonCO2 = 9.46 tCO2e/TJ (AR5 GWP). fNRB = 0.72 (UNFCCC national default, Kenya 2022). "
                "Project GHG sources: CO2 and non-CO2 from residual biomass combustion in project stove. "
                "Leakage: non-renewable biomass re-used elsewhere, addressed by 0.95 retention factor per §8.3."
            ),
        ],
        "failure_modes": [
            "fNRB value not cited in project boundary section",
            "non-CO2 sources (CH4, N2O) omitted from boundary",
            "leakage boundary not described separately from project boundary",
            "for electric projects, electricity grid emission factor omitted from project GHG sources",
        ],
        "content_format": "table",
        "format_instructions": (
            "Present a table with columns: Source/Sink/Reservoir, GHG, Included/Excluded, Justification. "
            "Then write a brief narrative confirming the geographic boundary, citing GPS coordinates or a map "
            "for grouped project instances."
        ),
        "template_scaffold": (
            "| Source/Sink | GHG | Included/Excluded | Justification |\n"
            "| --- | --- | --- | --- |\n"
            "| Baseline — non-renewable biomass combustion | CO2 | Included | Primary emission source |\n"
            "| Baseline — non-renewable biomass combustion | CH4, N2O | Included | Material non-CO2 GHGs per IPCC |\n"
            "| Project — biomass or project fuel combustion | CO2 | Included | Accounts for partial substitution |\n"
            "| Project — biomass or project fuel combustion | CH4, N2O | Included | Material non-CO2 GHGs |\n"
            "| Project — electricity (electric devices only) | CO2 | Included | Grid emissions via CDM TOOL07 |\n"
            "| Device manufacturing / transport | CO2 | Excluded | Conservative — increases ER |\n"
            "| Leakage — non-renewable biomass re-use | CO2 | Included | Addressed by 0.95 retention factor |"
        ),
    },

    # ============================================================
    # SECTION 4 — BASELINE SCENARIO
    # ============================================================
    "4.0": {
        "title": "Baseline Scenario",
        "parent_section": "Baseline",
        "must_include": [
            "identification and description of the baseline scenario (most plausible practice prior to project)",
            "confirmation that baseline devices meet VM0050 condition 6 (appropriate technology for the region)",
            "description of baseline fuel(s): primary fuel type, source (renewable vs non-renewable)",
            "fNRB value and source (UNFCCC national default / CDM TOOL30 × 0.74 / CDM TOOL33 v3)",
            "baseline fuel consumption determination: Option 1 (KPT, 90/10 CI) or Option 2 (IPCC default — 0.5 t/capita/yr firewood or 0.13 t/capita/yr charcoal)",
            "baseline device thermal efficiency (ηold,avg): default 15% for three-stone fire, or WBT result",
            "statement that baseline scenario is not a result of regulatory mandate",
        ],
        "examples": [
            (
                "The baseline scenario is the continued use of traditional three-stone fires burning non-renewable "
                "firewood. This is the most plausible practice in the absence of the project: no regulatory mandate "
                "requires displacement, and improved cookstoves are not commercially available without project support. "
                "\n\nfNRB = 0.72 — sourced from UNFCCC national default values for Kenya (published 2022, draft status; "
                "will be updated upon finalisation). Baseline fuel consumption: VM0050 §8.1.1 Option 2 default "
                "of 0.5 t/capita/yr air-dried firewood, scaled by household size of 5.2 persons. "
                "Baseline device efficiency: ηold,avg = 15% (VM0050 §9.1 default for three-stone fire)."
            ),
        ],
        "failure_modes": [
            "baseline fuel consumption method (Option 1 or 2) not explicitly stated",
            "fNRB source not identified — cannot be 'assumed' without citing the appropriate CDM tool or UNFCCC table",
            "if TOOL30 used for fNRB, 26% uncertainty discount not applied (fNRB must be × 0.74)",
            "ηold,avg not cited or confused with project device efficiency",
            "baseline scenario not confirmed as the most plausible pre-project practice",
        ],
        "content_format": "prose",
        "format_instructions": (
            "Describe the baseline scenario in a structured narrative. Clearly state: the baseline device and fuel, "
            "the fNRB value and source (with 0.74 discount if from TOOL30), the fuel consumption approach (Option 1/2) "
            "with supporting data or default values, and the baseline device efficiency."
        ),
    },

    # ============================================================
    # SECTION 5 — ADDITIONALITY
    # ============================================================
    "5.0": {
        "title": "Additionality",
        "parent_section": "Additionality",
        "must_include": [
            "tool applied: CDM TOOL36 (Procedure to demonstrate additionality of small-scale project activities) or VCS additionality tool",
            "regulatory surplus: confirmation that project activity is not required by law or regulatory mandate",
            "investment analysis or barrier analysis showing that the project would not occur without carbon finance",
            "common practice analysis: demonstration that the project technology is not widespread in the region",
            "statement about the additionality of the baseline scenario",
        ],
        "examples": [
            (
                "Additionality is demonstrated using CDM TOOL36. "
                "\nRegulatory surplus: No applicable law or regulation mandates the distribution of improved cookstoves "
                "in the project region. "
                "\nBarrier analysis: The project faces a financial barrier (improved stoves cost 3× the traditional "
                "three-stone fire, which requires no capital outlay) and a social barrier (households lack awareness "
                "of improved stove benefits). "
                "\nCommon practice: An analysis of the project region confirms that improved cookstoves account for "
                "less than 5% of cooking devices in use, confirming that the technology is not yet common practice."
            ),
        ],
        "failure_modes": [
            "additionality tool not cited",
            "project type is a government scheme with mandatory participation — additionality questionable",
            "common practice analysis uses national data instead of project region data",
            "barrier analysis does not specifically address the project stove technology",
        ],
        "content_format": "prose",
        "format_instructions": (
            "Structure the additionality section with the following sub-headings: "
            "(1) Regulatory Surplus; (2) Investment or Barrier Analysis; (3) Common Practice Analysis. "
            "Reference the CDM tool or VCS procedure used in the header. Conclude with a clear additionality statement."
        ),
    },

    # ============================================================
    # SECTION 6 — QUANTIFICATION OF EMISSION REDUCTIONS
    # ============================================================
    "6.1": {
        "title": "Baseline Emissions — Biomass Fuel (Equations 1–5)",
        "parent_section": "Quantification",
        "must_include": [
            "Eq. 1: BEy = sum over i of [ ECi,y × Nj,k,y × nj,k,y × (EFb,i,CO2 × fNRB,y + EFb,i,nonCO2) ]",
            "definition of ECi,y: annual energy consumption of baseline device type i per device (TJ/device/year)",
            "ECi,y derived from BCex-ante,b,i × NCVb,i (fuel mass × net calorific value), or from Eq. 3–5 for efficiency back-calculation or electric pressure cooker",
            "Eq. 2 (if using fuel consumption data): ECi,y = BCb,i,y × NCVb,i",
            "Eq. 3 (if project device efficiency used): ECi,y = (ηnew,avg,y / ηold,avg) × ECp,j,k,y",
            "Eq. 5 (electric pressure cooker only): ECi,y = (SCb,i / SCp,j) × ECp,j,k,y",
            "values for fNRB,y, EFb,i,CO2, EFb,i,nonCO2, NCVb,i with sources",
            "calculation of BEy for each monitoring period / ex-ante year",
        ],
        "examples": [
            (
                "Baseline Emissions — Eq. 1:\n"
                "BEy = ECi,y × Nj,k,y × nj,k,y × (EFb,i,CO2 × fNRB,y + EFb,i,nonCO2)\n\n"
                "Parameters (firewood baseline):\n"
                "  BCex-ante,b,i = 0.5 t/capita/yr × 5.2 persons/HH = 2.6 t/HH/yr (Option 2 default)\n"
                "  ECi,y = 2.6 × 0.0156 TJ/t = 0.04056 TJ/device/yr (Eq. 2)\n"
                "  Nj,k,y = 80,000 devices commissioned\n"
                "  nj,k,y = 0.85 (annual survey, lower bound of 90% CI)\n"
                "  EFb,i,CO2 = 112.0 tCO2/TJ (IPCC 2006, wood)\n"
                "  EFb,i,nonCO2 = 9.46 tCO2e/TJ (AR5 GWP, wood)\n"
                "  fNRB,y = 0.72 (UNFCCC national default, Kenya 2022)\n\n"
                "BEy = 0.04056 × 80,000 × 0.85 × (112.0 × 0.72 + 9.46)\n"
                "     = 3,248 × (80.64 + 9.46)\n"
                "     = 3,248 × 90.10 = 292,645 tCO2e/yr"
            ),
        ],
        "failure_modes": [
            "fNRB applied to fossil fuel baseline emissions (only applies to biomass)",
            "ECi,y not defined or unit incorrect (must be TJ/device/year for Eq. 1)",
            "Eq. 3 used without stating ηold,avg source (must cite §9.1 default or WBT result)",
            "Eq. 5 used without Controlled Cooking Test (CCT) evidence for SCb,i and SCp,j",
            "Nj,k,y and nj,k,y not distinguished (Nj,k,y = devices commissioned; nj,k,y = proportion in use)",
        ],
        "content_format": "calculation",
        "format_instructions": (
            "Present each equation number, followed by the variable definitions with units and sources, "
            "then the numerical calculation. Show intermediate steps. "
            "Clearly state which equation route was used (Eq. 2, 3, or 5) for ECi,y determination. "
            "Tabulate BEy for each year of the monitoring period or crediting period."
        ),
    },

    "6.2": {
        "title": "Baseline Emissions — Fossil Fuel (Equation 6)",
        "parent_section": "Quantification",
        "must_include": [
            "Eq. 6: BEy = sum over i of [ ECi,y,fossil × Nj,k,y × nj,k,y × EFp,j,CO2 + EFp,j,nonCO2 ]",
            "note that fNRB is NOT applied to fossil fuel baseline emissions",
            "ECi,y,fossil determination using same methods (fuel mass × NCV or efficiency back-calculation)",
            "emission factors for fossil fuel type (e.g., LPG: EF_CO2 = 63.1 tCO2/TJ; natural gas: 56.1 tCO2/TJ — IPCC 2006 defaults)",
        ],
        "examples": [
            "For LPG baseline: ECi,y = BCb,LPG × NCV_LPG; BEy = ECi,y × Nj × nj × (EF_CO2,LPG + EF_nonCO2,LPG). Note: fNRB is NOT used for fossil fuel emission calculation (Eq. 6).",
        ],
        "failure_modes": [
            "fNRB incorrectly applied to fossil fuel baseline emissions",
            "fossil fuel NCV or EF sourced from unofficial or un-cited reference",
        ],
        "content_format": "calculation",
        "format_instructions": (
            "Present Eq. 6 clearly, with explicit statement that fNRB does not appear in this equation. "
            "Define all variables with units and data sources."
        ),
    },

    "6.3": {
        "title": "Project Emissions — Biomass Fuel (Equation 7)",
        "parent_section": "Quantification",
        "must_include": [
            "Eq. 7: PEy = sum over j,k of [ BCp,j,k,y × NCVp,j × Nj,k,y × nj,k,y × (EFp,j,CO2 × fNRB,y + EFp,j,nonCO2) ]",
            "BCp,j,k,y: measured from KPT survey (90/10 confidence/precision) or direct fuel measurement",
            "fNRB,y applied to project biomass fuel combustion emissions (same value as baseline unless updated)",
            "NCVp,j, EFp,j,CO2, EFp,j,nonCO2 for project fuel type with sources",
        ],
        "examples": [
            (
                "Project Emissions — Eq. 7 (residual firewood in improved stove):\n"
                "BCp,j,k,y = 0.62 t/device/yr (KPT survey, 90% CI lower bound)\n"
                "NCVp,j = 0.0156 TJ/t (IPCC 2006 default, wood)\n"
                "EFp,j,CO2 = 112.0 tCO2/TJ; EFp,j,nonCO2 = 9.46 tCO2e/TJ (AR5 GWP)\n"
                "fNRB,y = 0.72\n"
                "PEy = 0.62 × 0.0156 × 80,000 × 0.85 × (112 × 0.72 + 9.46) = 53,120 tCO2e/yr"
            ),
        ],
        "failure_modes": [
            "fNRB not applied to project biomass emissions (Eq. 7 requires fNRB on project CO2 component)",
            "BCp,j,k,y not measured by KPT or not meeting 90/10 confidence/precision requirement",
            "project fuel NCV sourced from baseline fuel table — must be specific to project fuel type",
        ],
        "content_format": "calculation",
        "format_instructions": (
            "Present Eq. 7 with all variable definitions, units, and sources. Show the numerical calculation. "
            "Note the KPT survey methodology used for BCp,j,k,y and confirm 90/10 confidence/precision."
        ),
    },

    "6.4": {
        "title": "Project Emissions — Fossil Fuel and Electric Devices (Equations 8–10)",
        "parent_section": "Quantification",
        "must_include": [
            "Eq. 8 (fossil fuel project device): PEy = sum over j,k of [ BCp,j,k,y × NCVp,j × Nj,k,y × nj,k,y × (EFp,j,CO2 + EFp,j,nonCO2) ] — note: no fNRB",
            "Eq. 9 (electric project device — grid): PEy = sum over j,k of [ ECp,j,k,y × Nj,k,y × nj,k,y × EFel,y × (1 + TDLj,y) ]",
            "Eq. 10 (electric project device — self-generated renewable): PEy = 0 (or proportional if backup non-renewable > 20%)",
            "EFel,y source: CDM TOOL07 (combined margin or build margin factor)",
            "TDLj,y source: CDM TOOL05",
            "ECp,j,k,y measured by direct metering (90/10 confidence/precision)",
            "for backup generators >1% of annual electricity: exclude that proportion of ERs",
        ],
        "examples": [
            (
                "Eq. 9 — Electric project stove emissions:\n"
                "ECp,j,k,y = 180 kWh/device/yr = 0.18 MWh/device/yr (direct metering, 90/10 CI)\n"
                "EFel,y = 0.73 tCO2e/MWh (CDM TOOL07 combined margin, Uganda 2023)\n"
                "TDLj,y = 0.18 (CDM TOOL05, Uganda national grid, 2023)\n"
                "Nj,k,y = 50,000; nj,k,y = 0.82\n"
                "PEy = 0.18 × 50,000 × 0.82 × 0.73 × (1 + 0.18) = 6,365 tCO2e/yr"
            ),
        ],
        "failure_modes": [
            "fNRB incorrectly applied to fossil fuel project emissions (Eq. 8 — no fNRB for fossil fuels)",
            "EFel,y not sourced from CDM TOOL07",
            "TDLj,y omitted from electric device emission calculation",
            "ECp,j,k,y derived from billing data rather than direct metering — not acceptable per §9.2",
            "backup generator usage not assessed against the 1% threshold",
        ],
        "content_format": "calculation",
        "format_instructions": (
            "Identify which equation applies based on project device fuel type. "
            "Define all variables with units and data sources. Show the numerical calculation. "
            "For electric devices, explicitly cite the CDM TOOL07 EF and TOOL05 TDL values with vintage year."
        ),
    },

    "6.5": {
        "title": "Leakage (Section 8.3 and Equation 11)",
        "parent_section": "Quantification",
        "must_include": [
            "description of the two leakage pathways: (a) non-renewable biomass displaced but used elsewhere; (b) fossil fuel leakage from LPG/fossil project devices",
            "standard approach (§8.3): both leakage types addressed by applying 0.95 retention factor to (BEy − PEy)",
            "renewable biomass leakage (LERB,y): if applicable, calculated using CDM TOOL16 and subtracted additionally",
            "Eq. 11: ERy = (BEy − PEy) × 0.95 − LERB,y",
            "confirmation of which leakage approach is used (standard 0.95 factor is the default; project-specific is optional)",
        ],
        "examples": [
            (
                "Leakage (§8.3):\n"
                "The project applies the standard leakage approach per VM0050 §8.3. "
                "Both non-renewable biomass leakage and fossil fuel leakage are addressed by the 0.95 retention factor "
                "applied to (BEy − PEy). LERB,y = 0 (no project-specific renewable biomass leakage pathway identified).\n\n"
                "ERy = (BEy − PEy) × 0.95 − LERB,y\n"
                "    = (292,645 − 53,120) × 0.95 − 0\n"
                "    = 239,525 × 0.95 = 227,549 tCO2e/yr"
            ),
        ],
        "failure_modes": [
            "leakage section missing or omitted — not acceptable under VM0050",
            "0.95 factor not applied to gross ER (BEy − PEy) — applied to BE or PE individually instead",
            "renewable biomass leakage pathway identified but TOOL16 calculation not performed",
            "project-specific leakage claimed without substantiation",
        ],
        "content_format": "calculation",
        "format_instructions": (
            "Describe the leakage pathways, confirm the standard 0.95 factor approach, and present Eq. 11 "
            "with numerical values. If LERB,y > 0, show the CDM TOOL16 calculation separately."
        ),
    },

    "6.6": {
        "title": "Net GHG Emission Reductions Summary",
        "parent_section": "Quantification",
        "must_include": [
            "summary table of BEy, PEy, gross ERy = BEy − PEy, LERB,y, and net ERy for each year of crediting period",
            "total ERs over the crediting period",
            "annual average ERy",
            "confirmation that ERy is always >= 0 (no negative ER years reported without explanation)",
        ],
        "examples": [
            (
                "| Year | BEy (tCO2e) | PEy (tCO2e) | Gross ER (tCO2e) | LERB,y | Net ERy (tCO2e) |\n"
                "| 2025 | 292,645 | 53,120 | 239,525 | 0 | 227,549 |\n"
                "| 2026 | 285,000 | 51,800 | 233,200 | 0 | 221,540 |\n"
                "| ... | ... | ... | ... | ... | ... |\n"
                "| Total | 2,750,000 | 500,000 | 2,250,000 | 0 | 2,137,500 |"
            ),
        ],
        "failure_modes": [
            "summary table missing — must include year-by-year breakdown",
            "total and annual average ERy not stated",
            "gross ER column omitted (must show BEy, PEy, and leakage separately)",
        ],
        "content_format": "table",
        "format_instructions": "Present a year-by-year ER table with columns: Year, BEy, PEy, Gross ERy, LERB,y, Net ERy. Include row totals and annual average.",
        "template_scaffold": (
            "| Year | BEy (tCO2e) | PEy (tCO2e) | Gross ERy = BEy−PEy | LERB,y | Net ERy × 0.95 |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| [Year 1] | [...] | [...] | [...] | 0 | [...] |\n"
            "| Total | [...] | [...] | [...] | 0 | [...] |"
        ),
    },

    # ============================================================
    # SECTION 7 — DATA AND PARAMETERS
    # ============================================================
    "7.1": {
        "title": "Data and Parameters Available at Validation (§9.1)",
        "parent_section": "Data and Parameters",
        "must_include": [
            "fNRB,y: value, source (UNFCCC / TOOL30 × 0.74 / TOOL33 v3 Table 2 or 3)",
            "NCVb,i: value in TJ/Gg or TJ/tonne, source (IPCC 2006 / national / project-specific)",
            "NCVp,j: value, source (same hierarchy)",
            "EFb,i,CO2 and EFb,i,nonCO2 (AR5 GWP): values and IPCC 2006 source",
            "EFp,j,CO2 and EFp,j,nonCO2: values and source",
            "ηold,avg (baseline device efficiency): value (default 15% for three-stone fire) and source",
            "ηnew,avg,y (project device efficiency): initial WBT value, test report reference",
            "CF (if charcoal): value (default 4) and source (CDM TOOL33 v3 or national substantiation)",
            "BCex-ante,b,i: value and source (Option 1 KPT or Option 2 default × Hhi)",
            "Hhi (average household size): value and survey reference",
            "EFel,y (for electric devices): value, CDM TOOL07 reference, vintage year",
            "TDLj,y (for electric devices): value, CDM TOOL05 reference",
        ],
        "examples": [
            (
                "| Parameter | Value | Unit | Source |\n"
                "| fNRB,y | 0.72 | fraction | UNFCCC national default, Kenya, 2022 (draft) |\n"
                "| NCVb,i (wood) | 15.6 | TJ/Gg | IPCC 2006 Vol. 2 Table 1.2 |\n"
                "| EFb,i,CO2 (wood) | 112.0 | tCO2/TJ | IPCC 2006 |\n"
                "| EFb,i,nonCO2 (wood) | 9.46 | tCO2e/TJ | IPCC 2006 × AR5 GWP |\n"
                "| ηold,avg | 0.15 | fraction | VM0050 §9.1 default (three-stone fire) |\n"
                "| ηnew,avg,1 | 0.37 | fraction | WBT report ref. WBT-2024-KE-001 |\n"
                "| BCex-ante,b,i | 0.5 × 5.2 = 2.6 t/device/yr | t/device/yr | VM0050 §8.1.1 Option 2 default |"
            ),
        ],
        "failure_modes": [
            "parameters listed without units or data source",
            "ηold,avg and ηnew,avg,y not distinguished in the table",
            "fNRB cited from TOOL30 without applying the 26% discount",
            "WBT test report reference not provided for project device efficiency",
        ],
        "content_format": "table",
        "format_instructions": (
            "Present all §9.1 parameters in a table with columns: Parameter symbol, Description, Value, Unit, "
            "Data source. For each parameter, cite the specific document, table, and year."
        ),
        "template_scaffold": (
            "| Symbol | Description | Value | Unit | Data source |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| fNRB,y | Fraction of non-renewable biomass | [...] | fraction | [...] |\n"
            "| NCVb,i | NCV baseline fuel | [...] | TJ/Gg | IPCC 2006 Table [...] |\n"
            "| EFb,i,CO2 | CO2 EF baseline fuel | [...] | tCO2/TJ | IPCC 2006 |\n"
            "| EFb,i,nonCO2 | Non-CO2 EF baseline fuel | [...] | tCO2e/TJ | IPCC 2006 × AR5 GWP |\n"
            "| ηold,avg | Baseline device efficiency | 0.15 | fraction | VM0050 §9.1 default |\n"
            "| ηnew,avg,y | Project device efficiency | [...] | fraction | WBT report ref. [...] |"
        ),
    },

    "7.2": {
        "title": "Data and Parameters Monitored (§9.2)",
        "parent_section": "Data and Parameters",
        "must_include": [
            "Nj,k,y: number of commissioned project devices (registry/distribution records)",
            "nj,k,y: adoption/usage rate (SUMs or annual survey, 90/10 CI lower bound)",
            "BCb,i,y: baseline fuel consumption from biennial KPT in control households (90/10 CI)",
            "BCp,j,k,y: project fuel consumption from KPT or direct measurement (90/10 CI)",
            "Hhi: household size from baseline survey",
            "ηnew,avg,y: annual monitoring of project device efficiency (WBT or linear decay model)",
            "ECp,j,k,y (electric): direct metering of electricity consumption (90/10 CI)",
            "EFel,y (electric): annual update from CDM TOOL07",
            "TDLj,y (electric): annual update from CDM TOOL05",
            "fNRB,y: annual check against UNFCCC update; update when approved values change",
        ],
        "examples": [
            (
                "| Symbol | Description | Unit | Monitoring freq. | Measurement approach |\n"
                "| nj,k,y | Adoption/usage rate | fraction | Annual | Survey; use lower bound of 90% CI |\n"
                "| BCb,i,y | Baseline fuel consumption | t/device/yr | Biennial (KPT) | KPT in control HH at 90/10 CI |\n"
                "| BCp,j,k,y | Project fuel consumption | t/device/yr | Annual (KPT) | KPT in project HH at 90/10 CI |\n"
                "| ECp,j,k,y | Electricity consumption | MWh/device/yr | Continuous | Direct metering at 90/10 CI |\n"
                "| ηnew,avg,y | Project device efficiency | fraction | Annual | WBT or linear decay to 25% terminal |"
            ),
        ],
        "failure_modes": [
            "nj,k,y based on distribution records only, not an actual usage survey",
            "BCb,i,y not updated biennially as required",
            "KPT not meeting 90/10 confidence/precision requirement",
            "ηnew,avg,y not adjusted for stove aging over the crediting period",
            "fNRB,y not reviewed against UNFCCC updates",
        ],
        "content_format": "table",
        "format_instructions": (
            "Present all §9.2 parameters in a table with columns: Symbol, Description, Unit, "
            "Monitoring frequency, Measurement approach, QA/QC procedure. "
            "Note which parameters require a 90/10 CI standard."
        ),
    },

    # ============================================================
    # SECTION 8 — MONITORING PLAN
    # ============================================================
    "8.0": {
        "title": "Monitoring Plan",
        "parent_section": "Monitoring",
        "must_include": [
            "description of the monitoring system and data management process",
            "KPT procedure for BCb,i,y and BCp,j,k,y with sample size calculation (90/10 CI)",
            "adoption/usage survey procedure for nj,k,y (annual, 90/10 CI, use lower bound)",
            "project device efficiency monitoring approach (WBT annual or linear decay calculation)",
            "stove-stacking cross-check: confirmation of primary cooking fuel and cross-check that efficiency gain is not double-counted across fuels",
            "electric device monitoring: direct metering protocol with 90/10 CI",
            "data management: record retention, QA/QC checks, and audit trail requirements",
            "grouped project instance monitoring: each instance registered with GPS coordinates and device count",
        ],
        "examples": [
            (
                "Kitchen Performance Test (KPT):\n"
                "Baseline KPT is conducted biennially in a stratified random sample of control households "
                "(households that have not received project stoves). Sample size is calculated to achieve "
                "90% confidence / 10% precision on BCb,i,y. Project KPT is conducted annually in a stratified "
                "random sample of project households. Both KPTs are conducted according to the Household Energy "
                "and Health Survey (HEES) protocol.\n\n"
                "Adoption survey (nj,k,y):\n"
                "An annual household survey is conducted to determine the proportion of commissioned devices "
                "still in regular use. Sample size achieves 90% confidence / 10% precision. The lower bound "
                "of the 90% confidence interval is used as nj,k,y in the ER calculation."
            ),
        ],
        "failure_modes": [
            "monitoring plan does not address stove-stacking or cross-checking between fuel types",
            "KPT sample size not calculated to achieve 90/10 CI",
            "nj,k,y monitoring method not described (must be either SUMs or annual survey)",
            "stove aging / ηnew,avg,y monitoring not addressed",
            "data record retention period not stated",
        ],
        "content_format": "prose",
        "format_instructions": (
            "Structure the monitoring plan as follows: (1) Overview; (2) Baseline monitoring (BCb,i,y, fNRB,y); "
            "(3) Project device monitoring (BCp,j,k,y or ECp,j,k,y, nj,k,y, ηnew,avg,y); "
            "(4) Data management and QA/QC; (5) Grouped project instance monitoring. "
            "Cite the specific protocol or standard used for each measurement."
        ),
    },

    # ============================================================
    # SECTION 9 — MONITORING REPORT SPECIFICS
    # ============================================================
    "MR.1": {
        "title": "Monitoring Report — Monitoring Period Summary",
        "parent_section": "Monitoring Report",
        "must_include": [
            "monitoring period start and end dates",
            "total number of devices commissioned (Nj,k,y by batch)",
            "measured nj,k,y value per device batch with survey details (date, sample size, CI)",
            "BCb,i,y result from KPT (if biennial period falls within monitoring period)",
            "BCp,j,k,y result from KPT with date, sample size, and 90% CI",
            "ηnew,avg,y value for the period (WBT result or aging-adjusted value with calculation)",
            "fNRB,y value and confirmation of any UNFCCC update since last period",
            "calculated BEy, PEy, gross ERy, LERB,y, and net ERy",
        ],
        "examples": [
            (
                "Monitoring period: 1 January 2025 to 31 December 2025.\n"
                "Nj,k,y = 80,000 devices (Batch 1: 50,000 commissioned Q1 2024; Batch 2: 30,000 commissioned Q3 2024).\n"
                "nj,k,y = 0.85 (annual survey, March 2025; n=1,100 HH; lower bound of 90% CI = 0.85).\n"
                "BCp,j,k,y = 0.62 t/device/yr (KPT, January 2025; n=380 HH; 90/10 CI confirmed).\n"
                "ηnew,avg,y = 0.36 (WBT Year 1 result, linear decay from initial 0.37).\n"
                "fNRB,y = 0.72 (UNFCCC national default, Kenya 2022 — no update published).\n"
                "BEy = 292,645 tCO2e; PEy = 53,120 tCO2e; ERy = 227,549 tCO2e."
            ),
        ],
        "failure_modes": [
            "monitoring period dates not stated",
            "nj,k,y reported as a point estimate without CI lower bound used in calculation",
            "KPT result not linked to specific survey dates and sample sizes",
            "ηnew,avg,y not updated for device aging",
            "fNRB,y not reviewed for UNFCCC updates",
        ],
        "content_format": "prose",
        "format_instructions": (
            "Present a structured monitoring period summary with sub-sections for: "
            "(1) device counts, (2) usage/adoption, (3) fuel consumption, (4) efficiency, (5) emission factors, "
            "(6) ER calculation results. Reference supporting field data annexes."
        ),
    },
}


def get_subsections() -> dict[str, dict]:
    return SUBSECTIONS


def get_subsection(subsection_id: str) -> dict | None:
    return SUBSECTIONS.get(subsection_id)


def get_parent_sections() -> list[str]:
    parents: list[str] = []
    for s in SUBSECTIONS.values():
        p = s.get("parent_section", "")
        if p and p not in parents:
            parents.append(p)
    return parents


def get_subsections_for_parent(parent_section: str) -> dict[str, dict]:
    return {k: v for k, v in SUBSECTIONS.items() if v.get("parent_section") == parent_section}
