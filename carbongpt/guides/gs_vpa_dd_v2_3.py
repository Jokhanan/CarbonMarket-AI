"""
gs_vpa_dd_v2_3.py — Gold Standard VPA Design Document guide (v2.3).

Full coverage: Sections A–F.
"""

GUIDE_ID = "GoldStandard_VPA_DD_v2_3"

SUBSECTIONS: dict[str, dict] = {
    "A.1": {
        "title": "Purpose and general description",
        "parent_section": "SECTION A",
        "must_include": [
            "purpose and general description of the VPA",
            "physical/geographical location of the VPA",
            "technologies/measures to be employed and/or implemented",
            "project boundary summary",
            "baseline scenario summary",
            "for Forestry/AGR VPAs: environmental conditions, rare/endangered species, species selected, legal title to land",
        ],
        "examples": [
            "The VPA distributes improved cookstoves to 5,000 households in Siaya County, Kenya, displacing non-renewable biomass and reducing CO2 emissions.",
        ],
        "failure_modes": [
            "description is too vague without specifying the actual VPA activity",
            "no mention of the technology or measure employed",
            "project boundary and baseline scenario not summarised",
            "Forestry/AGR VPAs missing environmental conditions or species information",
        ],
        "content_format": "prose",
        "format_instructions": "Write a structured narrative covering the VPA purpose, location, technology, project boundary summary, and baseline scenario summary. Use sub-headings where appropriate. For Forestry/AGR VPAs, include a dedicated paragraph on environmental conditions and species.",
    },
    "A.1.1": {
        "title": "Eligibility of the VPA under approved PoA",
        "parent_section": "SECTION A",
        "must_include": [
            "eligibility criteria replicated from the Design Certified PoA-DD",
            "description/required condition for each criterion",
            "description of how the VPA meets each criterion with supporting evidence",
            "compliance with general eligibility criteria from GS4GG Principles & Requirements",
            "compliance with eligibility criteria of applicable Activity Requirements",
        ],
        "examples": [
            "Criterion 1: VPA must use the same methodology as PoA. This VPA applies AMS-II.G v09 as specified in the PoA-DD. Evidence: methodology reference in Section B.1.",
        ],
        "failure_modes": [
            "eligibility criteria table not completed",
            "criteria copied from PoA-DD but no description of how VPA meets them",
            "no supporting evidence or means of verification provided",
            "general GS4GG eligibility criteria not addressed",
        ],
        "content_format": "table",
        "format_instructions": "Present as a table with columns: Criterion | Description/Required Condition | How the VPA Meets the Criterion | Supporting Evidence. Include one row per eligibility criterion from the PoA-DD, plus rows for general GS4GG eligibility criteria and applicable Activity Requirements.",
    },
    "A.1.2": {
        "title": "Legal ownership of products",
        "parent_section": "SECTION A",
        "must_include": [
            "justification that project owner has full and uncontested legal ownership of all products",
            "demonstration of legal right to alter use of resources required to service the project",
            "where ownership is transferred from beneficiaries, transparent demonstration of transfer",
            "evidence of contractual arrangements or legal documentation supporting ownership",
        ],
        "examples": [
            "The project developer holds full legal ownership of VERs generated under Gold Standard certification, as evidenced by signed contracts with household beneficiaries (Annex 3).",
        ],
        "failure_modes": [
            "no statement on legal ownership of products",
            "ownership claimed without supporting documentation",
            "transfer of ownership from beneficiaries not transparently demonstrated",
            "legal right to alter resource use not addressed",
        ],
        "content_format": "prose",
        "format_instructions": "Write a narrative demonstrating legal ownership of all products, including references to contractual arrangements and legal documentation. Where ownership is transferred from beneficiaries, describe the transfer process transparently.",
    },
    "A.2": {
        "title": "Location of VPA",
        "parent_section": "SECTION A",
        "must_include": [
            "host country",
            "region or province",
            "physical address or GPS coordinates of VPA site(s)",
            "map or reference to a map showing the VPA boundary",
            "map must include project name, ID, legend, scale, north direction, GPS coordinate system, and infrastructure",
        ],
        "examples": [
            "The VPA is located in Kisumu County, Kenya (0.0917° S, 34.7680° E). See Annex 1 for detailed map with GPS grid (WGS 84).",
        ],
        "failure_modes": [
            "no geographic coordinates provided",
            "only country-level description without specific location",
            "map referenced but not included or attached",
            "map missing required elements (legend, scale, GPS grid, etc.)",
        ],
        "content_format": "prose",
        "format_instructions": "Provide the host country, region/province, and GPS coordinates. Include a placeholder for the map (e.g. '[Insert map here]') with a note that the map must include project name, ID, legend, scale, north direction, GPS coordinate system, and infrastructure.",
    },
    "A.3": {
        "title": "Technologies and/or measures",
        "parent_section": "SECTION A",
        "must_include": [
            "description of the technology or measure employed by the VPA",
            "how the technology/measure achieves emission reductions or other SDG impacts",
            "technical specifications of equipment or processes",
            "consistency with the technology/measure described in the PoA-DD",
        ],
        "examples": [
            "The VPA deploys fuel-efficient cookstoves (Brand X, thermal efficiency 45%) to replace traditional three-stone fires, reducing firewood consumption by approximately 60%.",
        ],
        "failure_modes": [
            "technology described generically without technical specifications",
            "no explanation of how emissions are reduced",
            "inconsistency with technology described in the PoA-DD",
            "multiple technologies listed without clear distinction",
        ],
        "content_format": "prose",
        "format_instructions": "Describe the technology or measure employed, including technical specifications (e.g. efficiency, capacity). Explain how it achieves emission reductions or SDG impacts and confirm consistency with the PoA-DD.",
    },
    "A.4": {
        "title": "Scale of the VPA",
        "parent_section": "SECTION A",
        "must_include": [
            "classification as microscale, small-scale, or large-scale",
            "justification for the selected scale based on applicable Activity Requirements",
            "confirmation that VPA scale complies with scale requirements defined at the real case VPA level",
        ],
        "examples": [
            "This is a small-scale VPA as defined under the Community Services Activities requirements, with annual emission reductions below 60,000 tCO2e.",
        ],
        "failure_modes": [
            "scale not explicitly stated",
            "no justification for scale classification",
            "scale inconsistent with real case VPA requirements",
            "threshold values for scale classification not referenced",
        ],
        "content_format": "prose",
        "format_instructions": "State the scale classification (microscale, small-scale, or large-scale) and provide justification based on applicable Activity Requirements and thresholds.",
    },
    "A.5": {
        "title": "Funding sources of VPA",
        "parent_section": "SECTION A",
        "must_include": [
            "description of all funding sources for the VPA",
            "indication of whether public or private funding is involved",
            "statement on whether ODA (Official Development Assistance) is used",
            "if ODA is involved, confirmation that it does not result in diversion of ODA",
        ],
        "examples": [
            "The VPA is funded through private investment by CleanCook Ltd and revenue from the sale of Gold Standard VERs. No public or ODA funding is involved.",
        ],
        "failure_modes": [
            "funding sources not disclosed",
            "no statement on whether ODA is involved",
            "public funding involved but not transparently declared",
            "section left blank or marked N/A without justification",
        ],
        "content_format": "prose",
        "format_instructions": "Describe all funding sources, indicate whether public or private, and state whether ODA is involved. If ODA is used, confirm it does not result in diversion of ODA.",
    },
    "B.1": {
        "title": "Reference of approved methodology(ies)",
        "parent_section": "SECTION B",
        "must_include": [
            "full name of the methodology applied",
            "version number of the methodology",
            "any applicable methodological tools or combined methodologies",
            "confirmation that the methodology is Gold Standard approved",
        ],
        "examples": [
            "AMS-II.G: Energy efficiency measures in thermal applications of non-renewable biomass, version 09. Gold Standard approved.",
        ],
        "failure_modes": [
            "methodology name given without version number",
            "wrong methodology referenced for the VPA type",
            "methodological tools used but not listed",
            "methodology not confirmed as Gold Standard approved",
        ],
        "content_format": "prose",
        "format_instructions": "State the full methodology name, version number, and any applicable methodological tools. Confirm Gold Standard approval status.",
    },
    "B.2": {
        "title": "Applicability of methodology(ies)",
        "parent_section": "SECTION B",
        "must_include": [
            "demonstration that all applicability conditions of the methodology are met",
            "point-by-point assessment of each applicability criterion",
            "evidence or justification for each criterion",
            "consistency with the applicability demonstration in the PoA-DD/real case VPA",
        ],
        "examples": [
            "Applicability condition 1: The project involves energy efficiency improvements in thermal applications. Met: The VPA distributes improved cookstoves replacing traditional biomass cooking devices.",
        ],
        "failure_modes": [
            "applicability conditions listed but not individually addressed",
            "no evidence provided for meeting each criterion",
            "applicability demonstration inconsistent with PoA-DD",
            "section contains generic statements without specific justification",
        ],
        "content_format": "table",
        "format_instructions": "Present as a table with columns: Applicability Condition | Met? (Yes/No) | Justification/Evidence. Include one row per applicability condition from the methodology. Ensure consistency with the PoA-DD demonstration.",
    },
    "B.3": {
        "title": "VPA boundary",
        "parent_section": "SECTION B",
        "must_include": [
            "definition of the VPA boundary including all emission sources, sinks, and reservoirs",
            "identification of gases included (CO2, CH4, N2O, etc.)",
            "baseline scenario emissions within the boundary",
            "project scenario emissions within the boundary",
            "any exclusions from the boundary with justification",
        ],
        "examples": [
            "The VPA boundary includes CO2 emissions from combustion of non-renewable biomass for cooking in households within Kisumu County. CH4 emissions from incomplete combustion are excluded as per methodology AMS-II.G.",
        ],
        "failure_modes": [
            "boundary not clearly defined",
            "gases included/excluded not specified",
            "sources, sinks, and reservoirs not identified",
            "exclusions from boundary not justified",
            "boundary inconsistent with methodology requirements",
        ],
        "content_format": "table",
        "format_instructions": "Fill in the exact template table below with project-specific data. Replace [...] placeholders with actual values. Rename 'Source 1', 'Source 2' to actual emission sources. Add or remove rows as needed. Include a placeholder for a flow diagram (e.g. '[Insert boundary flow diagram here]').",
        "template_scaffold": (
            "| Source | GHGs | Included? | Justification/Explanation |\n"
            "| --- | --- | --- | --- |\n"
            "| Baseline scenario | Source 1 | CO2 | [...] |\n"
            "| Baseline scenario | Source 1 | CH4 | [...] |\n"
            "| Baseline scenario | Source 1 | N2O | [...] |\n"
            "| Project scenario | Source 1 | CO2 | [...] |\n"
            "| Project scenario | Source 1 | CH4 | [...] |\n"
            "| Project scenario | Source 1 | N2O | [...] |"
        ),
    },
    "B.4": {
        "title": "Establishment and description of baseline scenario",
        "parent_section": "SECTION B",
        "must_include": [
            "description of the baseline scenario",
            "identification and justification of the most plausible baseline scenario",
            "explanation of what would occur in the absence of the VPA",
            "key assumptions underlying the baseline scenario",
            "consistency with the baseline scenario in the PoA-DD/real case VPA",
        ],
        "examples": [
            "In the absence of the VPA, households would continue using traditional three-stone fires with non-renewable firewood, resulting in continued CO2 and particulate emissions.",
        ],
        "failure_modes": [
            "baseline scenario not described or described only generically",
            "no justification for why the baseline is the most plausible scenario",
            "key assumptions not stated",
            "baseline scenario inconsistent with PoA-DD",
            "alternative scenarios not considered",
        ],
        "content_format": "prose",
        "format_instructions": "Describe the baseline scenario, justify why it is the most plausible, explain what would occur without the VPA, and state key assumptions. Confirm consistency with the PoA-DD.",
    },
    "B.5": {
        "title": "Demonstration of additionality",
        "parent_section": "SECTION B",
        "must_include": [
            "demonstration that the VPA would not have occurred without carbon finance",
            "application of the applicable additionality tool or approach",
            "barrier analysis and/or investment analysis as required",
            "common practice analysis where applicable",
        ],
        "examples": [
            "Additionality is demonstrated using the CDM Tool for the demonstration and assessment of additionality. The VPA faces investment and technological barriers that would prevent implementation without carbon finance revenue.",
        ],
        "failure_modes": [
            "no additionality demonstration provided",
            "additionality tool or approach not referenced",
            "barrier analysis lacking specific evidence",
            "common practice analysis missing when required",
            "additionality argument inconsistent with PoA-level demonstration",
        ],
        "content_format": "prose",
        "format_instructions": "Write a narrative demonstrating additionality using the applicable tool or approach. Include barrier analysis and/or investment analysis as required, and common practice analysis where applicable.",
    },
    "B.5.1": {
        "title": "Prior Consideration",
        "parent_section": "SECTION B",
        "must_include": [
            "evidence that carbon finance was considered prior to project implementation",
            "documentation of awareness of carbon markets before the VPA start date",
            "timeline demonstrating prior consideration",
        ],
        "examples": [
            "The project developer initiated discussions with Gold Standard in March 2021, prior to the VPA start date of September 2021, as evidenced by email correspondence (Annex 5).",
        ],
        "failure_modes": [
            "no evidence of prior consideration provided",
            "timeline shows carbon finance considered after project start",
            "supporting documentation not referenced or attached",
        ],
        "content_format": "prose",
        "format_instructions": "Provide evidence of prior consideration of carbon finance with a clear timeline, referencing supporting documentation such as correspondence or meeting minutes.",
    },
    "B.5.2": {
        "title": "Ongoing Financial Need",
        "parent_section": "SECTION B",
        "must_include": [
            "demonstration of ongoing financial need for carbon finance revenue",
            "financial analysis showing the VPA is not financially viable without carbon credits",
            "evidence that carbon revenue is essential for continued operation",
        ],
        "examples": [
            "Without carbon finance revenue, the VPA would generate a negative IRR of -3.2%. Carbon credit sales contribute 35% of total project revenue, making them essential for ongoing viability.",
        ],
        "failure_modes": [
            "no financial analysis demonstrating ongoing need",
            "carbon finance shown as supplementary rather than essential",
            "financial projections not supported by evidence",
            "section left blank or marked N/A",
        ],
        "content_format": "prose",
        "format_instructions": "Present a financial analysis demonstrating that the VPA is not viable without carbon credit revenue. Include key financial metrics (e.g. IRR, NPV) and show the contribution of carbon revenue to total project revenue.",
    },
    "B.6": {
        "title": "Sustainable Development Goals outcomes",
        "parent_section": "SECTION B",
        "must_include": [
            "minimum three SDGs addressed by the VPA",
            "relevant SDG targets for each SDG",
            "SDG indicators or proposed indicators for each SDG",
            "SDG 13 (Climate Action) as mandatory with VERs/CERs",
            "estimated annual average SDG impacts",
        ],
        "examples": [
            "SDG 13: Emissions Reductions — 15,000 VERs annually. SDG 3: Health — 650 aDALYs annually. SDG 7: Energy — 11,000 MWh renewable energy generated annually.",
        ],
        "failure_modes": [
            "fewer than three SDGs identified",
            "SDG 13 not included",
            "SDG targets not specified",
            "indicators not defined or not justified",
            "estimated values not provided in summary table",
        ],
        "content_format": "summary_table",
        "format_instructions": "Fill in the exact template table below with project-specific data. Replace [...] placeholders with actual values. Add rows for each targeted SDG. SDG 13 (Climate Action) must be the first row.",
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
            "explanation of methodological steps for calculating baseline and project outcomes under each SDG",
            "equations to be used for calculating net benefit clearly stated",
            "SDG 13 impact based on the selected SDG indicator",
            "consistency with the corresponding validated VPA methodology",
        ],
        "examples": [
            "SDG 13: Net emission reductions calculated as ER_y = BE_y - PE_y - LE_y per AMS-II.G equations 1-3. Baseline situation uses the 'amount of emission reduction' indicator.",
        ],
        "failure_modes": [
            "methodological choices not explained per SDG",
            "equations not stated or referenced",
            "SDG 13 impact not aligned with selected indicator",
            "approach inconsistent with validated VPA methodology",
        ],
        "content_format": "equations_and_prose",
        "format_instructions": "For each SDG, explain the methodological steps and present the equations used to calculate baseline and project outcomes. Define all variables and state the net benefit equation (e.g. ER_y = BE_y - PE_y - LE_y). Present SDG 13 first.",
    },
    "B.6.2": {
        "title": "Data and parameters fixed ex ante",
        "parent_section": "SECTION B",
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
        "format_instructions": "Present each parameter using the exact template block below. Repeat this block for each parameter. Replace [...] placeholders with actual values. Organize under SDG headings with SDG 13 first.",
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
            "transparent ex ante calculation of baseline and project scenarios",
            "application of all relevant equations from the selected methodology",
            "use of fixed ex ante values from section B.6.2 and monitored parameter estimates from B.7.1",
            "calculations shown step by step so a reader can reproduce them",
        ],
        "examples": [
            "Baseline emissions (SDG 13): BE_y = N_p * B_p,y * EF_b = 5000 * 3.2 * 112 = 1,792,000 kgCO2. Reference: Calculations.xlsx (Baseline Sheet).",
        ],
        "failure_modes": [
            "only final results given without showing calculation steps",
            "formulae shown but actual parameter values not substituted",
            "no reference to supporting spreadsheets",
            "reader cannot reproduce the calculation from information provided",
        ],
        "content_format": "equations_and_prose",
        "format_instructions": "For each SDG, show the ex ante calculation step by step: state the equation, substitute the parameter values from B.6.2, and compute the result. Include references to supporting spreadsheets. Ensure a reader can reproduce every calculation.",
    },
    "B.6.4": {
        "title": "Summary of ex ante estimates",
        "parent_section": "SECTION B",
        "must_include": [
            "summary table with baseline estimate, project estimate, and net benefit per year",
            "total over the crediting period",
            "annual average over the crediting period",
            "total number of crediting years",
        ],
        "examples": [
            "Year 1: Baseline 5,376 tCO2, Project 1,848 tCO2, Net benefit 3,528 tCO2e. Total over 5 years: 17,640 tCO2e. Annual average: 3,528 tCO2e.",
        ],
        "failure_modes": [
            "summary table missing or incomplete",
            "net benefit not calculated",
            "total and annual average not provided",
            "values inconsistent with calculations in B.6.3",
        ],
        "content_format": "summary_table",
        "format_instructions": "Fill in the exact template table below with project-specific data. Replace [...] placeholders with actual values. Repeat this table for each targeted SDG.",
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
            "data and parameters to be monitored (B.7.1) with tables per SDG (SDG 13 first)",
            "source of data, measurement methods, monitoring frequency, QA/QC procedures for each parameter",
            "sampling plan (B.7.2) if sampling approach is used, referencing the CDM sampling standard",
            "other elements of monitoring plan (B.7.3): operational/management structure, data archiving, responsibilities",
        ],
        "examples": [
            "Parameter: Up,y (usage rate). Unit: fraction. Monitoring frequency: annual. QA/QC: Cross-checked against field records. Sampling plan: Stratified random sample of 300 households per CDM sampling standard.",
        ],
        "failure_modes": [
            "monitored parameters missing QA/QC procedures",
            "monitoring frequency not specified",
            "sampling plan not described when sampling is used",
            "operational and management structure for monitoring not described",
            "data archiving provisions not included",
            "parameters duplicated across SDG headings instead of cross-referenced",
        ],
        "content_format": "parameter_blocks",
        "format_instructions": "Present each monitored parameter using the exact template block below. Repeat for each parameter. Organize under SDG headings with SDG 13 first. Include sub-sections for sampling plan (B.7.2) and operational structure (B.7.3).",
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
            "start date of the VPA in DD/MM/YYYY format",
            "definition of start date per GS4GG Principle 4",
            "evidence proving the start date",
            "justification of whether the project is regular or retroactive",
            "expected operational lifetime in years and months",
        ],
        "examples": [
            "VPA start date: 01/09/2021, defined as the date of first expenditure commitment. Expected operational lifetime: 10 years, 0 months. Evidence: signed purchase order (Annex 6).",
        ],
        "failure_modes": [
            "start date not in DD/MM/YYYY format",
            "no evidence provided for the start date",
            "regular vs retroactive status not justified",
            "expected operational lifetime not stated",
            "start date definition not referenced to GS4GG Principle 4",
        ],
        "content_format": "prose",
        "format_instructions": "State the VPA start date in DD/MM/YYYY format, define it per GS4GG Principle 4, provide evidence, justify regular vs retroactive status, and state the expected operational lifetime in years and months.",
    },
    "C.2": {
        "title": "Crediting period",
        "parent_section": "SECTION C",
        "must_include": [
            "start date of crediting period in DD/MM/YYYY format",
            "justification of crediting period start date per applicable rules",
            "total length of crediting period in years and months",
            "confirmation that crediting period does not exceed PoA duration",
            "reference to applicable Activity Requirements for maximum crediting period",
        ],
        "examples": [
            "Crediting period start date: 01/09/2021. Total length: 5 years, 0 months (renewable). The crediting period starts on the VPA start date and does not exceed the PoA end date.",
        ],
        "failure_modes": [
            "crediting period start date not specified",
            "no justification for crediting period start date",
            "total length not stated in years and months",
            "crediting period exceeds PoA duration without justification",
            "maximum crediting period not referenced",
        ],
        "content_format": "prose",
        "format_instructions": "State the crediting period start date in DD/MM/YYYY format, justify it per applicable rules, provide total length in years and months, confirm it does not exceed PoA duration, and reference maximum crediting period from applicable Activity Requirements.",
    },
    "D.1": {
        "title": "Safeguarding Principles",
        "parent_section": "SECTION D",
        "must_include": [
            "summary of safeguarding principles added to the monitoring plan",
            "reference to completed Safeguarding Principles Assessment in Appendix 1",
            "mitigation measures for each relevant principle",
            "indication of which principles require ongoing monitoring",
        ],
        "examples": [
            "Principle 3.1 (Human Rights): No risk identified. Principle 5.2 (Gender): Monitoring of women's participation rate added to monitoring plan with 50% threshold.",
        ],
        "failure_modes": [
            "no reference to Safeguarding Principles Assessment in Appendix 1",
            "mitigation measures not summarised for relevant principles",
            "principles requiring monitoring not identified",
            "section left blank when safeguards were part of the assessment",
        ],
        "content_format": "checklist",
        "format_instructions": "Present as a checklist of safeguarding principles with columns or fields: Principle Number | Principle Description | Risk Identified (Yes/No) | Mitigation Measure | Requires Ongoing Monitoring (Yes/No). Reference the completed Safeguarding Principles Assessment in Appendix 1.",
    },
    "D.2": {
        "title": "Gender sensitive assessment",
        "parent_section": "SECTION D",
        "must_include": [
            "evidence that project design covers the overall societal context from a gender perspective",
            "justification of compliance with local policies on gender or women empowerment",
            "assessment of whether an expert is needed for Gender Safeguarding Principles",
            "assessment of whether an expert is needed for gender issues at Stakeholder Consultation",
        ],
        "examples": [
            "The project design ensures equal access for women and men to cookstove distribution. The project complies with Kenya's National Gender and Equality Commission Act 2011. No gender expert required as gender is adequately addressed in the Safeguarding Principles Assessment.",
        ],
        "failure_modes": [
            "gender perspective not addressed in project design",
            "local gender policies not referenced",
            "expert assessment questions (Q3, Q4) not answered",
            "section left blank or contains only placeholder text",
        ],
        "content_format": "prose",
        "format_instructions": "Write a narrative covering the gender perspective in project design, reference local gender policies, and answer whether an expert is needed for Gender Safeguarding Principles and for gender issues at Stakeholder Consultation.",
    },
    "E.1": {
        "title": "Summary of stakeholder mitigation measures",
        "parent_section": "SECTION E",
        "must_include": [
            "summary of all concerns raised by stakeholders during consultations",
            "mitigation measures proposed for each concern",
            "description of how mitigation measures will be monitored",
            "details of how stakeholder comments are taken into account",
            "justification for any comments not incorporated or addressed",
        ],
        "examples": [
            "Concern: Indoor air quality. Mitigation: PM2.5 monitoring added to monitoring plan. Commitment to stakeholders: Annual reporting of air quality results.",
        ],
        "failure_modes": [
            "stakeholder concerns not listed",
            "mitigation measures not described for raised concerns",
            "no description of how mitigations will be monitored",
            "stakeholder comments not taken into account without justification",
            "section left blank when stakeholder consultation was conducted",
        ],
        "content_format": "prose",
        "format_instructions": "Summarize stakeholder concerns and mitigation measures in a narrative. For each concern raised, describe the mitigation measure proposed and how it will be monitored. Justify any comments not incorporated.",
    },
    "E.2": {
        "title": "Final continuous input / grievance mechanism",
        "parent_section": "SECTION E",
        "must_include": [
            "details of the Continuous Input/Grievance Expression Process Book (mandatory)",
            "Gold Standard contact (help@goldstandard.org) as mandatory method",
            "any other grievance methods agreed with stakeholders",
            "description of each method so it can be understood and used by readers",
        ],
        "examples": [
            "Method 1: Continuous Input/Grievance Expression Process Book available at project office. Method 2: GS Contact help@goldstandard.org. Method 3: Dedicated phone hotline +254-XXX-XXXX.",
        ],
        "failure_modes": [
            "Process Book not listed as mandatory method",
            "GS contact email not included",
            "methods described without sufficient detail for readers to use them",
            "section left blank or marked N/A",
            "methods not agreed with stakeholders during consultation",
        ],
        "content_format": "prose",
        "format_instructions": "List and describe each grievance mechanism method, including the mandatory Continuous Input/Grievance Expression Process Book and Gold Standard contact (help@goldstandard.org). Describe each method in enough detail for readers to understand and use it.",
    },
    "F.1": {
        "title": "Eligibility and inclusion criteria for VPAs",
        "parent_section": "SECTION F",
        "must_include": [
            "eligibility criteria and required conditions from the real case VPA",
            "description of how each criterion is met by this VPA",
            "means of verification and supporting evidence for inclusion",
            "confirmation that eligibility criteria have not been changed from real case VPA",
        ],
        "examples": [
            "Criterion 1: VPA must be located within the PoA geographic boundary (Kenya). Met: This VPA is located in Kisumu County, Kenya. Evidence: GPS coordinates and map in Section A.2.",
        ],
        "failure_modes": [
            "eligibility criteria table not completed",
            "criteria from real case VPA not replicated",
            "no description of how VPA meets each criterion",
            "supporting evidence not provided",
            "eligibility criteria modified from those set at real case VPA level",
        ],
        "content_format": "prose",
        "format_instructions": "Present the eligibility and inclusion criteria from the real case VPA. For each criterion, describe how it is met by this VPA and provide means of verification and supporting evidence. Confirm that criteria have not been changed from the real case VPA.",
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
