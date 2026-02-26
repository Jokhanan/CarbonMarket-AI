"""
gs_poa_dd_v2_2.py — Gold Standard Programme of Activity Design Document guide
(PoA-DD v2.2).

Full coverage: Sections A–E.
"""

GUIDE_ID = "GoldStandard_PoA_DD_v2_2"

SUBSECTIONS: dict[str, dict] = {
    "A.1": {
        "title": "Purpose and general description of the PoA",
        "parent_section": "SECTION A",
        "must_include": [
            "brief description of the PoA",
            "policy/measure or stated goal that the PoA seeks to promote",
            "framework for implementation of the PoA and inclusion of VPAs",
            "confirmation that the PoA is a voluntary action by the coordinating/managing entity",
        ],
        "examples": [
            "The PoA aims to promote the adoption of improved cookstoves across rural households in Sub-Saharan Africa, reducing firewood consumption and associated GHG emissions.",
        ],
        "failure_modes": [
            "no description of the policy or stated goal the PoA promotes",
            "framework for VPA inclusion not described",
            "missing confirmation that the PoA is a voluntary action",
            "description is too vague without specifying the actual programme activity",
        ],
    },
    "A.2": {
        "title": "Physical/geographical boundary of the PoA",
        "parent_section": "SECTION A",
        "must_include": [
            "geographical area within which all VPAs will be implemented",
            "boundary defined in terms of municipality, region, country, or multiple countries",
            "confirmation that boundary is defined in its entirety at Design Certification",
        ],
        "examples": [
            "The PoA boundary covers the entire territory of Kenya and Uganda.",
        ],
        "failure_modes": [
            "no geographical boundary defined",
            "boundary described too vaguely without specifying countries or regions",
            "boundary not defined in its entirety at time of Design Certification",
        ],
    },
    "A.3": {
        "title": "Technologies/measures",
        "parent_section": "SECTION A",
        "must_include": [
            "description of technologies and/or measures employed by VPAs under the PoA",
            "description of how technologies/measures and know-how are transferred to the host party where applicable",
        ],
        "examples": [
            "The PoA deploys high-efficiency biomass cookstoves with thermal efficiency above 40%, replacing traditional three-stone fires.",
        ],
        "failure_modes": [
            "technologies or measures not clearly described",
            "no mention of how technology/know-how is transferred to host party",
            "generic description without specifying the actual technology",
        ],
    },
    "A.4": {
        "title": "Target/Indicator for SDGs",
        "parent_section": "SECTION A",
        "must_include": [
            "SDGs targeted by the PoA (minimum three)",
            "most relevant SDG target for each SDG",
            "SDG impact indicator selected for each SDG",
            "SDG 13 (Climate Action) listed as mandatory",
        ],
        "examples": [
            "SDG 13 Climate Action: Emissions Reductions. SDG 7 Affordable and Clean Energy: MWh of renewable energy generated. SDG 3 Good Health: aDALYs avoided.",
        ],
        "failure_modes": [
            "fewer than three SDGs targeted",
            "SDG 13 not included as mandatory",
            "SDG targets or indicators missing for listed SDGs",
            "no table or structured presentation of SDG targets and indicators",
        ],
    },
    "A.5": {
        "title": "Coordinating/managing entity",
        "parent_section": "SECTION A",
        "must_include": [
            "name of the coordinating/managing entity (CME) of the PoA",
            "contact information provided in the appendix",
        ],
        "examples": [
            "The CME for this PoA is GreenCarbon GmbH. Contact details are provided in Appendix 1.",
        ],
        "failure_modes": [
            "CME name not provided",
            "no reference to contact information in appendix",
            "CME role and responsibilities not clear",
        ],
    },
    "A.6": {
        "title": "Funding sources of PoA",
        "parent_section": "SECTION A",
        "must_include": [
            "indication of whether the PoA receives public funding",
            "if public funding received: sources of public funding",
            "signed ODA Declaration for projects in OECD DAC ODA recipient countries",
        ],
        "examples": [
            "The PoA does not receive any public funding. All financing is through private investment and carbon credit revenues.",
            "The PoA receives partial public funding from GIZ. A signed ODA Declaration is attached.",
        ],
        "failure_modes": [
            "no indication of whether public funding is received",
            "public funding sources not disclosed",
            "ODA Declaration missing for projects in eligible countries",
            "section left blank without explicit statement",
        ],
    },
    "B.1": {
        "title": "Management System",
        "parent_section": "SECTION B",
        "must_include": [
            "operational and management system for PoA implementation",
            "clear definition of roles and responsibilities of personnel for VPA inclusion",
            "review of personnel competencies",
            "arrangements for training and capacity development",
            "procedure for technical review of VPA inclusion",
            "procedure to avoid double counting of VPAs",
            "records and documentation control process for each VPA",
            "measures for continuous improvement of the PoA management system",
        ],
        "examples": [
            "The management system includes a dedicated PoA Manager responsible for VPA inclusion review, a Quality Assurance Officer for documentation control, and annual training sessions for field staff.",
        ],
        "failure_modes": [
            "management system not described in sufficient detail",
            "roles and responsibilities not clearly defined",
            "no procedure to avoid double counting",
            "no documentation control process described",
            "missing training and capacity development arrangements",
            "no measures for continuous improvement",
        ],
    },
    "B.2": {
        "title": "Application of methodologies",
        "parent_section": "SECTION B",
        "must_include": [
            "exact references to selected GHG baseline and monitoring methodologies (title, version, UNFCCC reference number where applicable)",
            "any methodological tools referenced by the selected methodologies",
            "any selected standardized baselines where applicable",
            "any mandatory GS Guidelines applied (e.g. Usage Survey Guidelines)",
        ],
        "examples": [
            "Methodology: Technologies and Practices to Displace Decentralized Thermal Energy Consumption, version 4.0. Tool: Tool for the Demonstration and Assessment of Additionality, version 07.0.0.",
        ],
        "failure_modes": [
            "methodology name given without version number",
            "UNFCCC reference numbers missing where applicable",
            "methodological tools used but not listed",
            "mandatory GS Guidelines not referenced",
        ],
    },
    "B.2.1": {
        "title": "Multiple technologies/measures",
        "parent_section": "SECTION B",
        "must_include": [
            "list of all combinations of technologies/measures and methodologies used in the PoA",
            "demonstration that no GHG/SDG cross effects exist between technologies/measures, or how cross effects are accounted for",
        ],
        "examples": [
            "The PoA applies two technology types: improved cookstoves (AMS-II.G v09) and solar water heaters (AMS-I.J v07). No cross effects exist as each technology addresses a different end use.",
        ],
        "failure_modes": [
            "not all combinations of technologies and methodologies listed",
            "cross effects not addressed",
            "cross effects exist but no explanation of how they are accounted for in calculations",
            "section left blank when multiple technologies are applied",
        ],
    },
    "B.3": {
        "title": "Eligibility criteria for inclusion of VPA in PoA",
        "parent_section": "SECTION B",
        "must_include": [
            "eligibility criteria table with criterion number, description/required condition, and means of verification",
            "conditions to check VPA compliance with GS4GG Principles & Requirements",
            "conditions to check VPA compliance with applicable Activity Requirements",
            "geographical boundary consistency between VPA and PoA",
            "conditions to avoid double counting of GHG emission reductions",
            "conditions to check start dates of VPA through documentary evidence",
            "conditions to ensure compliance with applicable methodologies",
            "conditions to ensure VPA meets additionality demonstration requirements",
        ],
        "examples": [
            "Criterion 1: VPA is located within the PoA boundary (Kenya or Uganda). Means of verification: GPS coordinates and site visit records.",
        ],
        "failure_modes": [
            "eligibility criteria table missing or incomplete",
            "no means of verification specified for criteria",
            "double counting prevention not addressed",
            "start date verification conditions missing",
            "methodology applicability conditions not included",
            "additionality demonstration requirements missing",
            "distinct criteria not defined for different VPA types when applicable",
        ],
    },
    "C.1": {
        "title": "Demonstration of additionality",
        "parent_section": "SECTION C",
        "must_include": [
            "demonstration that without Gold Standard Certification related finance the VPAs would not be implemented",
            "or demonstration that mandatory policy/regulation is systematically not enforced and noncompliance is widespread",
            "or demonstration that PoA leads to greater enforcement of existing mandatory policy/regulation or greater adoption of existing voluntary scheme",
            "for retroactive PoAs/VPAs: demonstration of prior consideration per GHG Emissions Reductions & Sequestration requirements",
        ],
        "examples": [
            "Without carbon finance, the distribution of improved cookstoves would not be financially viable as end-user willingness to pay covers only 30% of unit costs.",
        ],
        "failure_modes": [
            "no clear demonstration of additionality",
            "additionality argument not supported with evidence or financial analysis",
            "prior consideration not demonstrated for retroactive PoAs/VPAs",
            "section contains only generic statements without project-specific justification",
        ],
    },
    "D.1": {
        "title": "Date of first submission",
        "parent_section": "SECTION D",
        "must_include": [
            "date when PoA was submitted to Gold Standard for Preliminary Review",
            "date in DD/MM/YYYY format",
        ],
        "examples": [
            "The PoA was first submitted to Gold Standard on 15/03/2022.",
        ],
        "failure_modes": [
            "no submission date provided",
            "date not in required DD/MM/YYYY format",
            "section left blank",
        ],
    },
    "D.2": {
        "title": "Duration of the PoA",
        "parent_section": "SECTION D",
        "must_include": [
            "PoA crediting cycle start date",
            "total duration of the PoA in years and months",
            "maximum duration not exceeding 28 years (renewable twice for 7 years each)",
        ],
        "examples": [
            "Start date: 01/01/2020. Duration: 28 years, 0 months.",
        ],
        "failure_modes": [
            "no crediting cycle start date provided",
            "total duration not stated in years and months",
            "duration exceeds maximum allowed period without justification",
            "section left blank",
        ],
    },
    "E.1": {
        "title": "Summary of stakeholder consultation at PoA Level",
        "parent_section": "SECTION E",
        "must_include": [
            "summary of PoA-level stakeholder consultation process",
            "description of stakeholders consulted",
            "method of consultation (e.g. meetings, workshops, surveys)",
            "key topics discussed during consultation",
        ],
        "examples": [
            "A stakeholder consultation was held on 10/05/2022 in Nairobi with representatives from local government, community leaders, and NGOs. Key topics included environmental impact, community benefits, and grievance mechanisms.",
        ],
        "failure_modes": [
            "no summary of stakeholder consultation provided",
            "stakeholders not identified",
            "consultation method not described",
            "key topics not summarized",
            "section left blank when PoA-level consultation is required",
        ],
    },
    "E.2": {
        "title": "Consideration of stakeholder comments received",
        "parent_section": "SECTION E",
        "must_include": [
            "list of comments received from stakeholders",
            "response or action taken for each comment",
            "explanation of how comments were incorporated into PoA design or why they were not",
        ],
        "examples": [
            "Comment: Community leaders requested additional training on cookstove maintenance. Response: A maintenance training programme was added to the VPA implementation plan.",
        ],
        "failure_modes": [
            "comments received but not listed",
            "no response provided for stakeholder comments",
            "no explanation of how comments influenced PoA design",
            "section left blank when comments were received",
        ],
    },
    "E.3": {
        "title": "Final Continuous Input / Grievance Mechanism",
        "parent_section": "SECTION E",
        "must_include": [
            "description of the Continuous Input and Grievance Mechanism (CIGM)",
            "how stakeholders can submit inputs or grievances",
            "process for addressing and resolving grievances",
            "confirmation that CIGM will be maintained throughout the PoA duration",
        ],
        "examples": [
            "A dedicated phone line and email address are available for stakeholder grievances. All grievances are logged, investigated within 30 days, and responses communicated to the complainant.",
        ],
        "failure_modes": [
            "no grievance mechanism described",
            "no clear process for submitting grievances",
            "no process for resolving grievances",
            "CIGM not confirmed to be maintained throughout PoA duration",
            "section left blank",
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
