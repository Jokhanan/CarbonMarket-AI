"""
gs_pdd_v1_5.py — Gold Standard Project Design Document guide
(Pre-Review v1.5).

Full coverage: Sections A–E.
"""

GUIDE_ID = "GoldStandard_PDD_v1_5"

SUBSECTIONS: dict[str, dict] = {
    "A.1": {
        "title": "Purpose and general description",
        "parent_section": "SECTION A",
        "must_include": [
            "purpose and general description of the project activity",
            "summary of the location of the project activity",
            "technologies or measures to be employed or implemented",
            "summary of the project boundary",
            "summary of the baseline scenario",
        ],
        "examples": [
            "The project distributes improved cookstoves in rural Kenya, displacing traditional three-stone fires and reducing firewood consumption and associated CO2 emissions.",
        ],
        "failure_modes": [
            "description is too vague or generic without specifying the actual activity",
            "no summary of location, technology, boundary, or baseline provided",
            "copy-pasted boilerplate text that does not describe the specific project",
        ],
        "content_format": "prose",
        "format_instructions": "Write a concise narrative overview covering the project purpose, location, technology, boundary, and baseline scenario. Use sub-headings or a structured paragraph for each topic.",
    },
    "A.1.1": {
        "title": "Eligibility under Gold Standard",
        "parent_section": "SECTION A",
        "must_include": [
            "demonstration that the project meets eligibility criteria per GS4GG Principles & Requirements section 3.1.1",
            "evidence the project is pre-identified as eligible or has Gold Standard approval",
            "demonstration the project meets General Eligibility criteria of applicable Activity Requirements",
            "confirmation the project is not registered with any other voluntary or compliance scheme",
            "demonstration the activity is not located in a jurisdiction with an emission reduction cap that includes the project scope",
            "demonstration of no potential for double counting of impacts",
            "demonstration of compliance with host country legal, environmental, ecological and social regulations",
        ],
        "examples": [
            "The project is eligible under GS4GG as it falls under Community Service Activity Requirements for distributed cookstove technologies. It is not registered under any other carbon standard.",
        ],
        "failure_modes": [
            "eligibility criteria not addressed point by point",
            "no confirmation that the project is not registered elsewhere",
            "double counting risk not discussed",
            "host country regulatory compliance not demonstrated",
        ],
        "content_format": "prose",
        "format_instructions": "Address each eligibility criterion point by point in narrative form, citing the relevant GS4GG Principles & Requirements sections.",
    },
    "A.1.2": {
        "title": "Legal ownership of products",
        "parent_section": "SECTION A",
        "must_include": [
            "justification that project owner has full and uncontested legal ownership of all Products generated under Gold Standard Certification",
            "demonstration of legal rights concerning changes in use of resources required to service the project",
            "demonstration of full and uncontested legal land title or tenure where applicable",
        ],
        "examples": [
            "The project developer holds full legal ownership of all VERs generated. Ownership transfer from beneficiaries is documented via signed agreements discussed during local stakeholder consultations.",
        ],
        "failure_modes": [
            "no evidence of legal ownership of products",
            "ownership transfer from beneficiaries not demonstrated transparently",
            "land tenure or resource rights not addressed for applicable project types",
        ],
        "content_format": "prose",
        "format_instructions": "Write a narrative describing legal ownership of products, referencing supporting agreements and documentation.",
    },
    "A.2": {
        "title": "Location of project",
        "parent_section": "SECTION A",
        "must_include": [
            "host country",
            "region, state or province",
            "physical address including city, town or community",
            "map showing the project location",
            "geographic coordinates where applicable",
        ],
        "examples": [
            "The project is located in Siaya County, Kenya (0.0617 S, 34.2422 E). A map showing the project boundary is included as Figure 1.",
        ],
        "failure_modes": [
            "no geographic coordinates provided",
            "only country-level description without specific location details",
            "map referenced but not included or attached",
        ],
        "content_format": "prose",
        "format_instructions": "Provide the location details in prose. Include a placeholder for the project location map (e.g. '[Insert map of project location here]') and present geographic coordinates in a small table with columns: Site | Latitude | Longitude.",
    },
    "A.3": {
        "title": "Technologies and/or measures",
        "parent_section": "SECTION A",
        "must_include": [
            "description of technologies and measures to be employed or implemented",
            "list of facilities, systems and equipment to be installed or modified",
            "age and average lifespan of equipment based on manufacturer specifications and industry standards",
            "information essential to understand how the project reduces GHG emissions and/or contributes to SDGs",
        ],
        "examples": [
            "The project deploys 20,000 improved biomass cookstoves (Model X, manufacturer lifespan 5 years) to replace traditional three-stone fires, reducing firewood consumption by approximately 50%.",
        ],
        "failure_modes": [
            "technology described at a high level without specifying equipment details",
            "equipment lifespan not provided",
            "no explanation of how the technology reduces emissions or contributes to SDGs",
        ],
        "content_format": "prose",
        "format_instructions": "Describe the technology and measures in narrative form, specifying equipment details, lifespan, and the mechanism by which emissions are reduced.",
    },
    "A.4": {
        "title": "Scale of the project",
        "parent_section": "SECTION A",
        "must_include": [
            "confirmation whether the project is micro scale, small scale or large scale",
            "justification of scale referring to the applied Activity Requirements",
            "for VER/CER projects, reference to CDM rules on project types I, II, III where applicable",
        ],
        "examples": [
            "The project qualifies as small scale under CDM Type I/II scale limits, with annual emission reductions below 60,000 tCO2e.",
        ],
        "failure_modes": [
            "scale not explicitly stated as micro, small, or large",
            "no justification provided for the declared scale",
            "scale limits not referenced against applicable Activity Requirements",
        ],
        "content_format": "prose",
        "format_instructions": "State the project scale classification and provide a brief justification referencing the applicable Activity Requirements and CDM scale limits.",
    },
    "A.5": {
        "title": "Funding sources",
        "parent_section": "SECTION A",
        "must_include": [
            "indication of whether the project activity receives public funding",
            "if public funding is received, sources of the public funding",
            "for projects in OECD DAC ODA recipient countries, a signed ODA Declaration",
        ],
        "examples": [
            "The project does not receive any public funding. All funding is sourced from private investment and carbon credit revenues.",
            "The project receives partial funding from GIZ. A signed ODA Declaration is attached.",
        ],
        "failure_modes": [
            "no statement on whether public funding is received",
            "public funding sources not identified",
            "ODA Declaration missing for projects in ODA recipient countries",
        ],
        "content_format": "prose",
        "format_instructions": "Describe funding sources in narrative form, clearly stating whether public funding is received and referencing any attached ODA Declarations.",
    },
    "B.1": {
        "title": "Reference of approved methodology(ies)",
        "parent_section": "SECTION B",
        "must_include": [
            "exact references including titles and version numbers of selected GHG baseline and monitoring methodologies",
            "any methodologies or methodological tools to which the selected methodologies refer",
            "any selected standardized baselines where applicable",
            "any mandatory GS Guidelines applied",
            "confirmation that the latest version of the methodology was applied at time of first submission",
        ],
        "examples": [
            "Methodology: Technologies and Practices to Displace Decentralized Thermal Energy Consumption, version 3.1. Tool: Tool for the Demonstration and Assessment of Additionality, version 07.0.0.",
        ],
        "failure_modes": [
            "methodology name given without version number",
            "referenced methodological tools not listed",
            "no confirmation that the latest version was applied at first submission",
        ],
        "content_format": "prose",
        "format_instructions": "List each methodology and tool with its exact title and version number. Confirm the version was current at first submission.",
    },
    "B.2": {
        "title": "Applicability of methodology(ies)",
        "parent_section": "SECTION B",
        "must_include": [
            "demonstration that the project meets each applicability condition of the applied methodology",
            "demonstration that the project meets any additional GS criteria mandated on use of UNFCCC methodologies",
        ],
        "examples": [
            "The project meets all applicability conditions of AMS-II.G v09: (1) the project involves energy efficiency improvements in thermal applications, (2) the baseline technology uses non-renewable biomass, (3) the project technology displaces the baseline technology.",
        ],
        "failure_modes": [
            "applicability conditions not addressed individually",
            "blanket statement of compliance without demonstrating each condition",
            "additional GS-specific criteria not addressed",
        ],
        "content_format": "table",
        "format_instructions": "Present a table with one row per applicability condition. Columns: Condition | Met? (Yes/No) | Justification. Address each condition individually.",
    },
    "B.3": {
        "title": "Project boundary",
        "parent_section": "SECTION B",
        "must_include": [
            "physical delineation of the project activity boundary",
            "flow diagram of the project boundary where possible",
            "emission sources and GHGs included in the project boundary for baseline and project scenarios",
            "justification for inclusion or exclusion of each GHG source",
        ],
        "examples": [
            "Baseline scenario: CO2 from combustion of non-renewable biomass (included). Project scenario: CO2 from combustion of renewable biomass (excluded, carbon neutral).",
        ],
        "failure_modes": [
            "project boundary not clearly defined",
            "no table or diagram showing included and excluded emission sources",
            "GHG sources listed without justification for inclusion or exclusion",
        ],
        "content_format": "table",
        "format_instructions": "Fill in the exact template table below with project-specific data. Replace [...] placeholders with actual values. Rename 'Source 1', 'Source 2' etc. to actual emission sources. Add or remove rows as needed. Include a placeholder for a flow diagram (e.g. '[Insert project boundary flow diagram here]').",
        "template_scaffold": (
            "| Source | GHGs | Included? | Justification/Explanation |\n"
            "| --- | --- | --- | --- |\n"
            "| Baseline scenario | Source 1 | CO2 | [...] |\n"
            "| Baseline scenario | Source 1 | CH4 | [...] |\n"
            "| Baseline scenario | Source 1 | N2O | [...] |\n"
            "| Baseline scenario | Source 2 | CO2 | [...] |\n"
            "| Baseline scenario | Source 2 | CH4 | [...] |\n"
            "| Baseline scenario | Source 2 | N2O | [...] |\n"
            "| Project scenario | Source 1 | CO2 | [...] |\n"
            "| Project scenario | Source 1 | CH4 | [...] |\n"
            "| Project scenario | Source 1 | N2O | [...] |\n"
            "| Project scenario | Source 2 | CO2 | [...] |\n"
            "| Project scenario | Source 2 | CH4 | [...] |\n"
            "| Project scenario | Source 2 | N2O | [...] |"
        ),
    },
    "B.4": {
        "title": "Establishment and description of baseline scenario",
        "parent_section": "SECTION B",
        "must_include": [
            "identification and description of the baseline scenario",
            "justification of the baseline scenario selection",
            "description of the most plausible baseline scenario in the absence of the project",
            "key assumptions used to determine the baseline",
        ],
        "examples": [
            "In the absence of the project, households would continue using traditional three-stone fires with non-renewable biomass. This is supported by household survey data and regional energy consumption patterns.",
        ],
        "failure_modes": [
            "baseline scenario not clearly identified",
            "no justification for why the selected scenario is the most plausible",
            "alternative scenarios not considered or discussed",
            "key assumptions not stated",
        ],
        "content_format": "prose",
        "format_instructions": "Describe the baseline scenario in narrative form, explaining the most plausible scenario in the absence of the project and the key assumptions underpinning it.",
    },
    "B.5": {
        "title": "Demonstration of additionality",
        "parent_section": "SECTION B",
        "must_include": [
            "demonstration that the project activity is additional",
            "application of the appropriate additionality test or tool",
            "evidence that the project would not have occurred in the absence of carbon finance",
        ],
        "examples": [
            "Additionality is demonstrated using the Tool for the Demonstration and Assessment of Additionality. The investment analysis shows a negative NPV without carbon revenue.",
        ],
        "failure_modes": [
            "additionality not demonstrated using an approved tool or method",
            "investment analysis missing or incomplete",
            "barrier analysis claims not substantiated with evidence",
        ],
        "content_format": "prose",
        "format_instructions": "Write a narrative demonstrating additionality using the appropriate tool or method. Include investment or barrier analysis results with supporting evidence.",
    },
    "B.5.1": {
        "title": "Prior Consideration",
        "parent_section": "SECTION B",
        "must_include": [
            "evidence that GS certification was considered prior to the project start date",
            "documentation of awareness of carbon finance before decision to proceed",
            "timeline showing when carbon certification was first considered relative to project start",
        ],
        "examples": [
            "The project developer initiated GS registration discussions in January 2020, six months before the project start date of July 2020, as evidenced by email correspondence with Gold Standard.",
        ],
        "failure_modes": [
            "no evidence that carbon certification was considered prior to project start",
            "timeline of prior consideration not clearly documented",
            "first submission date more than one year after project start date",
        ],
        "content_format": "prose",
        "format_instructions": "Provide a narrative with a clear timeline showing when GS certification was first considered relative to the project start date, referencing supporting documentation.",
    },
    "B.5.2": {
        "title": "Ongoing Financial Need",
        "parent_section": "SECTION B",
        "must_include": [
            "demonstration that carbon finance or certification revenue is essential for the project's ongoing financial viability",
            "financial projections showing the role of carbon revenue",
            "description of how carbon revenue is reinvested in the project",
        ],
        "examples": [
            "Without carbon revenue, the project would operate at a net loss of USD 150,000 per year. Carbon revenue covers 40% of operational costs and is reinvested in stove distribution and monitoring.",
        ],
        "failure_modes": [
            "no financial analysis demonstrating ongoing need for carbon revenue",
            "carbon revenue treated as supplementary without justifying necessity",
            "no description of how carbon revenue is allocated",
        ],
        "content_format": "prose",
        "format_instructions": "Provide financial projections in narrative form demonstrating the ongoing need for carbon revenue, including how it is allocated to project activities.",
    },
    "B.6": {
        "title": "Sustainable Development Goals outcomes",
        "parent_section": "SECTION B",
        "must_include": [
            "identification of SDGs targeted by the project",
            "description of how the project contributes to each targeted SDG",
            "SDG 13 (Climate Action) addressed as mandatory",
        ],
        "examples": [
            "The project targets SDG 13 (Climate Action) through emission reductions, SDG 3 (Good Health) through reduced indoor air pollution, and SDG 7 (Affordable Energy) through improved energy access.",
        ],
        "failure_modes": [
            "SDG 13 not addressed",
            "SDG contributions described vaguely without linking to project activities",
            "no clear identification of which SDGs are targeted",
        ],
        "content_format": "summary_table",
        "format_instructions": "Fill in the exact template table below with project-specific data. Replace [...] placeholders with actual values. Add rows for each targeted SDG. SDG 13 (Climate Action) must be the first row. Follow the table with a brief narrative linking each SDG to project activities.",
        "template_scaffold": (
            "| SUSTAINABLE DEVELOPMENT GOALS TARGETED | MOST RELEVANT SDG TARGET | SDG IMPACT | INDICATOR (PROPOSED OR SDG INDICATOR) |\n"
            "| --- | --- | --- | --- |\n"
            "| 13 Climate Action (mandatory) | [...] | [...] | [...] |\n"
            "| [...] | [...] | [...] | [...] |"
        ),
    },
    "B.6.1": {
        "title": "Explanation of methodological choices",
        "parent_section": "SECTION B",
        "must_include": [
            "explanation of methodological choices made for quantifying SDG impacts",
            "justification for selection of specific quantification approaches",
            "description of any deviations from default methodological approaches",
        ],
        "examples": [
            "Emission reductions are quantified using AMS-II.G with project-specific usage survey data rather than default values, as the project operates in a region with unique cooking patterns.",
        ],
        "failure_modes": [
            "no explanation of why specific methodological choices were made",
            "deviations from default approaches not justified",
            "methodological choices inconsistent with the selected methodology",
        ],
        "content_format": "equations_and_prose",
        "format_instructions": "For each targeted SDG, present the quantification equations with all variables defined. Explain methodological choices and justify any deviations from default approaches.",
    },
    "B.6.2": {
        "title": "Data and parameters fixed ex ante",
        "parent_section": "SECTION B",
        "must_include": [
            "compilation of all parameters determined before project start and fixed for the crediting period",
            "value applied for each parameter",
            "source of data for each parameter with traceable references",
            "measurement methods and procedures where applicable",
            "purpose of data (baseline, project, or leakage calculation)",
        ],
        "examples": [
            "Parameter: EF_CO2 (CO2 emission factor for biomass). Value: 112 gCO2/MJ. Source: IPCC 2006 Guidelines, Table 2.5. Purpose: Baseline emission calculation.",
        ],
        "failure_modes": [
            "parameter values listed without sources",
            "sources referenced but not traceable",
            "purpose of data not specified for each parameter",
            "IPCC or methodology defaults used without citing the specific table or version",
        ],
        "content_format": "parameter_blocks",
        "format_instructions": "Present each parameter using the exact template block below. Repeat this block for each parameter. Replace [...] placeholders with actual values.",
        "template_scaffold": (
            "| Data/parameter | [...] |\n"
            "| --- | --- |\n"
            "| Unit | [...] |\n"
            "| Description | [...] |\n"
            "| Source of data | [...] |\n"
            "| Value(s) applied | [...] |\n"
            "| Choice of data or Measurement methods and procedures | [...] |\n"
            "| Purpose of data | [...] |\n"
            "| Additional comment | [...] |"
        ),
    },
    "B.6.3": {
        "title": "Ex ante estimation of SDG Impact",
        "parent_section": "SECTION B",
        "must_include": [
            "ex ante calculation of emission reductions or SDG impacts",
            "sample calculations showing formulae with parameter values substituted",
            "calculations organized under headings for each SDG with SDG 13 first",
            "clear references to supporting spreadsheets",
        ],
        "examples": [
            "Ex ante emission reductions (SDG 13): ER_y = BE_y - PE_y - LE_y = 5,376 - 1,848 - 0 = 3,528 tCO2e/year. Reference: Calculations.xlsx (Ex Ante Sheet).",
        ],
        "failure_modes": [
            "only final results given without showing calculation steps",
            "formulae shown but actual parameter values not substituted",
            "no reference to supporting spreadsheets",
            "SDG impacts other than SDG 13 not addressed",
        ],
        "content_format": "equations_and_prose",
        "format_instructions": "Present sample calculations for each SDG (SDG 13 first). Show the formula, substitute actual parameter values, and compute the result. Reference supporting spreadsheets.",
    },
    "B.6.4": {
        "title": "Summary of ex ante estimates",
        "parent_section": "SECTION B",
        "must_include": [
            "summary table with ex ante estimates for each SDG",
            "total estimated emission reductions or removals for each crediting period year",
            "units clearly stated for each SDG impact",
        ],
        "examples": [
            "SDG 13: Estimated annual emission reductions of 3,528 tCO2e. SDG 3: Estimated 650 aDALYs avoided per year.",
        ],
        "failure_modes": [
            "summary table missing or incomplete",
            "estimates not broken down by crediting period year",
            "units not specified for each SDG impact",
        ],
        "content_format": "summary_table",
        "format_instructions": "Fill in the exact template table below with project-specific data. Repeat this table for each targeted SDG. Replace [...] placeholders with actual values. Add or remove year rows to match the crediting period length.",
        "template_scaffold": (
            "| YEAR | BASELINE ESTIMATE | PROJECT ESTIMATE | NET BENEFIT |\n"
            "| --- | --- | --- | --- |\n"
            "| Year 1 | [...] | [...] | [...] |\n"
            "| Year 2 | [...] | [...] | [...] |\n"
            "| Year 3 | [...] | [...] | [...] |\n"
            "| Year 4 | [...] | [...] | [...] |\n"
            "| Year 5 | [...] | [...] | [...] |\n"
            "| Year n | [...] | [...] | [...] |\n"
            "| Total | [...] | [...] | [...] |\n"
            "| Total number of crediting years | [...] | [...] | [...] |\n"
            "| Annual average over the crediting period | [...] | [...] | [...] |"
        ),
    },
    "B.7": {
        "title": "Monitoring plan",
        "parent_section": "SECTION B",
        "must_include": [
            "description of the monitoring plan including data to be monitored",
            "monitoring frequency and methods for each parameter",
            "description of data management and quality assurance/quality control procedures",
            "roles and responsibilities for monitoring activities",
            "description of monitoring equipment and calibration procedures",
        ],
        "examples": [
            "Usage surveys will be conducted annually using stratified random sampling of 300 households. Data is collected by trained field officers using digital survey tools and cross-checked by the monitoring team lead.",
        ],
        "failure_modes": [
            "monitoring plan does not specify frequency of data collection",
            "QA/QC procedures not described",
            "roles and responsibilities for monitoring not assigned",
            "monitoring equipment and calibration not addressed",
            "monitoring plan inconsistent with the requirements of the applied methodology",
        ],
        "content_format": "parameter_blocks",
        "format_instructions": "Present each monitored parameter using the exact template block below. Repeat this block for each parameter. Replace [...] placeholders with actual values. Include a description of the sampling plan and roles/responsibilities after the parameter blocks.",
        "template_scaffold": (
            "| Data / Parameter | [...] |\n"
            "| --- | --- |\n"
            "| Unit | [...] |\n"
            "| Description | [...] |\n"
            "| Source of data | [...] |\n"
            "| Value(s) applied | [...] |\n"
            "| Measurement methods and procedures | [...] |\n"
            "| Monitoring frequency | [...] |\n"
            "| QA/QC procedures | [...] |\n"
            "| Purpose of data | [...] |\n"
            "| Additional comment | [...] |"
        ),
    },
    "C.1": {
        "title": "Duration of project",
        "parent_section": "SECTION C",
        "must_include": [
            "project start date",
            "expected operational lifetime of the project",
            "justification for the stated project duration",
        ],
        "examples": [
            "Project start date: 01/07/2020. Expected operational lifetime: 28 years, based on the lifespan of the improved cookstove technology and ongoing distribution.",
        ],
        "failure_modes": [
            "project start date not provided in DD/MM/YYYY format",
            "operational lifetime not stated or justified",
            "duration inconsistent with equipment lifespan or project design",
        ],
        "content_format": "prose",
        "format_instructions": "State the project start date and operational lifetime in narrative form, with justification linked to equipment lifespan and project design.",
    },
    "C.2": {
        "title": "Crediting period",
        "parent_section": "SECTION C",
        "must_include": [
            "type of crediting period selected (fixed or renewable)",
            "start date and length of the crediting period",
            "justification for the selected crediting period type",
        ],
        "examples": [
            "A renewable crediting period of 7 years (renewable twice) is selected, starting 01/07/2020. This is consistent with GS4GG requirements for small-scale projects.",
        ],
        "failure_modes": [
            "crediting period type not specified",
            "start date or length of crediting period not stated",
            "crediting period exceeds maximum allowed under GS4GG rules",
        ],
        "content_format": "prose",
        "format_instructions": "State the crediting period type, start date, and length in narrative form with justification referencing GS4GG requirements.",
    },
    "D.1": {
        "title": "Safeguarding Principles that will be monitored",
        "parent_section": "SECTION D",
        "must_include": [
            "identification of safeguarding principles applicable to the project",
            "description of indicators to be monitored for each safeguarding principle",
            "pre-set tolerances or thresholds for key indicators",
            "description of mitigation measures for identified risks",
        ],
        "examples": [
            "Gender safeguard: Women's participation rate will be monitored with a minimum threshold of 50%. Environmental safeguard: Indoor air quality will be monitored via PM2.5 sampling.",
        ],
        "failure_modes": [
            "safeguarding principles not identified",
            "no indicators or tolerances specified for monitoring",
            "mitigation measures not described for identified risks",
            "safeguarding assessment appendix not completed or referenced",
        ],
        "content_format": "checklist",
        "format_instructions": "Fill in the exact template table below. List each safeguarding principle identified as applicable from Appendix 1, with the corresponding mitigation measure added to the monitoring plan. Add rows as needed.",
        "template_scaffold": (
            "| PRINCIPLES | MITIGATION MEASURES ADDED TO THE MONITORING PLAN |\n"
            "| --- | --- |\n"
            "| Principle x.y | [...] |\n"
            "| [...] | [...] |"
        ),
    },
    "D.2": {
        "title": "Gender sensitive assessment",
        "parent_section": "SECTION D",
        "must_include": [
            "gender-sensitive assessment of the project's impacts",
            "description of how the project addresses gender-related risks and opportunities",
            "gender-disaggregated data collection plan where applicable",
            "measures to ensure equitable participation and benefit sharing",
        ],
        "examples": [
            "The project targets women as primary beneficiaries, as they are responsible for cooking in 95% of surveyed households. Gender-disaggregated monitoring data will track women's participation in training and usage surveys.",
        ],
        "failure_modes": [
            "no gender-sensitive assessment conducted",
            "gender impacts described without supporting data or analysis",
            "no plan for gender-disaggregated data collection",
            "equitable benefit sharing not addressed",
        ],
        "content_format": "table",
        "format_instructions": "Fill in the exact template table below with project-specific responses to each gender question.",
        "template_scaffold": (
            "| Question 1 - Explain how the project reflects the key issues and requirements of Gender Sensitive design and implementation as outlined in the Gender Policy? | [...] |\n"
            "| --- | --- |\n"
            "| Question 2 - Explain how the project aligns with existing country policies, strategies and best practices | [...] |\n"
            "| Question 3 - Is an Expert required for the Gender Safeguarding Principles & Requirements? | [...] |\n"
            "| Question 4 - Is an Expert required to assist with Gender issues at the Stakeholder Consultation? | [...] |"
        ),
    },
    "E.1": {
        "title": "Summary of stakeholder mitigation measures",
        "parent_section": "SECTION E",
        "must_include": [
            "summary of mitigation measures proposed based on stakeholder consultation",
            "description of how stakeholder feedback was incorporated into project design",
            "status of agreed mitigation measures",
        ],
        "examples": [
            "Stakeholders raised concerns about smoke from cookstove startup. Mitigation: Additional user training on proper lighting technique was incorporated into the distribution protocol.",
        ],
        "failure_modes": [
            "no summary of stakeholder mitigation measures",
            "stakeholder concerns listed without corresponding mitigation actions",
            "no indication of how feedback was incorporated into project design",
        ],
        "content_format": "prose",
        "format_instructions": "Summarize stakeholder mitigation measures in narrative form, describing the concerns raised, mitigation actions taken, and their current status.",
    },
    "E.2": {
        "title": "Final continuous input / grievance mechanism",
        "parent_section": "SECTION E",
        "must_include": [
            "description of the Continuous Input and Grievance Mechanism (CIGM) established for the project",
            "how stakeholders can submit inputs or grievances",
            "process for addressing and resolving grievances",
            "contact information for the grievance mechanism",
        ],
        "examples": [
            "A toll-free hotline and community notice boards have been established for stakeholders to submit grievances. All grievances are logged, reviewed within 14 days, and resolved within 30 days.",
        ],
        "failure_modes": [
            "no CIGM described",
            "grievance process described without contact information or submission methods",
            "no timeline for addressing and resolving grievances",
            "CIGM not accessible to all relevant stakeholders",
        ],
        "content_format": "table",
        "format_instructions": "Fill in the exact template table below with project-specific grievance mechanism details. Replace [...] placeholders with actual values.",
        "template_scaffold": (
            "| METHOD | INCLUDE ALL DETAILS OF CHOSEN METHOD(S) SO THAT THEY MAY BE UNDERSTOOD AND, WHERE RELEVANT, USED BY READERS |\n"
            "| --- | --- |\n"
            "| Continuous Input / Grievance Expression Process Book (mandatory) | [...] |\n"
            "| GS Contact (mandatory) | help@goldstandard.org |\n"
            "| Other | [...] |"
        ),
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
