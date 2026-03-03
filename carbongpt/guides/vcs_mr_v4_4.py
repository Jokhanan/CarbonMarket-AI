"""
vcs_mr_v4_4.py — Verra VCS Monitoring Report guide (v4.4).

Full coverage: Sections 1–5 (28 subsections).
"""

GUIDE_ID = "Verra_VCS_MR_v4_4"

SUBSECTIONS: dict[str, dict] = {
    "1.1": {
        "title": "Summary Description of the Implementation Status of the Project",
        "parent_section": "Project Details",
        "must_include": [
            "summary of the implementation status of technologies or measures",
            "relevant implementation dates (construction, commissioning, continued operation)",
            "total GHG emission reductions and carbon dioxide removals generated in the monitoring period",
        ],
        "examples": [
            "The project has been operational since 01-Jan-2020. During the monitoring period, 50,000 tCO2e of emission reductions were generated from the improved forest management activity.",
        ],
        "failure_modes": [
            "no mention of implementation status of the project activity",
            "implementation dates not provided",
            "total GHG reductions or removals for the monitoring period not stated",
            "exceeds one page limit",
        ],
        "content_format": "prose",
        "format_instructions": "Write a concise narrative (no more than one page) summarising the implementation status, key dates, and total GHG reductions/removals for the monitoring period.",
    },
    "1.2": {
        "title": "Audit History",
        "parent_section": "Project Details",
        "must_include": [
            "table of audit history including all monitoring periods",
            "audit type (validation or verification)",
            "period covered by each audit",
            "program (VCS)",
            "validation/verification body name",
            "number of years covered",
        ],
        "examples": [
            "Verification | 01-Jan-2022 to 31-Dec-2022 | VCS | SCS Global Services | One year.",
        ],
        "failure_modes": [
            "audit history table missing or incomplete",
            "current monitoring period not included in the table",
            "validation/verification body not named",
            "audit type not specified",
        ],
        "content_format": "table",
        "format_instructions": "Present a table with columns: Audit Type | Period Covered | Program | Validation/Verification Body | Years Covered. Include one row per audit, covering all monitoring periods up to and including the current one.",
    },
    "1.3": {
        "title": "Sectoral Scope and Project Type",
        "parent_section": "Project Details",
        "must_include": [
            "sectoral scope of the project",
            "project activity type",
            "for AFOLU projects: AFOLU project category",
        ],
        "examples": [
            "Sectoral Scope: 14 (AFOLU). AFOLU project category: Improved Forest Management (IFM). Project activity type: Logged to Protected Forest (LtPF).",
        ],
        "failure_modes": [
            "sectoral scope not identified",
            "project activity type not specified",
            "AFOLU category missing for AFOLU projects",
            "non-AFOLU table used for an AFOLU project or vice versa",
        ],
        "content_format": "prose",
        "format_instructions": "State the sectoral scope number and name, the project activity type, and (for AFOLU projects) the AFOLU project category in short declarative sentences.",
    },
    "1.4": {
        "title": "Project Proponent",
        "parent_section": "Project Details",
        "must_include": [
            "organization name of the project proponent",
            "contact person name",
            "title of the contact person",
            "address",
            "telephone number",
            "email address with domain matching the organization",
        ],
        "examples": [
            "Organization: GreenForest Inc. Contact: Jane Doe, Director of Carbon Projects. Address: 123 Forest Lane, Portland, OR 97201. Email: jane.doe@greenforest.com.",
        ],
        "failure_modes": [
            "project proponent contact information incomplete",
            "email domain does not match the organization",
            "no contact person identified",
        ],
        "content_format": "table",
        "format_instructions": "Present the project proponent information in a structured table with rows: Organization | Contact Person | Title | Address | Telephone | Email.",
    },
    "1.5": {
        "title": "Other Entities Involved in the Project",
        "parent_section": "Project Details",
        "must_include": [
            "organization name of each additional entity",
            "role in the project for each entity",
            "contact person, title, address, telephone, and email for each entity",
        ],
        "examples": [
            "Organization: Carbon Advisors LLC. Role: Monitoring and reporting. Contact: John Smith, Senior Analyst.",
        ],
        "failure_modes": [
            "other entities listed without specifying their role",
            "contact information incomplete for listed entities",
            "section left blank without stating no other entities are involved",
        ],
        "content_format": "table",
        "format_instructions": "Present each entity in a table with columns: Organization | Role | Contact Person | Title | Address | Telephone | Email. If no other entities are involved, state this explicitly.",
    },
    "1.6": {
        "title": "Project Start Date",
        "parent_section": "Project Details",
        "must_include": [
            "project start date in DD-Month-YYYY format",
            "justification of how the start date conforms with VCS Program requirements",
        ],
        "examples": [
            "Project start date: 15-March-2018. The start date is the date of initial site preparation activities, conforming with VCS Standard Section 3.2.1.",
        ],
        "failure_modes": [
            "start date not provided or in incorrect format",
            "no justification for how the start date conforms with VCS requirements",
            "start date inconsistent with other project documents",
        ],
        "content_format": "prose",
        "format_instructions": "State the project start date in DD-Month-YYYY format followed by a brief justification of how it conforms with VCS Program requirements.",
    },
    "1.7": {
        "title": "Project Crediting Period",
        "parent_section": "Project Details",
        "must_include": [
            "crediting period type (seven years twice renewable, ten years fixed, or other with justification)",
            "start and end date of the first or fixed crediting period",
        ],
        "examples": [
            "Crediting period: Seven years, twice renewable. Start: 01-Jan-2019. End: 31-Dec-2025.",
        ],
        "failure_modes": [
            "crediting period type not specified",
            "start and end dates of crediting period not provided",
            "non-standard crediting period selected without justification",
        ],
        "content_format": "prose",
        "format_instructions": "State the crediting period type and its start and end dates. If the crediting period is non-standard, include a justification.",
    },
    "1.8": {
        "title": "Project Location",
        "parent_section": "Project Details",
        "must_include": [
            "project location description",
            "geographic boundaries if applicable",
            "set of geodetic coordinates",
            "for AFOLU, GCS, grouped, or multi-instance projects: separate KML file reference",
        ],
        "examples": [
            "The project is located in Madre de Dios, Peru (12.5933 S, 69.1891 W). A KML file delineating the project boundary is provided as a separate attachment.",
        ],
        "failure_modes": [
            "no geodetic coordinates provided",
            "project location described only at country level without specifics",
            "KML file not referenced for AFOLU or grouped projects",
        ],
        "content_format": "prose",
        "format_instructions": "Describe the project location with geodetic coordinates. Reference a KML file attachment for AFOLU, GCS, grouped, or multi-instance projects.",
    },
    "1.9": {
        "title": "Title and Reference of Methodology",
        "parent_section": "Project Details",
        "must_include": [
            "type of each item (methodology, tool, or module)",
            "reference ID if applicable",
            "title of the methodology, tool, or module",
            "version number",
        ],
        "examples": [
            "Methodology | VM0007 | REDD+ Methodology Framework (REDD+MF) | Version 6.0.",
        ],
        "failure_modes": [
            "methodology title given without version number",
            "reference ID missing when applicable",
            "tools or modules used but not listed",
            "type (methodology, tool, module) not distinguished",
        ],
        "content_format": "prose",
        "format_instructions": "List each methodology, tool, or module used with its type, reference ID, title, and version number.",
    },
    "1.10": {
        "title": "Double Counting and Participation under Other GHG Programs",
        "parent_section": "Project Details",
        "must_include": [
            "statement on whether the project is receiving or seeking credit under another GHG program (no double issuance)",
            "if yes: evidence of no double issuance per VCS Standard",
            "statement on whether the project was registered or seeking registration under other GHG programs",
            "if yes: registration number, relevant details, and date of project inactivity in the other program",
        ],
        "examples": [
            "The project is not receiving or seeking credit under any other GHG program. The project has not been registered under any other GHG program.",
        ],
        "failure_modes": [
            "no explicit statement on double issuance",
            "participation under other GHG programs not addressed",
            "yes answer given without providing required evidence or registration details",
        ],
        "content_format": "checklist",
        "format_instructions": "Present as a checklist with Yes/No answers for each question: (1) Is the project receiving or seeking credit under another GHG program? (2) Was the project registered or seeking registration under other GHG programs? Provide supporting evidence or details for any 'Yes' answers.",
    },
    "1.11": {
        "title": "Double Claiming, Other Forms of Credit, and Scope 3 Emissions",
        "parent_section": "Project Details",
        "must_include": [
            "statement on whether reductions/removals are included in an emissions trading program or binding emission limit",
            "statement on whether the project has sought, received, or plans to receive credit from another GHG-related environmental credit system",
            "statement on whether project activities affect the emissions footprint of supply chain products",
            "if applicable: evidence of no double claiming, public statement on website, and supply chain disclosure",
        ],
        "examples": [
            "Project reductions are not included in any emissions trading program. The project has not sought credit from any other GHG-related environmental credit system. Project activities do not affect the emissions footprint of any supply chain product.",
        ],
        "failure_modes": [
            "double claiming questions not addressed",
            "scope 3 emissions impact not discussed",
            "yes answers given without providing required evidence or public statements",
            "supply chain disclosure missing when applicable",
        ],
        "content_format": "checklist",
        "format_instructions": "Present as a checklist with Yes/No answers for each question: (1) Are reductions/removals included in an emissions trading program or binding emission limit? (2) Has the project sought or received credit from another GHG-related environmental credit system? (3) Do project activities affect the emissions footprint of supply chain products? Provide supporting evidence for any 'Yes' answers.",
    },
    "1.12": {
        "title": "Sustainable Development Contributions",
        "parent_section": "Project Details",
        "must_include": [
            "brief description (no more than 100 words) of project activities during the monitoring period resulting in SD contributions",
            "explanation of how activities result in the SD contributions described in Table 1",
            "identification of which SD contributions align with nationally stated sustainable development priorities",
            "Table 1 with SDG target, indicator, net impact, current project contributions, and cumulative lifetime contributions",
            "evidence of SD contributions provided as appendices",
        ],
        "examples": [
            "SDG 13.0 | Tonnes of greenhouse gas emissions avoided or removed | Implemented activities to increase | By conserving 400 ha of tropical rainforest, the project prevented the release of 250,000 tCO2e during the monitoring period.",
        ],
        "failure_modes": [
            "SD contributions table (Table 1) missing or incomplete",
            "SDG targets and indicators not referenced using official SDG framework",
            "climate mitigation impacts not reported under SDG 13.0",
            "no evidence provided or referenced as appendices",
            "description exceeds 100 words",
            "activities from previous monitoring periods included",
        ],
        "content_format": "summary_table",
        "format_instructions": "Begin with a brief narrative (max 100 words) describing project activities and SD contributions. Then present Table 1 with columns: SDG Target | Indicator | Net Impact | Current Period Contributions | Cumulative Lifetime Contributions. Include SDG 13.0 for climate mitigation. Reference appendices containing evidence of SD contributions.",
    },
    "1.13": {
        "title": "Commercially Sensitive Information",
        "parent_section": "Project Details",
        "must_include": [
            "indication of whether any commercially sensitive information has been excluded from the public version",
            "brief description of items to which sensitive information pertains",
            "justification for why the information is commercially sensitive",
            "confirmation that excluded information is not otherwise publicly available",
        ],
        "examples": [
            "No commercially sensitive information has been excluded from the public version of this monitoring report.",
            "Commercially sensitive information related to proprietary forest inventory methods has been excluded and is provided in Appendix 1.",
        ],
        "failure_modes": [
            "section left blank without stating whether sensitive information exists",
            "information related to baseline, additionality, or emission quantification excluded (not permitted)",
            "no justification provided for excluding information",
        ],
        "content_format": "prose",
        "format_instructions": "State whether any commercially sensitive information has been excluded. If yes, describe the items, justify why the information is commercially sensitive, and confirm it is not otherwise publicly available.",
    },
    "2.1": {
        "title": "Stakeholder Engagement and Consultation",
        "parent_section": "Safeguards and Stakeholder Engagement",
        "must_include": [
            "stakeholder identification process and list of stakeholders (if changed since validation)",
            "description of legal or customary tenure and access rights",
            "stakeholder diversity and changes over time",
            "expected changes in well-being under baseline scenario",
            "location of stakeholders and areas predicted to be impacted",
            "ongoing consultation activities during the monitoring period",
            "dates of stakeholder consultation",
            "how monitoring results were communicated",
            "consultation records and documentation methods",
            "how stakeholder input was taken into account",
            "FPIC process: consent obtained, outcome, information disclosed",
            "grievance redress procedure and any grievances raised with resolution",
            "public comments received with actions taken",
        ],
        "examples": [
            "Stakeholder consultation was conducted on 15-March-2023. Monitoring results were shared with community leaders. No grievances were raised during the monitoring period.",
        ],
        "failure_modes": [
            "no evidence of ongoing stakeholder consultation during the monitoring period",
            "FPIC process not described or outcomes not documented",
            "grievance redress procedure not accessible to stakeholders",
            "public comments not addressed or actions not documented",
            "stakeholder identification not updated when makeup has changed",
        ],
        "content_format": "prose",
        "format_instructions": "Write a structured narrative covering stakeholder identification, consultation activities, dates, FPIC process, grievance redress, and public comments. Use sub-headings to organise the different aspects of stakeholder engagement.",
    },
    "2.2": {
        "title": "Risks to Stakeholders and the Environment",
        "parent_section": "Safeguards and Stakeholder Engagement",
        "must_include": [
            "demonstration that management teams have expertise or experience in similar project activities",
            "risk assessment table with risks identified at validation",
            "mitigation or preventative measures taken for each risk during the monitoring period",
            "coverage of: natural/human-induced risks, risks to participation, working conditions, safety of women and girls, safety of minorities and marginalized groups, pollutants",
        ],
        "examples": [
            "Risk: Natural disasters impacting forest area. Mitigation: Fire prevention measures including firebreaks and community fire brigades maintained during the monitoring period.",
        ],
        "failure_modes": [
            "management experience not demonstrated",
            "risk assessment table missing or incomplete",
            "risks identified but no mitigation measures described",
            "risk categories from the template not all addressed",
            "new entities involved but their management experience not demonstrated",
        ],
        "content_format": "prose",
        "format_instructions": "Begin with a narrative demonstrating management team expertise. Then describe each risk category (natural/human-induced, participation, working conditions, safety of women/girls, minorities, pollutants) with corresponding mitigation measures taken during the monitoring period.",
    },
    "2.3": {
        "title": "Respect for Human Rights and Equity",
        "parent_section": "Safeguards and Stakeholder Engagement",
        "must_include": [
            "identification of risks to rights related to labor and work",
            "mitigation or preventative measures for labor and work risks",
            "identification of risks to rights related to indigenous peoples, local communities, and customary rights holders",
            "mitigation measures for IP and LC rights risks",
            "identification of risks to cultural heritage and rights related to property",
            "identification of risks to rights related to equality and non-discrimination",
        ],
        "examples": [
            "No risks to labor rights were identified. Workers are employed under contracts complying with national labor laws.",
        ],
        "failure_modes": [
            "labor and work risks not addressed",
            "indigenous peoples and local community rights not discussed",
            "risks identified but mitigation measures not described",
            "section marked N/A without justification",
        ],
        "content_format": "prose",
        "format_instructions": "Address each rights category (labor/work, indigenous peoples/local communities, cultural heritage/property, equality/non-discrimination) with identified risks and corresponding mitigation measures.",
    },
    "2.4": {
        "title": "Ecosystem Health",
        "parent_section": "Safeguards and Stakeholder Engagement",
        "must_include": [
            "identification of risks to biodiversity and ecosystems",
            "mitigation or preventative measures for ecosystem risks",
            "identification of risks to soil, water, and air resources",
            "mitigation measures for resource risks",
            "for AFOLU projects: demonstration that native species are used or justification for non-native species",
        ],
        "examples": [
            "Biodiversity monitoring confirms no negative impacts on key species. Water quality testing shows no degradation of local water sources.",
        ],
        "failure_modes": [
            "ecosystem health risks not identified or addressed",
            "biodiversity and natural resource impacts not discussed",
            "AFOLU species requirements not addressed",
            "risks identified but no mitigation measures provided",
        ],
        "content_format": "prose",
        "format_instructions": "Describe risks to biodiversity, ecosystems, soil, water, and air resources with corresponding mitigation measures. For AFOLU projects, demonstrate that native species are used or justify the use of non-native species.",
    },
    "3.1": {
        "title": "Implementation Status of the Project Activity",
        "parent_section": "Implementation Status",
        "must_include": [
            "operation of the project activity during the monitoring period",
            "events that may impact GHG emission reductions, removals, or monitoring",
            "any changes to project proponent or other entities",
            "for AFOLU: demonstration that previously implemented activities continued if no new activities were implemented",
            "for AFOLU: any loss of carbon stock during the monitoring period with date, size, and extent",
        ],
        "examples": [
            "The project continued forest protection activities throughout the monitoring period. No loss events or reversals occurred. No changes to the project proponent.",
        ],
        "failure_modes": [
            "implementation status not described for the current monitoring period",
            "events impacting GHG reductions not reported",
            "AFOLU carbon stock losses not reported when applicable",
            "loss events reported without specifying date, size, and extent",
        ],
        "content_format": "prose",
        "format_instructions": "Describe the operation of project activities during the monitoring period, any events impacting GHG reductions, and any changes to proponents or entities. For AFOLU projects, address continuation of activities and any carbon stock losses with date, size, and extent.",
    },
    "3.2": {
        "title": "Deviations",
        "parent_section": "Implementation Status",
        "must_include": [
            "description and justification of any methodology deviations including previous deviations",
            "evidence that methodology deviations do not negatively impact conservativeness",
            "evidence that methodology deviations relate only to monitoring or measurement criteria",
            "description and justification of any project description deviations during current and previous monitoring periods",
            "assessment of whether PD deviations impact applicability, additionality, or baseline scenario",
            "if no deviations: explicit statement",
        ],
        "examples": [
            "No methodology deviations were applied. No project description deviations were applied during this monitoring period.",
        ],
        "failure_modes": [
            "deviations applied but not described or justified",
            "conservativeness impact of methodology deviations not demonstrated",
            "PD deviations not assessed for impact on applicability, additionality, or baseline",
            "previous deviations not mentioned",
            "section left blank without stating whether deviations exist",
        ],
        "content_format": "prose",
        "format_instructions": "Describe any methodology deviations and project description deviations separately. For each deviation, provide justification and impact assessment. If no deviations exist, state this explicitly.",
    },
    "3.3": {
        "title": "Grouped Projects",
        "parent_section": "Implementation Status",
        "must_include": [
            "for grouped projects: information about new project activity instances",
            "demonstration that each new instance meets eligibility criteria from the project description",
            "each eligibility criterion addressed separately",
            "if not a grouped project: explicit statement",
        ],
        "examples": [
            "This is not a grouped project.",
            "Two new project activity instances were added. Instance A meets all eligibility criteria as demonstrated below.",
        ],
        "failure_modes": [
            "new instances added without demonstrating eligibility",
            "eligibility criteria not addressed separately",
            "section left blank for grouped projects",
        ],
        "content_format": "prose",
        "format_instructions": "If not a grouped project, state this explicitly. For grouped projects, describe each new project activity instance and demonstrate compliance with each eligibility criterion separately.",
    },
    "3.4": {
        "title": "Baseline Reassessment",
        "parent_section": "Implementation Status",
        "must_include": [
            "statement on whether baseline reassessment was conducted during the monitoring period",
            "if yes: summary of the baseline reassessment including use of latest methodology version",
            "if yes: sections in the project description updated to reflect baseline changes",
            "if yes: whether the previous baseline scenario is still valid",
            "if yes: impact of new national or sectoral policies on baseline validity",
            "if yes: percentage change between revised and previous baseline emissions",
        ],
        "examples": [
            "No baseline reassessment was conducted during the monitoring period.",
        ],
        "failure_modes": [
            "no statement on whether baseline reassessment was conducted",
            "baseline reassessment conducted but summary not provided",
            "updated project description sections not identified",
            "impact of policy changes on baseline not discussed when applicable",
            "percentage change in baseline emissions not reported after reassessment",
        ],
        "content_format": "prose",
        "format_instructions": "State whether a baseline reassessment was conducted. If yes, provide a summary including methodology version used, updated project description sections, validity of previous baseline, policy impacts, and percentage change in baseline emissions.",
    },
    "4.1": {
        "title": "Data and Parameters Available at Validation",
        "parent_section": "Data and Parameters",
        "must_include": [
            "table for each data unit or parameter fixed at validation",
            "data/parameter name",
            "data unit (unit of measure)",
            "description of the data/parameter",
            "source of data",
            "value applied",
            "justification of choice of data or description of measurement methods and procedures",
            "purpose of data (baseline scenario determination, baseline emissions, project emissions, or leakage)",
        ],
        "examples": [
            "Parameter: Carbon fraction (CF). Unit: tC/t d.m. Description: Carbon fraction of dry matter. Source: IPCC 2006 Guidelines. Value: 0.47. Purpose: Calculation of baseline emissions.",
        ],
        "failure_modes": [
            "parameter table missing required fields",
            "values listed without sources",
            "sources not traceable (missing references)",
            "purpose of data not specified",
            "measurement methods not described for measured values",
        ],
        "content_format": "parameter_blocks",
        "format_instructions": "Present each parameter as a structured block with fields on separate lines: Parameter Name, Data Unit, Description, Source of Data, Value Applied, Justification/Measurement Methods, Purpose (baseline scenario determination, baseline emissions, project emissions, or leakage). Provide one block per parameter fixed at validation.",
    },
    "4.2": {
        "title": "Data and Parameters Monitored",
        "parent_section": "Data and Parameters",
        "must_include": [
            "table for each monitored data unit or parameter",
            "data/parameter name and unit",
            "description of the data/parameter",
            "source of data",
            "description of measurement methods and procedures",
            "frequency of monitoring and recording",
            "value monitored",
            "monitoring equipment (type, accuracy class, serial number)",
            "QA/QC procedures applied including calibration",
            "purpose of data (baseline emissions, project emissions, or leakage)",
            "calculation method including equations where relevant",
        ],
        "examples": [
            "Parameter: Above-ground biomass (AGB). Unit: t d.m./ha. Source: Field measurements. Measurement: Plot-based inventory following national forest inventory protocol. Frequency: Annual. Equipment: Diameter tape (accuracy +/- 0.1 cm). QA/QC: 10% of plots re-measured by independent team.",
        ],
        "failure_modes": [
            "monitored parameter table missing required fields",
            "measurement methods and procedures not described",
            "monitoring frequency not specified",
            "QA/QC procedures not described",
            "monitoring equipment not identified with accuracy information",
            "calculation method not provided where relevant",
        ],
        "content_format": "parameter_blocks",
        "format_instructions": "Present each monitored parameter as a structured block with fields on separate lines: Parameter Name, Data Unit, Description, Source of Data, Measurement Methods and Procedures, Monitoring Frequency, Value Monitored, Monitoring Equipment (type, accuracy class, serial number), QA/QC Procedures, Purpose (baseline emissions, project emissions, or leakage), Calculation Method. Provide one block per monitored parameter.",
    },
    "4.3": {
        "title": "Monitoring Plan",
        "parent_section": "Data and Parameters",
        "must_include": [
            "process and schedule followed during the monitoring period for obtaining, compiling, and analyzing data",
            "methods used for measuring, recording, storing, aggregating, collating, and reporting data",
            "calibration processes for monitoring equipment where relevant",
            "organizational structure, responsibilities, and competencies of monitoring personnel",
            "processes for internal auditing and handling non-conformities",
            "implementation of sampling approaches including target precision, sample sizes, site locations, stratification, frequency, and QA/QC",
            "demonstration of whether required confidence level or precision has been met",
        ],
        "examples": [
            "Monitoring was conducted by a team of 5 trained field officers under the supervision of a senior forest ecologist. Data was collected annually using systematic sampling across 100 permanent plots.",
        ],
        "failure_modes": [
            "monitoring plan not described for the current monitoring period",
            "organizational structure and responsibilities not detailed",
            "sampling approach not described when sampling is used",
            "confidence/precision level not demonstrated",
            "calibration procedures not described for monitoring equipment",
            "internal audit processes not documented",
        ],
        "content_format": "prose",
        "format_instructions": "Write a structured narrative covering the monitoring process, data management methods, calibration procedures, organisational structure, internal auditing, and sampling approaches. Use sub-headings to organise each aspect of the monitoring plan.",
    },
    "5.1": {
        "title": "Baseline Emissions",
        "parent_section": "Quantification of GHG Emission Reductions and Removals",
        "must_include": [
            "quantification of baseline emissions and/or carbon stock changes for the monitoring period",
            "application of the methodology for baseline calculation",
            "all relevant equations included",
            "sufficient information to allow the reader to reproduce the calculation",
            "reductions and removals specified separately where methodology provides for it",
            "calculations included in the emission reduction and removal calculation spreadsheet",
        ],
        "examples": [
            "Baseline emissions for the monitoring period: BE = A_BSL x EF_BSL = 5,000 ha x 150 tCO2e/ha = 750,000 tCO2e. See ER Calculation Spreadsheet, Baseline tab.",
        ],
        "failure_modes": [
            "baseline emissions not quantified for the monitoring period",
            "equations not shown or not sufficient to reproduce calculations",
            "methodology not correctly applied",
            "reductions and removals not separated where required",
            "no reference to calculation spreadsheet",
        ],
        "content_format": "equations_and_prose",
        "format_instructions": "Present all baseline emission equations using standard notation (e.g. BE_y = A_BSL x EF_BSL). Define all variables with their units and substitute actual values from the monitoring period. Separate reductions and removals where required by the methodology. Reference the ER calculation spreadsheet.",
    },
    "5.2": {
        "title": "Project Emissions",
        "parent_section": "Quantification of GHG Emission Reductions and Removals",
        "must_include": [
            "quantification of project emissions and/or carbon stock changes for the monitoring period",
            "application of the methodology for project emissions calculation",
            "all relevant equations included",
            "sufficient information to allow the reader to reproduce the calculation",
            "reductions and removals specified separately where methodology provides for it",
            "calculations included in the emission reduction and removal calculation spreadsheet",
        ],
        "examples": [
            "Project emissions for the monitoring period: PE = sum of emissions from project activities = 50,000 tCO2e. See ER Calculation Spreadsheet, Project tab.",
        ],
        "failure_modes": [
            "project emissions not quantified for the monitoring period",
            "equations not shown or insufficient to reproduce calculations",
            "methodology not correctly applied",
            "reductions and removals not separated where required",
            "no reference to calculation spreadsheet",
        ],
        "content_format": "equations_and_prose",
        "format_instructions": "Present all project emission equations using standard notation (e.g. PE_y = sum of emission sources). Define all variables with their units and substitute actual values from the monitoring period. Separate reductions and removals where required by the methodology. Reference the ER calculation spreadsheet.",
    },
    "5.3": {
        "title": "Leakage Emissions",
        "parent_section": "Quantification of GHG Emission Reductions and Removals",
        "must_include": [
            "quantification of leakage emissions for the monitoring period",
            "application of the methodology for leakage calculation",
            "all relevant equations included",
            "sufficient information to allow the reader to reproduce the calculation",
            "reductions and removals specified separately where methodology provides for it",
            "calculations included in the emission reduction and removal calculation spreadsheet",
        ],
        "examples": [
            "Leakage emissions: LE = activity-shifting leakage + market leakage = 10,000 + 5,000 = 15,000 tCO2e. See ER Calculation Spreadsheet, Leakage tab.",
            "No leakage is applicable per the methodology. LE = 0 tCO2e.",
        ],
        "failure_modes": [
            "leakage emissions not quantified",
            "leakage assumed zero without methodology justification",
            "equations not shown or insufficient for reproduction",
            "no reference to calculation spreadsheet",
        ],
        "content_format": "equations_and_prose",
        "format_instructions": "Present all leakage emission equations using standard notation (e.g. LE_y = LE_activity + LE_market). Define all variables with their units and substitute actual values from the monitoring period. If leakage is zero, state the methodology justification. Reference the ER calculation spreadsheet.",
    },
    "5.4": {
        "title": "GHG Emission Reductions and Carbon Dioxide Removals",
        "parent_section": "Quantification of GHG Emission Reductions and Removals",
        "must_include": [
            "quantification of total GHG emission reductions and removals for the monitoring period",
            "vintage period table with baseline emissions, project emissions, leakage emissions, reduction VCUs, removal VCUs, and total VCUs by calendar year",
            "for projects with permanence risk: non-permanence risk rating, buffer pool allocation, and LTA where applicable",
            "ex-ante vs achieved comparison table with vintage period, estimated reductions/removals, achieved reductions/removals, percent difference, and explanation",
            "all relevant equations included",
        ],
        "examples": [
            "Total VCUs for the monitoring period: Baseline 750,000 - Project 50,000 - Leakage 15,000 = 685,000 tCO2e. Vintage 2022: 685,000 VCUs issued.",
        ],
        "failure_modes": [
            "vintage period table not completed by calendar year",
            "reductions and removals not separated where required by methodology",
            "non-permanence risk rating and buffer pool not included for AFOLU projects",
            "ex-ante vs achieved comparison table missing",
            "percent difference not calculated or explained",
            "total VCUs not summed across vintage periods",
        ],
        "content_format": "summary_table",
        "format_instructions": "Present two tables: (1) Vintage period summary table with columns: Vintage Period | Baseline Emissions (tCO2e) | Project Emissions (tCO2e) | Leakage Emissions (tCO2e) | Reduction VCUs | Removal VCUs | Total VCUs, with one row per calendar year and a totals row. (2) Ex-ante vs achieved comparison table with columns: Vintage Period | Estimated Reductions/Removals | Achieved Reductions/Removals | Percent Difference | Explanation. Include the net emission reduction equation (ER_y = BE_y - PE_y - LE_y) and, for AFOLU projects, the non-permanence risk rating and buffer pool allocation.",
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
