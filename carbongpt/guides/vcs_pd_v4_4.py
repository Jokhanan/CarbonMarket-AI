"""
vcs_pd_v4_4.py — Verra VCS Project Description guide (v4.4).

Full coverage: Sections 1–5 (36 subsections).
"""

GUIDE_ID = "Verra_VCS_PD_v4_4"

SUBSECTIONS: dict[str, dict] = {
    "1.1": {
        "title": "Summary Description of the Project",
        "parent_section": "Project Details",
        "must_include": [
            "summary description of technologies or measures implemented",
            "location of the project",
            "explanation of how the project generates GHG emission reductions or carbon dioxide removals",
            "brief description of the scenario existing prior to project implementation",
            "estimate of annual average and total reductions and removals",
        ],
        "examples": [
            "The project installs 50 MW of solar PV capacity in Gujarat, India, displacing grid electricity generated from fossil fuels and reducing approximately 75,000 tCO2e per year.",
        ],
        "failure_modes": [
            "description exceeds one page without providing a concise summary",
            "no explanation of the GHG reduction or removal mechanism",
            "missing estimate of annual average or total emission reductions",
            "prior scenario not described",
        ],
    },
    "1.2": {
        "title": "Audit History",
        "parent_section": "Project Details",
        "must_include": [
            "audit history table for projects undergoing crediting period renewal",
            "audit type (validation or verification)",
            "period covered by each audit (start and end dates)",
            "name of the validation/verification body",
            "number of years covered",
        ],
        "examples": [
            "Validation: 01-Jan-2018 to 31-Dec-2018, VCS, SCS Global Services, 1 year.",
        ],
        "failure_modes": [
            "audit history table missing for crediting period renewal projects",
            "validation/verification body name not provided",
            "audit periods not specified with start and end dates",
            "current monitoring period not included in the table",
        ],
    },
    "1.3": {
        "title": "Sectoral Scope and Project Type",
        "parent_section": "Project Details",
        "must_include": [
            "sectoral scope number",
            "project activity type",
            "for AFOLU projects: AFOLU project category",
        ],
        "examples": [
            "Sectoral scope: 1 (Energy industries). Project activity type: Renewable energy generation.",
            "Sectoral scope: 14 (AFOLU). AFOLU project category: ARR. Project activity type: Afforestation.",
        ],
        "failure_modes": [
            "sectoral scope not specified",
            "project activity type missing",
            "AFOLU project category not provided for AFOLU projects",
            "non-AFOLU table used for an AFOLU project or vice versa",
        ],
    },
    "1.4": {
        "title": "Project Eligibility",
        "parent_section": "Project Details",
        "must_include": [
            "justification that the project activity is within the scope of the VCS Program",
            "demonstration that the project is not excluded under Table 2.1 of the VCS Standard",
            "evidence of meeting pipeline listing deadline and validation deadline requirements",
            "demonstration that the applied methodology is eligible under the VCS Program",
            "for AFOLU projects: justification of AFOLU project category eligibility",
        ],
        "examples": [
            "The project is a grid-connected renewable energy project, which is within the scope of the VCS Program. The activity is not listed as excluded under Table 2.1 of the VCS Standard.",
        ],
        "failure_modes": [
            "no reference to VCS Standard Table 2.1 exclusion list",
            "eligibility criteria addressed generically without project-specific justification",
            "pipeline listing and validation deadline requirements not discussed",
            "methodology eligibility not demonstrated",
            "AFOLU eligibility requirements not addressed for AFOLU projects",
        ],
    },
    "1.5": {
        "title": "Project Design",
        "parent_section": "Project Details",
        "must_include": [
            "indication of project design type: single location, multiple locations, or grouped project",
            "for grouped projects: eligibility criteria for new project activity instances",
            "for grouped projects: additional design information",
        ],
        "examples": [
            "The project is designed as a single location installation.",
            "The project is designed as a grouped project. New instances must meet the following eligibility criteria: located within the host country, use approved cookstove models, and demonstrate compliance with the methodology applicability conditions.",
        ],
        "failure_modes": [
            "project design type not indicated",
            "grouped project selected but no eligibility criteria for new instances provided",
            "multiple locations indicated but not distinguished from grouped project design",
        ],
    },
    "1.6": {
        "title": "Project Proponent",
        "parent_section": "Project Details",
        "must_include": [
            "organization name of the project proponent",
            "contact person name",
            "title of contact person",
            "address",
            "telephone number",
            "email address with domain matching the organization",
        ],
        "examples": [
            "Organization: GreenEnergy Corp. Contact: Jane Smith, Director of Carbon Projects. Address: 123 Sustainability Ave, Mumbai, India. Email: jane.smith@greenenergy.com.",
        ],
        "failure_modes": [
            "contact information incomplete (missing phone, email, or address)",
            "email domain does not match the organization",
            "multiple proponents listed without separate tables for each",
        ],
    },
    "1.7": {
        "title": "Other Entities Involved in the Project",
        "parent_section": "Project Details",
        "must_include": [
            "organization name of each entity involved",
            "role in the project for each entity",
            "contact person, title, address, telephone, and email for each entity",
        ],
        "examples": [
            "Organization: CarbonConsult Ltd. Role: Project design and methodology application. Contact: John Doe, Senior Consultant.",
        ],
        "failure_modes": [
            "entities listed without specifying their role in the project",
            "contact details incomplete for listed entities",
            "section left blank without stating that no other entities are involved",
        ],
    },
    "1.8": {
        "title": "Ownership",
        "parent_section": "Project Details",
        "must_include": [
            "evidence of project ownership",
            "conformance with VCS Program requirements on project ownership",
        ],
        "examples": [
            "Project ownership is evidenced by the Power Purchase Agreement between GreenEnergy Corp and the State Electricity Board, and the land lease agreement for the project site.",
        ],
        "failure_modes": [
            "no evidence of project ownership provided",
            "ownership claim made without supporting documentation",
            "VCS Program ownership requirements not referenced",
        ],
    },
    "1.9": {
        "title": "Project Start Date",
        "parent_section": "Project Details",
        "must_include": [
            "project start date in DD-Month-YYYY format",
            "justification of how the start date conforms with VCS Program requirements",
        ],
        "examples": [
            "Project start date: 15-March-2020. The start date is the date of the first concrete action (ground-breaking for plant construction), conforming with the VCS Standard definition.",
        ],
        "failure_modes": [
            "start date not provided in required format",
            "no justification for how the start date conforms with VCS requirements",
            "start date appears inconsistent with documented project activities",
        ],
    },
    "1.10": {
        "title": "Project Crediting Period",
        "parent_section": "Project Details",
        "must_include": [
            "crediting period type selected (seven years twice renewable, ten years fixed, or other)",
            "start and end date of the first or fixed crediting period",
            "justification if 'other' crediting period is selected",
        ],
        "examples": [
            "Crediting period: Seven years, twice renewable. First crediting period: 01-January-2020 to 31-December-2026.",
        ],
        "failure_modes": [
            "crediting period type not specified",
            "start and end dates of crediting period not provided",
            "crediting period selected does not conform with VCS Program requirements",
        ],
    },
    "1.11": {
        "title": "Project Scale and Estimated GHG Emission Reductions or Removals",
        "parent_section": "Project Details",
        "must_include": [
            "indication of project scale (less than or greater than 300,000 tCO2e/year)",
            "table of estimated GHG emission reductions or removals by calendar year",
            "total estimated ERRs during the crediting period",
            "total number of years",
            "average annual ERRs",
        ],
        "examples": [
            "Project scale: < 300,000 tCO2e/year. Total estimated ERRs: 525,000 tCO2e over 7 years. Average annual ERRs: 75,000 tCO2e.",
        ],
        "failure_modes": [
            "project scale not indicated",
            "estimated ERRs table missing or incomplete",
            "total and average annual ERRs not calculated",
            "calendar years in the table do not match the crediting period",
        ],
    },
    "1.12": {
        "title": "Description of the Project Activity",
        "parent_section": "Project Details",
        "must_include": [
            "description of the project activity or activities",
            "technologies or measures employed",
            "how the activity achieves GHG emission reductions or carbon dioxide removals",
            "implementation schedule",
            "for non-AFOLU: list of main manufacturing/production technologies and equipment",
            "for non-AFOLU: age, average lifetime, installed capacities, load factors, and efficiencies of equipment",
        ],
        "examples": [
            "The project installs three 15 MW wind turbines (Vestas V110, 25-year design life) at the project site. The turbines generate renewable electricity displacing fossil-fuel-based grid electricity.",
        ],
        "failure_modes": [
            "project activity described without specifying the technology or measures",
            "no implementation schedule provided",
            "equipment details missing for non-AFOLU projects (age, capacity, efficiency)",
            "no explanation of how baseline services would have been provided",
            "AFOLU-specific requirements not addressed for AFOLU projects",
        ],
    },
    "1.13": {
        "title": "Project Location",
        "parent_section": "Project Details",
        "must_include": [
            "project location description",
            "geographic boundaries",
            "set of geodetic coordinates",
            "for AFOLU, GCS, grouped projects, or multiple instances: separate KML file",
        ],
        "examples": [
            "The project is located in Rajasthan, India (26.9124 N, 70.9120 E). The project boundary encompasses the solar farm site of approximately 100 hectares.",
        ],
        "failure_modes": [
            "no geodetic coordinates provided",
            "geographic boundaries not described",
            "KML file not provided for AFOLU or grouped projects",
            "location description too vague (country-level only)",
        ],
    },
    "1.14": {
        "title": "Conditions Prior to Project Initiation",
        "parent_section": "Project Details",
        "must_include": [
            "description of conditions existing prior to project initiation",
            "demonstration that the project was not implemented to generate GHG emissions for subsequent reduction",
            "for AFOLU: ecosystem type description",
            "for AFOLU: current and historical land-use description",
            "for AFOLU: environmental conditions (climate, hydrology, topography, soils, vegetation)",
        ],
        "examples": [
            "Prior to the project, the site was unused barren land with no electricity generation infrastructure. The baseline scenario is described in Section 3.4.",
        ],
        "failure_modes": [
            "pre-project conditions not described",
            "no demonstration that the project was not created to generate emissions for subsequent reduction",
            "AFOLU-specific information missing (ecosystem type, land-use history, environmental conditions)",
            "section left blank or only references Section 3.4 without any description",
        ],
    },
    "1.15": {
        "title": "Compliance with Laws, Statutes and Other Regulatory Frameworks",
        "parent_section": "Project Details",
        "must_include": [
            "identification of relevant local, regional and national laws and regulations",
            "demonstration of compliance with identified legal and regulatory frameworks",
        ],
        "examples": [
            "The project complies with the Indian Electricity Act 2003, the Environmental Impact Assessment Notification 2006, and all applicable state-level regulations for renewable energy projects.",
        ],
        "failure_modes": [
            "no specific laws or regulations identified",
            "compliance claimed without supporting evidence or demonstration",
            "only general statements without reference to specific legal frameworks",
        ],
    },
    "1.16": {
        "title": "Double Counting and Participation under Other GHG Programs",
        "parent_section": "Project Details",
        "must_include": [
            "statement on whether the project is receiving or seeking credit under another GHG program (no double issuance)",
            "statement on whether the project has registered under any other GHG programs",
            "if registered elsewhere: registration number and date of project inactivity",
            "statement on whether the project has been rejected by other GHG programs",
            "if rejected: program name, reason, date, and justification of VCS eligibility",
        ],
        "examples": [
            "The project is not receiving or seeking credit under any other GHG program. The project has not been registered under or rejected by any other GHG program.",
        ],
        "failure_modes": [
            "double issuance question not answered (yes/no)",
            "registration under other programs not disclosed",
            "rejection by other programs not addressed",
            "evidence of no double issuance not provided when project is under another program",
        ],
    },
    "1.17": {
        "title": "Double Claiming, Other Forms of Credit, and Scope 3 Emissions",
        "parent_section": "Project Details",
        "must_include": [
            "statement on whether reductions are included in an emissions trading program or binding emission limit",
            "statement on whether the project has sought or received credit from another GHG-related environmental credit system",
            "statement on whether project activities affect supply chain (Scope 3) emissions",
            "if Scope 3 applies: disclosure of buyer/seller status and public statement evidence",
        ],
        "examples": [
            "The project reductions are not included in any emissions trading program or binding emission limit. The project has not sought credit from any other GHG-related environmental credit system. The project does not affect supply chain emissions.",
        ],
        "failure_modes": [
            "emissions trading program or binding emission limit question not answered",
            "other environmental credit systems not addressed",
            "Scope 3 emissions impact not assessed",
            "public statement evidence not provided when required",
        ],
    },
    "1.18": {
        "title": "Sustainable Development Contributions",
        "parent_section": "Project Details",
        "must_include": [
            "summary description of project activities resulting in sustainable development contributions (max 500 words)",
            "explanation of how project activities result in expected SD contributions",
            "description of how the project contributes to nationally stated sustainable development priorities",
            "provisions for monitoring and reporting SD contributions",
        ],
        "examples": [
            "The project contributes to SDG 7 (Affordable and Clean Energy) by adding 50 MW of renewable capacity and SDG 13 (Climate Action) by reducing approximately 75,000 tCO2e annually. These align with India's National Action Plan on Climate Change.",
        ],
        "failure_modes": [
            "description exceeds 500 words",
            "SD contributions claimed without explanation of how activities produce them",
            "no reference to nationally stated SD priorities",
            "monitoring and reporting provisions not discussed",
        ],
    },
    "1.19": {
        "title": "Additional Information Relevant to the Project",
        "parent_section": "Project Details",
        "must_include": [
            "leakage management plan and implementation of mitigation measures (where applicable)",
            "indication of whether commercially sensitive information has been excluded (with justification)",
            "any additional relevant legislative, technical, economic, or environmental information",
        ],
        "examples": [
            "No commercially sensitive information has been excluded from this project description. No leakage management plan is required as the methodology does not identify leakage sources.",
        ],
        "failure_modes": [
            "commercially sensitive information section left blank without explicit statement",
            "leakage management not addressed where applicable",
            "information excluded without justification for commercial sensitivity",
            "baseline, additionality, or monitoring information claimed as commercially sensitive",
        ],
    },
    "2.1": {
        "title": "Stakeholder Engagement and Consultation",
        "parent_section": "Safeguards and Stakeholder engagement",
        "must_include": [
            "stakeholder identification process and list of identified stakeholders",
            "description of legal or customary tenure/access rights held by stakeholders",
            "social, economic, and cultural diversity within stakeholder groups",
            "expected changes in well-being relative to baseline scenario",
            "location of stakeholders and areas predicted to be impacted",
            "stakeholder consultation date and engagement process",
            "consultation outcome including discussion of consent, risks, costs and benefits",
            "mechanisms for ongoing communication",
            "FPIC process description and outcome",
            "grievance redress procedure development and description",
        ],
        "examples": [
            "Stakeholder consultation was held on 10-March-2019 with representatives from three local villages. FPIC was obtained through community meetings conducted in the local language.",
        ],
        "failure_modes": [
            "stakeholder identification process not described",
            "no list of identified stakeholders",
            "FPIC process not documented or outcome not described",
            "grievance redress procedure not developed or described",
            "consultation outcomes not summarized",
            "ongoing communication mechanisms not specified",
            "stakeholder diversity and changes over time not discussed",
        ],
    },
    "2.2": {
        "title": "Risks to Stakeholders and the Environment",
        "parent_section": "Safeguards and Stakeholder engagement",
        "must_include": [
            "identification of risks the project poses to stakeholders and the environment",
            "natural and human-induced risks to the project and mitigation measures",
            "management of identified risks including mitigation strategy",
        ],
        "examples": [
            "Risk: Potential loss of grazing land for local herders. Mitigation: Alternative grazing areas have been identified and agreements reached with affected herders.",
        ],
        "failure_modes": [
            "no risk identification performed",
            "risks identified but no mitigation measures described",
            "environmental risks not assessed",
            "natural and human-induced risks not addressed",
        ],
    },
    "2.3": {
        "title": "Respect for Human Rights and Equity",
        "parent_section": "Safeguards and Stakeholder engagement",
        "must_include": [
            "demonstration that the project respects human rights",
            "assessment of project impacts on equity",
            "measures to ensure equitable benefit sharing",
            "labor and working conditions assessment",
        ],
        "examples": [
            "The project adheres to the ILO core labor standards. Equitable benefit sharing is ensured through a community development fund receiving 2% of carbon credit revenue.",
        ],
        "failure_modes": [
            "no reference to human rights considerations",
            "equity impacts not assessed",
            "benefit sharing mechanisms not described",
            "labor and working conditions not addressed",
        ],
    },
    "2.4": {
        "title": "Ecosystem Health",
        "parent_section": "Safeguards and Stakeholder engagement",
        "must_include": [
            "assessment of impacts on biodiversity and ecosystems",
            "identification of rare, threatened, or endangered species in the project area",
            "measures to protect ecosystem health",
            "for AFOLU: evidence that native ecosystems have not been converted to generate GHG credits",
            "for ARR/ALM/WRC/ACoGS: evidence that clearing or conversion did not occur within 10 years of project start date",
        ],
        "examples": [
            "An environmental impact assessment confirmed no rare or threatened species in the project area. The project site was previously degraded agricultural land with no native ecosystem conversion.",
        ],
        "failure_modes": [
            "no assessment of biodiversity impacts",
            "rare or threatened species not identified or assessed",
            "ecosystem protection measures not described",
            "AFOLU projects lacking evidence of no native ecosystem conversion",
            "section left blank or marked not applicable without justification",
        ],
    },
    "3.1": {
        "title": "Title and Reference of Methodology",
        "parent_section": "Application of Methodology",
        "must_include": [
            "full title of the applied methodology",
            "version number of the methodology",
            "any applicable methodological tools or modules",
            "any other applied methodologies or standardized methods",
        ],
        "examples": [
            "Methodology: ACM0002 Grid-connected electricity generation from renewable sources, version 20.0. Tool: TOOL07 Tool to calculate the emission factor for an electricity system, version 07.0.",
        ],
        "failure_modes": [
            "methodology title provided without version number",
            "applicable tools or modules not listed",
            "wrong methodology referenced for the project type",
        ],
    },
    "3.2": {
        "title": "Applicability of Methodology",
        "parent_section": "Application of Methodology",
        "must_include": [
            "demonstration that the project meets all applicability conditions of the methodology",
            "each applicability condition addressed individually with project-specific justification",
        ],
        "examples": [
            "Applicability condition 1: The project is a grid-connected renewable energy facility. Justification: The project connects to the state grid through a 132 kV transmission line as evidenced by the grid connection agreement.",
        ],
        "failure_modes": [
            "applicability conditions not individually addressed",
            "generic claims of applicability without project-specific evidence",
            "not all applicability conditions covered",
            "applicability of methodological tools not demonstrated",
        ],
    },
    "3.3": {
        "title": "Project Boundary",
        "parent_section": "Application of Methodology",
        "must_include": [
            "description of the project boundary",
            "GHG sources, sinks, and reservoirs included and excluded",
            "justification for exclusion of any sources, sinks, or reservoirs",
            "gases included (CO2, CH4, N2O, etc.) with justification",
        ],
        "examples": [
            "The project boundary includes the solar PV plant and grid connection point. Included source: grid electricity displacement (CO2). Excluded: SF6 from switchgear (conservative exclusion, minor source).",
        ],
        "failure_modes": [
            "project boundary not clearly defined",
            "GHG sources, sinks, and reservoirs not listed",
            "excluded sources not justified",
            "gases included not specified",
        ],
    },
    "3.4": {
        "title": "Baseline Scenario",
        "parent_section": "Application of Methodology",
        "must_include": [
            "identification and description of the baseline scenario",
            "justification for the selection of the baseline scenario",
            "description of how the baseline scenario is identified per the methodology",
        ],
        "examples": [
            "The baseline scenario is the continued use of grid electricity generated from the existing mix of fossil fuel and renewable sources. This is identified using Step 1 of the combined tool per ACM0002.",
        ],
        "failure_modes": [
            "baseline scenario not clearly identified",
            "no justification for baseline scenario selection",
            "methodology procedure for identifying baseline not followed",
            "alternative scenarios not considered where required by methodology",
        ],
    },
    "3.5": {
        "title": "Additionality",
        "parent_section": "Application of Methodology",
        "must_include": [
            "demonstration of additionality following the methodology or applicable VCS tool",
            "investment analysis, barrier analysis, or common practice analysis as required",
            "evidence and data supporting the additionality demonstration",
        ],
        "examples": [
            "Additionality is demonstrated using TOOL01 (version 07.0). The investment analysis shows that the project IRR of 8.2% is below the benchmark of 12%, confirming the project is not financially attractive without carbon revenue.",
        ],
        "failure_modes": [
            "additionality not demonstrated using the required approach",
            "investment analysis conducted without transparent assumptions",
            "barrier analysis claims not substantiated with evidence",
            "common practice analysis missing where required",
            "sensitivity analysis not performed for investment analysis",
        ],
    },
    "3.6": {
        "title": "Methodology Deviations",
        "parent_section": "Application of Methodology",
        "must_include": [
            "description of any methodology deviations applied",
            "justification that deviations meet VCS Program requirements",
            "if no deviations: explicit statement that no methodology deviations have been applied",
        ],
        "examples": [
            "No methodology deviations have been applied.",
            "A deviation from the default emission factor was applied using country-specific data from the National GHG Inventory, which is more accurate and conservative.",
        ],
        "failure_modes": [
            "section left blank without stating whether deviations exist",
            "deviation applied but not described or justified",
            "deviation does not meet VCS requirements but is not flagged",
        ],
    },
    "4.1": {
        "title": "Baseline Emissions",
        "parent_section": "Quantification of Estimated GHG Emission Reductions and Removals",
        "must_include": [
            "equations used to estimate baseline emissions",
            "description of all parameters and data sources",
            "estimated baseline emissions for each year of the crediting period",
        ],
        "examples": [
            "Baseline emissions: BE_y = EG_y * EF_grid. Where EG_y = net electricity generation (MWh), EF_grid = combined margin emission factor (tCO2/MWh). BE_2020 = 150,000 * 0.85 = 127,500 tCO2.",
        ],
        "failure_modes": [
            "equations not provided or not consistent with the methodology",
            "parameter values listed without data sources",
            "baseline emissions not estimated for all years of the crediting period",
            "calculation steps not shown transparently",
        ],
    },
    "4.2": {
        "title": "Project Emissions",
        "parent_section": "Quantification of Estimated GHG Emission Reductions and Removals",
        "must_include": [
            "equations used to estimate project emissions",
            "description of all parameters and data sources",
            "estimated project emissions for each year of the crediting period",
        ],
        "examples": [
            "Project emissions: PE_y = 0 (solar PV generates no direct GHG emissions during operation).",
        ],
        "failure_modes": [
            "equations not provided or not consistent with the methodology",
            "if project emissions are zero: no explicit justification provided",
            "parameter values listed without data sources",
            "project emissions not estimated for all years of the crediting period",
        ],
    },
    "4.3": {
        "title": "Leakage Emissions",
        "parent_section": "Quantification of Estimated GHG Emission Reductions and Removals",
        "must_include": [
            "equations used to estimate leakage emissions",
            "description of all parameters and data sources",
            "estimated leakage for each year of the crediting period",
            "if no leakage: explicit statement with justification per the methodology",
        ],
        "examples": [
            "Leakage: LE_y = 0. Per ACM0002, no leakage sources are identified for grid-connected solar PV projects.",
        ],
        "failure_modes": [
            "leakage section left blank without stating whether leakage applies",
            "leakage assumed zero without methodology justification",
            "leakage sources identified in methodology but not quantified",
        ],
    },
    "4.4": {
        "title": "Estimated GHG Emission Reductions and Carbon Dioxide Removals",
        "parent_section": "Quantification of Estimated GHG Emission Reductions and Removals",
        "must_include": [
            "summary table of estimated GHG emission reductions or removals by year",
            "calculation: ERR_y = BE_y - PE_y - LE_y for each year",
            "total estimated emission reductions or removals for the crediting period",
        ],
        "examples": [
            "Year 2020: BE = 127,500 tCO2, PE = 0, LE = 0, ERR = 127,500 tCO2e. Total ERRs (2020-2026): 892,500 tCO2e.",
        ],
        "failure_modes": [
            "summary table missing or incomplete",
            "ERR not calculated as baseline minus project minus leakage",
            "totals do not match the sum of annual estimates",
            "values inconsistent with Section 1.11 estimates",
        ],
    },
    "5.1": {
        "title": "Data and Parameters Available at Validation",
        "parent_section": "Monitoring",
        "must_include": [
            "table of all data and parameters available at validation (fixed ex ante)",
            "for each parameter: data unit, description, source of data",
            "value applied for each parameter",
            "justification of choice of data or description of measurement methods",
            "purpose of data in the calculation",
            "any comments on the parameter",
        ],
        "examples": [
            "Parameter: EF_grid. Unit: tCO2/MWh. Description: Combined margin emission factor. Source: National grid authority published data. Value: 0.85 tCO2/MWh. Purpose: Baseline emission calculation.",
        ],
        "failure_modes": [
            "parameter table missing or incomplete",
            "parameter values provided without sources",
            "purpose of data not specified for each parameter",
            "measurement methods not described where applicable",
            "not all ex ante parameters listed",
        ],
    },
    "5.2": {
        "title": "Data and Parameters Monitored",
        "parent_section": "Monitoring",
        "must_include": [
            "table of all data and parameters to be monitored",
            "for each parameter: data unit, description, source of data",
            "description of measurement methods and procedures",
            "monitoring and recording frequency",
            "QA/QC procedures applied",
            "purpose of data in the calculation",
            "calculation method if the parameter is calculated from other measured values",
        ],
        "examples": [
            "Parameter: EG_y. Unit: MWh. Description: Net electricity generated. Source: Calibrated energy meters at the grid connection point. Frequency: Continuous, recorded monthly. QA/QC: Meters calibrated annually per manufacturer specifications.",
        ],
        "failure_modes": [
            "monitored parameter table missing or incomplete",
            "measurement methods and frequency not described",
            "QA/QC procedures not specified",
            "source of data not traceable",
            "not all monitored parameters listed as required by the methodology",
        ],
    },
    "5.3": {
        "title": "Monitoring Plan",
        "parent_section": "Monitoring",
        "must_include": [
            "description of the monitoring plan",
            "organizational structure and responsibilities for monitoring",
            "description of the data management system",
            "procedures for handling data gaps and uncertainties",
            "internal auditing and QA/QC procedures",
        ],
        "examples": [
            "The monitoring plan follows ACM0002 requirements. The plant manager is responsible for data collection. Data is recorded in the centralized SCADA system and backed up monthly to cloud storage.",
        ],
        "failure_modes": [
            "no monitoring plan described",
            "organizational responsibilities not defined",
            "data management procedures not specified",
            "QA/QC and internal audit procedures not included",
            "monitoring plan not aligned with the applied methodology",
        ],
    },
}


def get_subsections() -> dict[str, dict]:
    return SUBSECTIONS


def get_subsection(subsection_id: str) -> dict | None:
    return SUBSECTIONS.get(subsection_id)


def get_parent_sections() -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for sub in SUBSECTIONS.values():
        ps = sub["parent_section"]
        if ps not in seen:
            seen.add(ps)
            result.append(ps)
    return result


def get_subsections_for_parent(parent_section: str) -> dict[str, dict]:
    return {
        k: v for k, v in SUBSECTIONS.items()
        if v["parent_section"] == parent_section
    }
