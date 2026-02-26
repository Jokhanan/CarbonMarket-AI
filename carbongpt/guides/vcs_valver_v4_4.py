"""
vcs_valver_v4_4.py — Verra VCS Joint Validation & Verification Report guide
(VCS v4.4).

Full coverage: Sections 1–5.
"""

GUIDE_ID = "Verra_VCS_ValVer_v4_4"

SUBSECTIONS: dict[str, dict] = {
    "1.1": {
        "title": "Objective",
        "parent_section": "SECTION 1",
        "must_include": [
            "purpose of the validation and verification",
            "statement of what the audit intends to confirm or assess",
        ],
        "examples": [
            "The objective of this validation and verification is to assess the conformance of the project with VCS Program requirements and to evaluate the GHG emission reductions achieved during the monitoring period.",
        ],
        "failure_modes": [
            "no clear statement of the purpose of the audit",
            "objective is generic without reference to VCS Program or the specific project",
            "validation and verification objectives not distinguished where relevant",
        ],
    },
    "1.2": {
        "title": "Scope and Criteria",
        "parent_section": "SECTION 1",
        "must_include": [
            "scope of the validation and verification engagement",
            "criteria used for the assessment (e.g., VCS Standard version, methodology)",
            "any boundaries or limitations of the scope",
        ],
        "examples": [
            "The scope includes validation of the project description and verification of GHG emission reductions for the period 01-Jan-2022 to 31-Dec-2022 against VCS Standard v4.4 and methodology VM0015 v1.1.",
        ],
        "failure_modes": [
            "scope not clearly defined",
            "VCS Standard version not referenced",
            "applicable methodology not mentioned",
            "monitoring period dates not specified in the scope",
        ],
    },
    "1.3": {
        "title": "Reasonableness of Assumptions and Level of Assurance",
        "parent_section": "SECTION 1",
        "must_include": [
            "for validation: reasonableness of assumptions, limitations, and methods supporting statements about future outcomes",
            "for verification: level of assurance provided",
            "any material limitations or qualifications",
        ],
        "examples": [
            "For validation, the assumptions regarding future emission reductions are considered reasonable based on historical data and conservative default values. For verification, a reasonable level of assurance is provided.",
        ],
        "failure_modes": [
            "no distinction between validation assumptions and verification assurance level",
            "level of assurance not explicitly stated for verification",
            "assumptions described without assessing their reasonableness",
        ],
    },
    "1.4": {
        "title": "Summary Description of the Project",
        "parent_section": "SECTION 1",
        "must_include": [
            "brief description of the project activity",
            "project type and technology or measures employed",
            "location of the project",
            "summary limited to approximately one page",
        ],
        "examples": [
            "The project involves the installation of a 50 MW wind farm in Tamil Nadu, India, displacing grid electricity generated from fossil fuels. The project is registered under VCS and uses methodology ACM0002.",
        ],
        "failure_modes": [
            "summary exceeds one page or is overly detailed for an introduction",
            "no mention of the project type or technology",
            "project location not included in the summary",
            "summary is too vague to give the reader an understanding of the project",
        ],
    },
    "2.1": {
        "title": "Method and Criteria",
        "parent_section": "SECTION 2",
        "must_include": [
            "description of the method used for validation and verification",
            "evidence-gathering plan and approach",
            "important assumptions and justification for the chosen approach",
            "validation and verification schedule with key milestones and dates",
        ],
        "examples": [
            "The validation and verification was conducted following ISO 14064-3:2019. Key milestones included a kick-off meeting on 15-Mar-2023, desk review from 20-Mar to 15-Apr-2023, site visit on 01-May-2023, and report finalization on 30-Jun-2023.",
        ],
        "failure_modes": [
            "no evidence-gathering plan described",
            "schedule or key milestones not provided",
            "method described without referencing applicable standards (e.g., ISO 14064-3)",
            "assumptions not stated or justified",
        ],
    },
    "2.2": {
        "title": "Document Review",
        "parent_section": "SECTION 2",
        "must_include": [
            "description of how the document review was performed",
            "list or description of documents reviewed (project description, monitoring report, supporting documents)",
            "how documents were cross-checked and compared with requirements",
        ],
        "examples": [
            "The audit team reviewed the project description v3.0, monitoring report for MP2, emission reduction calculation spreadsheet, and calibration certificates. Documents were cross-checked against VCS Standard requirements and the applied methodology.",
        ],
        "failure_modes": [
            "no description of which documents were reviewed",
            "document review process not described",
            "no mention of cross-checking documents against requirements",
        ],
    },
    "2.3": {
        "title": "Interviews",
        "parent_section": "SECTION 2",
        "must_include": [
            "description of the interview process",
            "identification of personnel interviewed including their roles",
            "information obtained beyond what was in project documents",
        ],
        "examples": [
            "Interviews were conducted with the project manager (Mr. Smith, CleanEnergy Ltd), the monitoring officer (Ms. Doe), and community liaison (Mr. Osei) to verify implementation status and stakeholder engagement activities.",
        ],
        "failure_modes": [
            "no personnel identified by name or role",
            "interview process not described",
            "section states interviews were conducted but provides no details",
        ],
    },
    "2.4": {
        "title": "Site Visits",
        "parent_section": "SECTION 2",
        "must_include": [
            "method and objectives for site visits",
            "details of facilities and project areas visited",
            "physical and organizational aspects assessed",
            "dates of site visits",
            "if site visit occurred before end of monitoring period: description of additional evidence gathering and demonstration of reasonable assurance",
        ],
        "examples": [
            "A site visit was conducted on 01-May-2023 to the wind farm location in Tamil Nadu. The team inspected turbine installations, reviewed on-site monitoring equipment, and verified metering infrastructure. The organizational structure and O&M procedures were also assessed.",
        ],
        "failure_modes": [
            "site visit dates not provided",
            "no description of what was physically inspected or assessed",
            "facilities or project areas visited not identified",
            "site visit prior to end of monitoring period without additional evidence gathering described",
        ],
    },
    "2.5": {
        "title": "Resolution of Findings",
        "parent_section": "SECTION 2",
        "must_include": [
            "process for resolution of findings (CARs, CLs, FARs, other findings)",
            "outstanding forward action requests from previous audits addressed",
            "total number of CARs, CLs, FARs, and other findings raised",
            "summary of each finding including issue, response, and conclusion",
            "details of any forward action requests raised for subsequent audits",
        ],
        "examples": [
            "A total of 3 CARs, 2 CLs, and 1 FAR were raised. CAR-01: Incomplete emission factor documentation. Response: Project proponent provided updated references. Conclusion: Resolved, PD updated accordingly.",
        ],
        "failure_modes": [
            "total number of findings not stated",
            "findings listed without responses or conclusions",
            "outstanding FARs from previous audits not addressed",
            "resolution process not described",
            "forward action requests not detailed for future audits",
        ],
    },
    "3.1": {
        "title": "Project Details",
        "parent_section": "SECTION 3",
        "must_include": [
            "overall conclusion on accuracy and completeness of the project description",
            "evidence gathering activities, evidence checked, and assessment conclusions for each item",
            "assessment of audit history, sectoral scope, project type, eligibility",
            "assessment of project design, ownership, start date, crediting period, scale",
            "assessment of technologies and measures, implementation schedule, project location",
            "assessment of conditions prior to initiation, legal compliance",
            "assessment of double counting, double claiming, sustainable development contributions",
            "assessment of additional relevant information including leakage management and commercially sensitive information",
        ],
        "examples": [
            "The project description is accurate and complete. Sectoral scope 1 is correctly identified. The project start date of 01-Jan-2020 is supported by commissioning certificates. No evidence of double counting was found.",
        ],
        "failure_modes": [
            "no overall conclusion on project description accuracy",
            "key assessment items missing (e.g., eligibility, double counting)",
            "conclusions stated without describing evidence checked",
            "evidence gathering activities not described for each item",
            "AFOLU-specific items not addressed when applicable",
        ],
    },
    "3.2": {
        "title": "Project Activity Instances in Grouped Projects",
        "parent_section": "SECTION 3",
        "must_include": [
            "steps taken to validate inclusion of project activity instances",
            "evidence-gathering process for validation and verification of instances",
            "number of project activity instances added in this verification period",
            "quality and completeness of evidence for new instances",
            "conformance of instances with eligibility criteria in project description",
            "overall conclusion on validity of inclusion",
        ],
        "examples": [
            "15 new project activity instances were added during this verification period. Each instance was verified against the eligibility criteria in Section 1.5 of the PD. Documentation for all instances was complete and conforming.",
            "This section is not applicable as the project is not a grouped project.",
        ],
        "failure_modes": [
            "section marked N/A without explanation for non-grouped projects",
            "no conclusion on validity of instance inclusion",
            "number of instances added not stated",
            "eligibility criteria conformance not assessed",
            "evidence quality not evaluated",
        ],
    },
    "3.3": {
        "title": "Safeguards",
        "parent_section": "SECTION 3",
        "must_include": [
            "assessment of stakeholder engagement and consultation (identification, consultation, FPIC, grievance redress, public comments)",
            "assessment of risks to local stakeholders and the environment (management experience, risk assessment)",
            "assessment of respect for human rights and equity (labor, human rights, indigenous peoples, property rights, benefit sharing)",
            "assessment of ecosystem health (biodiversity, soil, water, rare/threatened/endangered species)",
            "evidence gathering activities, evidence checked, and conclusions for each safeguard area",
        ],
        "examples": [
            "Stakeholder identification was assessed through review of the stakeholder mapping document. The project proponent identified all relevant stakeholder groups including local communities, government agencies, and NGOs. The grievance redress procedure is accessible and conforms with VCS requirements.",
        ],
        "failure_modes": [
            "one or more safeguard areas not addressed",
            "conclusions stated without evidence gathering description",
            "FPIC assessment missing when indigenous peoples are affected",
            "risk assessment items not individually addressed",
            "ecosystem health risks not evaluated",
            "public comments section omitted",
        ],
    },
    "3.4": {
        "title": "Application of Methodology",
        "parent_section": "SECTION 3",
        "must_include": [
            "assessment of methodology applicability to the project",
            "assessment of project boundary definition",
            "assessment of baseline scenario determination",
            "assessment of additionality demonstration",
            "assessment of quantification approach (baseline, project, leakage emissions)",
            "assessment of any methodology deviations",
            "assessment of monitoring plan",
            "evidence gathering activities and conclusions for each aspect",
        ],
        "examples": [
            "Methodology ACM0002 v19.0 is correctly applied. The project boundary includes the wind farm site and the connected grid. Additionality is demonstrated using the investment analysis approach with supporting financial documentation.",
        ],
        "failure_modes": [
            "methodology applicability not assessed",
            "project boundary assessment missing",
            "additionality not evaluated",
            "baseline scenario determination not assessed",
            "quantification approach not reviewed",
            "methodology deviations not addressed",
            "AFOLU-specific methodology requirements not assessed when applicable",
        ],
    },
    "3.5": {
        "title": "Non-Permanence Risk Analysis",
        "parent_section": "SECTION 3",
        "must_include": [
            "assessment of non-permanence risk analysis where applicable (AFOLU projects)",
            "evaluation of internal, external, and natural risk factors",
            "assessment of quality of documentation and data supporting the risk score",
            "conclusion on appropriateness of the risk score",
            "conclusion on the overall risk rating value",
            "if not applicable: explicit statement with justification",
        ],
        "examples": [
            "The non-permanence risk analysis was assessed. Internal risk is rated at 5%, external risk at 3%, and natural risk at 4%, resulting in an overall risk rating of 12%. The documentation supports the assigned scores.",
            "Non-permanence risk analysis is not applicable as the project is not an AFOLU project.",
        ],
        "failure_modes": [
            "section left blank without stating applicability",
            "risk factors not individually assessed",
            "documentation quality not evaluated",
            "no conclusion on the overall risk rating",
            "risk score accepted without independent assessment",
        ],
    },
    "4.1": {
        "title": "Project Implementation Status",
        "parent_section": "SECTION 4",
        "must_include": [
            "description of implementation status of project activities",
            "overall conclusion on whether project is implemented as described in PD",
            "assessment of project implementation including material misstatements",
            "assessment of monitoring plan implementation and completeness",
            "assessment of monitoring system suitability (process, schedule, data management)",
            "AFOLU-specific implementation assessment if applicable",
        ],
        "examples": [
            "The project has been implemented as described in the PD. All 25 wind turbines are operational. The monitoring plan is fully implemented with automated SCADA data collection. No material misstatements were identified.",
        ],
        "failure_modes": [
            "no overall conclusion on implementation status",
            "monitoring plan implementation not assessed",
            "material misstatements between implementation and PD not evaluated",
            "monitoring system suitability not assessed",
            "AFOLU-specific items not addressed when applicable",
        ],
    },
    "4.2": {
        "title": "Accuracy of Reduction and Removal Calculations",
        "parent_section": "SECTION 4",
        "must_include": [
            "identification of data and parameters used in calculations",
            "assessment of accuracy of spreadsheet formulae, conversions, and aggregations",
            "assessment of consistent use of data and parameters",
            "assessment of whether methods and formulae follow the PD and methodology",
            "assessment of appropriateness of default values used",
            "assessment of manual transposition errors between data sets",
            "overall conclusion on whether reductions/removals are quantified correctly",
        ],
        "examples": [
            "The emission reduction calculations were checked against the methodology formulae. Spreadsheet formulae were independently verified. Default emission factors were confirmed against IPCC sources. No transposition errors were identified. Total verified reductions of 125,000 tCO2e are quantified correctly.",
        ],
        "failure_modes": [
            "no overall conclusion on calculation accuracy",
            "spreadsheet formulae not independently checked",
            "default values used without assessing appropriateness",
            "transposition error assessment not described",
            "data and parameters not identified",
            "methodology conformance of formulae not assessed",
        ],
    },
    "4.3": {
        "title": "Quality of Evidence to Determine Reductions and Removals",
        "parent_section": "SECTION 4",
        "must_include": [
            "identification of evidence used to determine reductions/removals",
            "assessment of sufficiency of quantity and quality of evidence",
            "assessment of reliability, source, and nature of evidence (external/internal, oral/documented)",
            "assessment of information flow from data generation to monitoring report",
            "assessment of calibration frequency of monitoring equipment where applicable",
            "overall conclusion on evidence quality",
        ],
        "examples": [
            "Evidence includes SCADA data exports, grid operator invoices, and calibration certificates. Data flows from turbine meters through SCADA to monthly summary spreadsheets. All monitoring equipment was calibrated within the required intervals. The evidence is sufficient in quantity and appropriate in quality.",
        ],
        "failure_modes": [
            "no overall conclusion on evidence quality",
            "evidence sources not identified",
            "reliability of evidence not assessed",
            "information flow not described",
            "calibration frequency not assessed where relevant",
            "cross-checks on reported data not described",
        ],
    },
    "5.1": {
        "title": "Validation and Verification Summary",
        "parent_section": "SECTION 5",
        "must_include": [
            "statement that the GHG statement is the responsibility of the project proponent",
            "statement on whether the project conforms with VCS validation and verification criteria",
            "any qualifications or modifications to the opinion",
            "if adverse, disclaimed, modified, or qualified: description of reasons placed before the conclusion",
            "if IAF-accredited: declaration of conformance with ISO 14064-3 including version",
        ],
        "examples": [
            "The GHG statement is the responsibility of the project proponent. Based on our assessment, the project conforms with the validation and verification criteria set out in VCS Version 4. This validation and verification was conducted in accordance with ISO 14064-3:2019.",
        ],
        "failure_modes": [
            "no statement that GHG statement is the proponent's responsibility",
            "conformance with VCS criteria not stated",
            "qualified or adverse opinion without reasons described",
            "ISO 14064-3 declaration missing or without version number for IAF-accredited bodies",
        ],
    },
    "5.2": {
        "title": "Validation Conclusion",
        "parent_section": "SECTION 5",
        "must_include": [
            "description of whether data is hypothetical, projected, or historical",
            "statement on reasonableness of assumptions, limitations, and methods",
            "conclusion on whether the project is likely to achieve estimated GHG ERRs",
            "crediting period dates",
            "validated estimated GHG emission reductions and removals table for the crediting period",
            "where applicable: separate validation of reductions and removals",
            "for AFOLU: non-permanence risk rating, buffer pool allocation, and LTA if applicable",
        ],
        "examples": [
            "The data supporting the GHG statement is projected in nature. Assumptions are reasonable. The project is likely to achieve the estimated reductions of 500,000 tCO2e over the 10-year crediting period (01-Jan-2020 to 31-Dec-2029).",
        ],
        "failure_modes": [
            "no conclusion on likelihood of achieving estimated ERRs",
            "crediting period dates not stated",
            "validated estimates table missing or incomplete",
            "nature of data (hypothetical/projected/historical) not described",
            "assumptions not assessed for reasonableness",
            "reductions and removals not validated separately where required",
        ],
    },
    "5.3": {
        "title": "Verification Conclusion",
        "parent_section": "SECTION 5",
        "must_include": [
            "level of assurance stated",
            "verified quantity of GHG emission reductions and removals in tCO2e",
            "verification period dates",
            "breakdown of reductions and removals by calendar year (vintage period)",
            "verified GHG ERRs table",
            "where applicable: separate verification of reductions and removals",
            "for AFOLU: non-permanence risk rating, buffer pool allocation, LTA, and loss accounting",
        ],
        "examples": [
            "With a reasonable level of assurance, the project achieved verified GHG emission reductions of 125,000 tCO2e during the verification period 01-Jan-2022 to 31-Dec-2022.",
        ],
        "failure_modes": [
            "level of assurance not stated",
            "verified quantity not provided in tCO2e",
            "verification period dates missing",
            "vintage period breakdown not provided",
            "verified ERRs table missing or incomplete",
            "reductions and removals not verified separately where required",
        ],
    },
    "5.4": {
        "title": "Ex-ante vs Ex-post ERR Comparison",
        "parent_section": "SECTION 5",
        "must_include": [
            "estimated ex-ante GHG emission reductions and removals for monitoring period",
            "achieved (ex-post) reductions and removals for monitoring period",
            "percentage difference between ex-ante and ex-post",
            "justification or explanation for the difference",
            "quantities reported before buffer credit deductions",
            "comparison by vintage period",
        ],
        "examples": [
            "Ex-ante estimated reductions: 130,000 tCO2e. Achieved reductions: 125,000 tCO2e. Difference: -3.8%. The difference is due to lower-than-expected wind speeds during Q3 2022.",
        ],
        "failure_modes": [
            "comparison table missing",
            "percentage difference not calculated",
            "difference not justified or explained",
            "quantities reported after buffer deductions instead of before",
            "vintage period breakdown not provided",
            "ex-ante estimates not stated for the monitoring period",
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
