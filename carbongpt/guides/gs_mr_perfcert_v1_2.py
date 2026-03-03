"""
gs_mr_perfcert_v1_2.py — Gold Standard Monitoring Report guide
(Performance Certification v1.2).

Full coverage: Sections A–G.
"""

GUIDE_ID = "GoldStandard_MR_PerfCert_v1_2"

SUBSECTIONS: dict[str, dict] = {
    "A.1": {
        "title": "General description of the project",
        "parent_section": "SECTION A",
        "must_include": [
            "purpose and objective of the project",
            "type of GHG emission reduction or removal activity",
            "technology or measure employed",
            "brief summary of how the project reduces or removes emissions",
        ],
        "examples": [
            "The project distributes improved cookstoves to households, reducing firewood consumption and associated CO2 emissions.",
        ],
        "failure_modes": [
            "description is too vague or generic without specifying the actual activity",
            "no mention of the GHG reduction mechanism",
            "copy-pasted boilerplate text that does not describe the specific project",
        ],
        "content_format": "prose",
        "format_instructions": "Write a concise narrative covering the project purpose, activity type, technology employed, and GHG reduction mechanism. Use sub-headings if the description spans multiple activity components.",
    },
    "A.2": {
        "title": "Location of the project",
        "parent_section": "SECTION A",
        "must_include": [
            "host country",
            "region or province",
            "physical address or GPS coordinates of project site(s)",
            "map or reference to a map showing the project boundary",
        ],
        "examples": [
            "The project is located in Siaya County, Kenya (0.0617° S, 34.2422° E).",
        ],
        "failure_modes": [
            "no geographic coordinates provided",
            "only country-level description without specific location",
            "map referenced but not included or attached",
        ],
        "content_format": "prose",
        "format_instructions": "Provide host country, region/province, and GPS coordinates. Include a placeholder for a map showing the project boundary.",
    },
    "A.3": {
        "title": "Parties and project participants",
        "parent_section": "SECTION A",
        "must_include": [
            "name and role of each project participant or entity",
            "contact details for the coordinating or managing entity",
            "host country party (DNA) involvement if applicable",
        ],
        "examples": [
            "Project Developer: CleanCook Ltd (Kenya). Coordinating entity: GreenCarbon GmbH (Germany).",
        ],
        "failure_modes": [
            "project participants not listed by name and role",
            "no contact information provided for the coordinating entity",
            "roles are ambiguous or not clearly assigned",
        ],
        "content_format": "table",
        "format_instructions": "Present project participants in a table with columns: Entity Name | Role | Country | Contact Details. Include a row for each project participant and the coordinating/managing entity.",
    },
    "A.4": {
        "title": "Reference of applied methodology",
        "parent_section": "SECTION A",
        "must_include": [
            "full name of the methodology",
            "version number of the methodology applied",
            "any applicable methodological tools or combined methodologies",
        ],
        "examples": [
            "AMS-II.G: Energy efficiency measures in thermal applications of non-renewable biomass, version 09.",
        ],
        "failure_modes": [
            "methodology name given without version number",
            "wrong methodology referenced for the project type",
            "methodological tools used but not listed",
        ],
        "content_format": "prose",
        "format_instructions": "State the full methodology name and version number. List any applicable methodological tools or combined methodologies used.",
    },
    "B.1": {
        "title": "Implementation status of the project",
        "parent_section": "SECTION B",
        "must_include": [
            "current operational status of the project",
            "date of start of project operation / crediting period",
            "description of actual implementation versus project design",
            "any deviations from the registered PDD",
        ],
        "examples": [
            "The project has been operational since 01/01/2020. 15,000 cookstoves have been distributed as of the end of this monitoring period.",
        ],
        "failure_modes": [
            "no clear statement of whether the project is operational",
            "start date of operation not provided",
            "deviations from PDD not disclosed or discussed",
        ],
        "content_format": "prose",
        "format_instructions": "Describe the current operational status, start date, implementation progress versus the project design, and any deviations from the registered PDD.",
    },
    "B.2": {
        "title": "Post-registration changes",
        "parent_section": "SECTION B",
        "must_include": [
            "whether any post-registration changes have occurred",
            "if changes occurred: description, approval status, and impact on emission reductions",
            "if no changes: explicit statement that no post-registration changes have been made",
        ],
        "examples": [
            "No post-registration design changes have been made during this monitoring period.",
            "A change in project boundary was approved on 15/06/2023 (change request CR-001).",
        ],
        "failure_modes": [
            "section is blank or contains placeholder text",
            "changes occurred but are not described",
            "no explicit statement confirming presence or absence of changes",
        ],
        "content_format": "prose",
        "format_instructions": "Clearly state whether any post-registration changes have occurred. If changes occurred, describe each change, its approval status, and impact on emission reductions.",
    },
    "B.3": {
        "title": "Compliance with applicable rules and standards",
        "parent_section": "SECTION B",
        "must_include": [
            "confirmation of compliance with Gold Standard rules and requirements",
            "reference to any applicable host country regulations",
            "status of environmental and social safeguards requirements",
        ],
        "examples": [
            "The project complies with all applicable Gold Standard requirements and host country environmental regulations.",
        ],
        "failure_modes": [
            "no explicit compliance statement",
            "host country regulations not referenced",
            "safeguards requirements not addressed",
        ],
        "content_format": "prose",
        "format_instructions": "Provide an explicit compliance statement covering Gold Standard rules, host country regulations, and environmental and social safeguards requirements.",
    },
    "C.1": {
        "title": "Description of the monitoring system",
        "parent_section": "SECTION C",
        "must_include": [
            "description of the monitoring system as implemented",
            "alignment with the monitoring plan in the Design Certified PDD",
            "description of data collection procedures and instruments used",
            "roles and responsibilities for monitoring activities",
        ],
        "examples": [
            "Monitoring is conducted by trained field officers using digital survey tools. Data is collected monthly and cross-checked against distribution records per the approved monitoring plan.",
        ],
        "failure_modes": [
            "no reference to the monitoring plan in the PDD",
            "monitoring system described at a high level without operational details",
            "no mention of who is responsible for data collection",
            "instruments or tools used for measurement not specified",
        ],
        "content_format": "prose",
        "format_instructions": "Describe the monitoring system as implemented, referencing the approved monitoring plan. Cover data collection procedures, instruments used, and roles and responsibilities.",
    },
    "D.1": {
        "title": "Data and parameters fixed ex ante",
        "parent_section": "SECTION D",
        "must_include": [
            "compilation of all parameters fixed before design certification",
            "value applied for each parameter",
            "source of data for each parameter with traceable references",
            "measurement methods and procedures where applicable",
            "purpose of data (baseline, project, or leakage calculation)",
            "parameters organized under SDG headings, with SDG 13 first",
        ],
        "examples": [
            "Parameter: EF_CO2 (CO2 emission factor for biomass). Value: 112 gCO2/MJ. Source: IPCC 2006 Guidelines, Table 2.5. Purpose: Calculation of baseline scenario.",
        ],
        "failure_modes": [
            "parameter values listed without sources",
            "sources referenced but not traceable (e.g. missing filenames or page numbers)",
            "purpose of data not specified for each parameter",
            "parameters duplicated across SDG headings instead of cross-referenced",
            "IPCC or methodology defaults used without citing the specific table or version",
        ],
        "content_format": "parameter_blocks",
        "format_instructions": "Present each ex ante parameter as a structured block with fields: Parameter Name, Symbol, Unit, Value, Source (with traceable reference), Measurement Method, Purpose (baseline/project/leakage). Organize parameters under SDG headings with SDG 13 first.",
    },
    "D.2": {
        "title": "Data and parameters monitored",
        "parent_section": "SECTION D",
        "must_include": [
            "all monitored parameters with values obtained during the monitoring period",
            "source of data with traceable references (filenames, sheet names)",
            "description of QA/QC procedures applied",
            "measurement methods and frequency",
            "parameters organized under SDG headings, with SDG 13 first",
        ],
        "examples": [
            "Parameter: Up,y (usage rate). Value: 0.83. Source: Developer Name Usage Survey results.xls (Summary Sheet). QA/QC: Cross-checked against field records and independently verified by team lead.",
        ],
        "failure_modes": [
            "monitored values not transparently reported in the document",
            "source data references missing filenames or sheet names",
            "no description of QA/QC procedures",
            "usage rates reported without showing age group breakdown and weighted average",
            "measured vs capped values not both reported where methodology requires capping",
        ],
        "content_format": "parameter_blocks",
        "format_instructions": "Present each monitored parameter as a structured block with fields: Parameter Name, Symbol, Unit, Value, Source (filename and sheet name), Measurement Method, Frequency, QA/QC Procedures, Purpose. Organize parameters under SDG headings with SDG 13 first.",
    },
    "D.3": {
        "title": "Comparison of monitored parameters with last monitoring period",
        "parent_section": "SECTION D",
        "must_include": [
            "table comparing current monitoring period values with previous period values",
            "explanation for any values that have increased or are less conservative",
        ],
        "examples": [
            "Parameter Up,y: current period 0.83, previous period 0.79. Increase due to improved adoption observed in year 3 of distribution.",
        ],
        "failure_modes": [
            "no comparison table provided",
            "values changed significantly with no explanation",
            "section marked N/A for Community Service Activities (should be completed)",
            "previous period values not reported",
        ],
        "content_format": "table",
        "format_instructions": "Present a comparison table with columns: Parameter | Current Period Value | Previous Period Value | Explanation. Include a row for each monitored parameter, with explanations for any values that have increased or become less conservative.",
    },
    "D.4": {
        "title": "Implementation of sampling plan",
        "parent_section": "SECTION D",
        "must_include": [
            "description of implemented sampling design",
            "collected data summary",
            "analysis of collected data",
            "demonstration that the required confidence/precision level has been met",
            "demonstration that samples were randomly selected and representative",
        ],
        "examples": [
            "A stratified random sample of 300 households was selected. The 95/10 confidence/precision threshold was achieved with a margin of error of 7.2%.",
        ],
        "failure_modes": [
            "sampling design described in theory but actual implementation not documented",
            "confidence/precision level not demonstrated with calculations",
            "no evidence that sample was randomly selected",
            "spreadsheets or detailed calculations not referenced or attached",
            "section left blank when D.2 parameters use sampling",
        ],
        "content_format": "prose",
        "format_instructions": "Describe the implemented sampling design, collected data summary, and analysis. Demonstrate that the required confidence/precision level has been met with calculations, and that samples were randomly selected and representative.",
    },
    "E.1": {
        "title": "Calculation of baseline emissions or baseline situation",
        "parent_section": "SECTION E",
        "must_include": [
            "sample calculations for all baseline formulae using actual values",
            "calculations organized under headings for each SDG",
            "clear references to supporting spreadsheets (including sheet names)",
            "baseline emissions or baseline situation for SDG 13 and other relevant SDGs",
        ],
        "examples": [
            "Baseline emissions (SDG 13): BE_y = N_p * B_p,y * EF_b = 15000 * 3.2 * 112 = 5,376,000 kgCO2. Reference: Calculations.xlsx (Baseline Sheet).",
        ],
        "failure_modes": [
            "only final results given without showing calculation steps",
            "formulae shown but actual parameter values not substituted",
            "no reference to supporting spreadsheets",
            "SDG impacts other than SDG 13 not addressed",
        ],
        "content_format": "equations_and_prose",
        "format_instructions": "Present baseline equations with all variables defined, then substitute actual parameter values to show calculation steps. Organize under SDG headings with SDG 13 first. Include references to supporting spreadsheets with sheet names.",
    },
    "E.2": {
        "title": "Calculation of project emissions or project situation",
        "parent_section": "SECTION E",
        "must_include": [
            "sample calculations for all project scenario formulae using actual values",
            "calculations organized under headings for each SDG",
            "clear references to supporting spreadsheets (including sheet names)",
            "project emissions or project situation for SDG 13 and other relevant SDGs",
        ],
        "examples": [
            "Project emissions (SDG 13): PE_y = N_p * P_p,y * EF_p = 15000 * 1.1 * 112 = 1,848,000 kgCO2. Reference: Calculations.xlsx (Project Sheet).",
        ],
        "failure_modes": [
            "only final results given without showing calculation steps",
            "formulae shown but actual parameter values not substituted",
            "no reference to supporting spreadsheets",
            "SDG impacts other than SDG 13 not addressed",
        ],
        "content_format": "equations_and_prose",
        "format_instructions": "Present project scenario equations with all variables defined, then substitute actual parameter values to show calculation steps. Organize under SDG headings with SDG 13 first. Include references to supporting spreadsheets with sheet names.",
    },
    "E.3": {
        "title": "Calculation of leakage",
        "parent_section": "SECTION E",
        "must_include": [
            "sample calculations for all leakage formulae using actual values (SDG 13)",
            "clear references to supporting spreadsheets (including sheet names)",
            "if no leakage applies: explicit statement with justification",
        ],
        "examples": [
            "Leakage (SDG 13): LE_y = 0 (no leakage applicable per methodology AMS-II.G). Reference: Calculations.xlsx (Leakage Sheet).",
        ],
        "failure_modes": [
            "leakage section left blank without stating whether leakage applies",
            "leakage assumed to be zero without justification or methodology reference",
            "formulae shown but actual values not substituted",
            "no reference to supporting spreadsheets",
        ],
        "content_format": "equations_and_prose",
        "format_instructions": "Present leakage equations with all variables defined and substitute actual values. If no leakage applies, provide an explicit statement with methodology justification. Include references to supporting spreadsheets with sheet names.",
    },
    "E.4": {
        "title": "Calculation of net SDG impact",
        "parent_section": "SECTION E",
        "must_include": [
            "summary table with baseline estimate, project estimate, and net benefit for each SDG",
            "SDG 13 listed first, followed by other design-certified SDGs",
            "project estimate accounts for leakage where applicable",
            "net emission reductions or net SDG impact clearly stated",
        ],
        "examples": [
            "SDG 13: Baseline 5,376 tCO2, Project 1,848 tCO2, Net benefit 3,528 tCO2e.",
        ],
        "failure_modes": [
            "summary table missing or incomplete",
            "net benefit not calculated (only baseline and project shown)",
            "leakage not accounted for in the project estimate",
            "SDGs listed but without corresponding impact values",
        ],
        "content_format": "summary_table",
        "format_instructions": "Present a summary table with columns: SDG | Baseline Estimate | Project Estimate (incl. leakage) | Net Benefit. List SDG 13 first, followed by other design-certified SDGs. Include totals row where applicable.",
    },
    "E.5": {
        "title": "Comparison of actual SDG impacts with estimates in approved PDD",
        "parent_section": "SECTION E",
        "must_include": [
            "comparison table of validated ex ante estimates vs actual achieved values for each SDG",
            "comparison covers this specific monitoring period number",
            "where emission reductions are capped, both original and capped values reported",
            "explanation of how ex ante estimates were calculated for this monitoring period",
        ],
        "examples": [
            "SDG 13: Ex ante estimate for MP2 was 3,200 tCO2e; actual achieved was 3,528 tCO2e (3,650 tCO2e uncapped).",
        ],
        "failure_modes": [
            "no comparison table provided",
            "ex ante estimates not specific to this monitoring period",
            "capped vs uncapped values not both reported where applicable",
            "no explanation of how ex ante estimate was derived for this period",
            "anomalous differences between estimated and actual values not explained",
        ],
        "content_format": "table",
        "format_instructions": "Present a comparison table with columns: SDG | Ex Ante Estimate | Actual Achieved | Variance | Explanation. Report both capped and uncapped values where applicable. Ensure estimates are specific to this monitoring period.",
    },
    "E.6": {
        "title": "Remarks on increase in achieved SDG impacts",
        "parent_section": "SECTION E",
        "must_include": [
            "statement on whether actual impacts exceed ex ante estimates",
            "if impacts increased: explanation of cause of increase",
            "description of any differences from assumptions in the Design Certified PDD",
        ],
        "examples": [
            "Actual emission reductions exceeded the ex ante estimate by 10.3% due to higher than expected adoption rates in Year 3.",
            "Actual emission reductions were below the ex ante estimate. No explanation of increase required.",
        ],
        "failure_modes": [
            "section left blank or marked N/A without justification",
            "increase in impacts acknowledged but cause not explained",
            "differences from PDD assumptions not discussed",
        ],
        "content_format": "prose",
        "format_instructions": "State whether actual impacts exceed ex ante estimates. If impacts increased, explain the cause and describe any differences from assumptions in the Design Certified PDD.",
    },
    "F.1": {
        "title": "Safeguards reporting",
        "parent_section": "SECTION F",
        "must_include": [
            "report on safeguarding principles added to the monitoring plan",
            "update on implementation of mitigation measures including successes and failures",
            "monitoring and reporting on key indicators against pre-set tolerances",
            "information on any assessment questions answered 'Potentially' or requiring re-assessment",
        ],
        "examples": [
            "Gender safeguard: Women's participation rate monitored at 62%, exceeding the 50% tolerance threshold. No corrective action required.",
            "Environmental safeguard: Indoor air quality monitored via PM2.5 sampling; all readings within tolerance.",
        ],
        "failure_modes": [
            "no reference to safeguarding principles from the monitoring plan",
            "mitigation measures listed without reporting on their effectiveness",
            "key indicators not reported against pre-set tolerances",
            "assessment questions requiring re-assessment not addressed",
            "section left blank or marked N/A when safeguards were part of the monitoring plan",
        ],
        "content_format": "checklist",
        "format_instructions": "Present as a structured checklist of safeguarding principles from the monitoring plan. For each principle, report: Safeguard | Indicator | Monitored Value | Tolerance Threshold | Status (Met/Not Met) | Corrective Action. Include updates on mitigation measure effectiveness and any assessment questions requiring re-assessment.",
    },
    "G.1": {
        "title": "Inputs and grievances received",
        "parent_section": "SECTION G",
        "must_include": [
            "list of all inputs, disputes, and comments received via the Continuous Input and Grievance Mechanism (CIGM)",
            "response or mitigation action taken for each grievance",
            "status of any items not yet fully addressed with follow-up actions",
        ],
        "examples": [
            "Grievance received 15/03/2023 from Village Elder re: smoke complaints. Response: Additional training provided on cookstove operation. Status: Resolved.",
            "No grievances or inputs were received via the CIGM during this monitoring period.",
        ],
        "failure_modes": [
            "section left blank without stating whether grievances were received",
            "grievances listed without responses or mitigation actions",
            "unresolved items not flagged with follow-up actions",
            "CIGM not referenced by name",
        ],
        "content_format": "table",
        "format_instructions": "Present grievances in a table with columns: Date | Source | Description | Response/Mitigation Action | Status. If no grievances were received, provide an explicit statement referencing the CIGM by name.",
    },
    "G.2": {
        "title": "Stakeholder mitigations monitoring",
        "parent_section": "SECTION G",
        "must_include": [
            "update on mitigations proposed to stakeholders that were agreed to be monitored",
            "current status of each agreed mitigation measure",
        ],
        "examples": [
            "Agreed mitigation: Provide replacement stoves for units failing within 12 months. Status: 42 replacements provided in this period, all within agreed timeframe.",
        ],
        "failure_modes": [
            "no update provided on agreed mitigations",
            "mitigations listed without current status",
            "section left blank when mitigations were agreed during stakeholder consultation",
        ],
        "content_format": "prose",
        "format_instructions": "Provide an update on each agreed stakeholder mitigation measure, including its current status and any actions taken during this monitoring period.",
    },
    "G.3": {
        "title": "Legal contests during the monitoring period",
        "parent_section": "SECTION G",
        "must_include": [
            "details of any legal challenges claiming the project is not in compliance with regulations",
            "if no legal contests: explicit statement that no legal challenges have arisen",
            "confirmation of compliance with host country legal, environmental, ecological, and social regulations",
        ],
        "examples": [
            "No legal contests have arisen during this monitoring period. The project remains in compliance with all applicable host country regulations.",
        ],
        "failure_modes": [
            "section left blank without stating whether legal contests occurred",
            "legal challenge disclosed but outcome or status not reported",
            "no statement on compliance with host country regulations",
            "failure to transparently declare events may result in decertification",
        ],
        "content_format": "prose",
        "format_instructions": "State whether any legal challenges have arisen during this monitoring period. If none, provide an explicit statement. Confirm compliance with host country legal, environmental, ecological, and social regulations.",
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
