"""
vcs_valver_v4_4.py — Verra VCS Joint Validation and Verification Report guide
(Template v4.4).

Full coverage: Sections 1–5 (21 subsections).
"""

GUIDE_ID = "Verra_VCS_ValVer_v4_4"

SUBSECTIONS: dict[str, dict] = {
    "1.1": {
        "title": "Objective",
        "parent_section": "Introduction",
        "must_include": [
            "statement of the objective of the validation and/or verification engagement",
            "identification of the project name and Verra project ID",
            "reference to the VCS Program rules and requirements under which the assessment is conducted",
            "whether the engagement is a validation, verification, or combined validation and verification",
        ],
        "examples": [
            "The objective of this report is to present the findings of the joint validation and verification of Project XYZ (Verra ID 1234) in accordance with the VCS Program rules.",
        ],
        "failure_modes": [
            "no clear statement of the engagement objective",
            "project name or Verra ID not identified",
            "type of engagement (validation/verification/combined) not specified",
            "no reference to VCS Program rules",
        ],
    },
    "1.2": {
        "title": "Scope and Criteria",
        "parent_section": "Introduction",
        "must_include": [
            "scope of the validation and/or verification assessment",
            "criteria against which the project was assessed (VCS Standard, methodology, applicable tools)",
            "monitoring period dates for verification (start and end dates)",
            "applicable sectoral scope(s)",
        ],
        "examples": [
            "The scope of this assessment includes validation of the project design and verification of emission reductions for the monitoring period 01/01/2022 to 31/12/2022, assessed against VCS Standard v4.5, methodology VM0050 v1.0, and applicable VCS Program requirements.",
        ],
        "failure_modes": [
            "scope of assessment not clearly defined",
            "criteria (VCS Standard version, methodology) not identified",
            "monitoring period dates missing for verification",
            "sectoral scope not stated",
        ],
    },
    "1.3": {
        "title": "Reasonableness of Assumptions and Level of Assurance",
        "parent_section": "Introduction",
        "must_include": [
            "statement on the level of assurance provided (reasonable or limited)",
            "description of inherent limitations in the validation and verification process",
            "statement on the reasonableness of assumptions, limitations, and methods used in the project",
            "reference to materiality thresholds applied",
        ],
        "examples": [
            "This verification provides a reasonable level of assurance that the reported GHG emission reductions are materially correct, applying a materiality threshold of 5% as required by VCS.",
        ],
        "failure_modes": [
            "level of assurance not stated",
            "no discussion of inherent limitations",
            "materiality threshold not referenced",
            "assumptions not assessed for reasonableness",
        ],
    },
    "1.4": {
        "title": "Summary Description of the Project",
        "parent_section": "Introduction",
        "must_include": [
            "brief description of the project activity and its GHG reduction or removal mechanism",
            "project location (country, region)",
            "project proponent name",
            "methodology applied and version",
            "project crediting period and scale",
        ],
        "examples": [
            "The project involves the distribution of improved cookstoves in rural Kenya, reducing non-renewable biomass consumption. The project applies VM0050 v1.0 and is registered under the VCS Program with a 10-year crediting period.",
        ],
        "failure_modes": [
            "description too vague without specifying the GHG reduction mechanism",
            "project location not mentioned",
            "methodology not identified",
            "crediting period or project scale not stated",
        ],
    },
    "2.1": {
        "title": "Method and Criteria",
        "parent_section": "VALIDATION AND VERIFICATION   PROCESS",
        "must_include": [
            "description of the validation and verification methods employed by the VVB",
            "criteria and standards against which the assessment was conducted",
            "reference to ISO 14064-3 or applicable auditing standards",
            "description of the audit team composition and competencies",
        ],
        "examples": [
            "The assessment was conducted in accordance with ISO 14064-3:2019 and the VCS Program Guide v4.4. The audit team comprised a lead auditor with 10 years of experience in energy efficiency projects and a technical reviewer specializing in cookstove methodologies.",
        ],
        "failure_modes": [
            "validation/verification methods not described",
            "no reference to applicable auditing standards",
            "audit team competencies not demonstrated",
            "criteria for assessment not clearly stated",
        ],
    },
    "2.2": {
        "title": "Document Review",
        "parent_section": "VALIDATION AND VERIFICATION   PROCESS",
        "must_include": [
            "list of key documents reviewed during the assessment",
            "reference to the project description or monitoring report reviewed",
            "reference to supporting evidence and data files reviewed",
            "identification of any information gaps found during document review",
        ],
        "examples": [
            "The following documents were reviewed: Project Description v3.2, Monitoring Report for MP1, emission reduction calculation spreadsheet (ER_Calc_v2.xlsx), distribution records database, and usage survey raw data files.",
        ],
        "failure_modes": [
            "no list of documents reviewed",
            "key project documents (PD, MR, calculation files) not mentioned",
            "information gaps identified but not followed up",
            "generic statement without specific document references",
        ],
    },
    "2.3": {
        "title": "Interviews",
        "parent_section": "VALIDATION AND VERIFICATION   PROCESS",
        "must_include": [
            "list of persons interviewed and their roles",
            "topics covered during interviews",
            "dates of interviews conducted",
            "summary of key information obtained from interviews",
        ],
        "examples": [
            "Interviews were conducted on 15/03/2023 with the Project Manager (Mr. A), Field Coordinator (Ms. B), and local community representatives. Topics included distribution logistics, monitoring procedures, and stakeholder engagement processes.",
        ],
        "failure_modes": [
            "no list of interviewees or their roles",
            "topics discussed not documented",
            "dates of interviews not provided",
            "interviews not conducted with relevant project personnel",
        ],
    },
    "2.4": {
        "title": "Site Visits",
        "parent_section": "VALIDATION AND VERIFICATION   PROCESS",
        "must_include": [
            "dates and locations of site visits conducted",
            "description of activities performed during the site visit",
            "observations and findings from the site visit",
            "if no site visit was conducted: justification for its omission",
        ],
        "examples": [
            "A site visit was conducted on 16-18/03/2023 to the project area in Siaya County, Kenya. Activities included inspection of cookstove installations in 30 randomly selected households, review of distribution records at the local warehouse, and observation of monitoring procedures.",
        ],
        "failure_modes": [
            "no dates or locations for site visits",
            "activities during site visit not described",
            "observations and findings not documented",
            "site visit omitted without justification",
        ],
    },
    "2.5": {
        "title": "Resolution of Findings",
        "parent_section": "VALIDATION AND VERIFICATION   PROCESS",
        "must_include": [
            "summary of all findings raised during the assessment (CARs, CLs, FARs)",
            "description of how each finding was resolved",
            "confirmation that all corrective action requests (CARs) and clarification requests (CLs) have been closed",
            "list of any forward action requests (FARs) and their required timelines",
        ],
        "examples": [
            "A total of 5 CARs and 3 CLs were raised. CAR-01: Sampling methodology not adequately documented. Resolution: Project proponent provided updated sampling report with detailed methodology. Status: Closed. All CARs and CLs have been satisfactorily resolved.",
        ],
        "failure_modes": [
            "findings raised but resolution not documented",
            "CARs or CLs still open at time of report finalization",
            "no summary of findings raised during assessment",
            "FARs not clearly identified with required timelines",
        ],
    },
    "3.1": {
        "title": "Project Details",
        "parent_section": "VALIDATION FINDINGS",
        "must_include": [
            "assessment of the accuracy and completeness of project details in the PD",
            "confirmation that the project meets VCS eligibility requirements",
            "assessment of project start date and crediting period",
            "assessment of project ownership and right to claim emission reductions",
            "findings on project location and boundary",
        ],
        "examples": [
            "The VVB confirms that the project details presented in the PD are accurate and complete. The project start date of 01/01/2020 is supported by commissioning evidence. The crediting period of 10 years (01/01/2020 - 31/12/2029) is consistent with VCS rules for this project type.",
        ],
        "failure_modes": [
            "no assessment of project eligibility",
            "project start date not verified against evidence",
            "crediting period not checked for compliance with VCS rules",
            "ownership and right to claim reductions not assessed",
            "project boundary not verified",
        ],
    },
    "3.2": {
        "title": "Project Activity Instances in Grouped Projects",
        "parent_section": "VALIDATION FINDINGS",
        "must_include": [
            "assessment of project activity instances included in the group",
            "verification that inclusion criteria are clearly defined and properly applied",
            "assessment of geographic scope and boundaries for grouped projects",
            "if not a grouped project: explicit statement that this section is not applicable",
        ],
        "examples": [
            "The project includes 12 VPA instances across 3 regions. The VVB confirms that each VPA meets the defined inclusion criteria and falls within the approved geographic boundaries.",
            "This section is not applicable as the project is not a grouped project.",
        ],
        "failure_modes": [
            "no assessment of inclusion criteria for grouped projects",
            "VPA instances not individually evaluated",
            "geographic boundaries not verified",
            "section left blank for grouped projects",
            "no statement of non-applicability for non-grouped projects",
        ],
    },
    "3.3": {
        "title": "Safeguards",
        "parent_section": "VALIDATION FINDINGS",
        "must_include": [
            "assessment of the project's compliance with VCS safeguards requirements",
            "evaluation of stakeholder engagement and consultation processes",
            "assessment of risks to stakeholders and the environment",
            "assessment of respect for human rights and equity",
            "assessment of ecosystem health impacts",
        ],
        "examples": [
            "The VVB confirms that the project has conducted stakeholder consultations in accordance with VCS requirements. Environmental and social risks have been identified and appropriate mitigation measures are in place.",
        ],
        "failure_modes": [
            "no assessment of safeguards compliance",
            "stakeholder engagement not evaluated",
            "environmental and social risks not assessed",
            "human rights considerations not addressed",
            "ecosystem health impacts not evaluated",
        ],
    },
    "3.4": {
        "title": "Application of Methodology",
        "parent_section": "VALIDATION FINDINGS",
        "must_include": [
            "confirmation that the selected methodology is appropriate for the project activity",
            "assessment of applicability conditions and whether the project meets them",
            "assessment of the baseline scenario determination",
            "assessment of additionality demonstration",
            "evaluation of the monitoring plan design",
            "assessment of any methodology deviations and their justification",
        ],
        "examples": [
            "The VVB confirms that VM0050 v1.0 is applicable to this project. All applicability conditions are met. The baseline scenario is correctly identified as continued use of traditional three-stone fires. Additionality has been demonstrated through the investment analysis and barrier analysis.",
        ],
        "failure_modes": [
            "no confirmation that methodology is appropriate",
            "applicability conditions not individually assessed",
            "baseline scenario determination not evaluated",
            "additionality assessment not reviewed",
            "monitoring plan not assessed for compliance with methodology",
            "methodology deviations not evaluated",
        ],
    },
    "3.5": {
        "title": "Non-Permanence Risk Analysis",
        "parent_section": "VALIDATION FINDINGS",
        "must_include": [
            "assessment of the non-permanence risk analysis (for AFOLU projects)",
            "evaluation of the risk rating and buffer pool contribution",
            "if not an AFOLU project: explicit statement that this section is not applicable",
        ],
        "examples": [
            "The VVB has assessed the non-permanence risk analysis and confirms a combined risk rating of 15%, resulting in a buffer pool contribution of 15% of verified emission reductions.",
            "This section is not applicable as the project is not an AFOLU project.",
        ],
        "failure_modes": [
            "non-permanence risk not assessed for AFOLU projects",
            "risk rating or buffer pool contribution not evaluated",
            "no statement of non-applicability for non-AFOLU projects",
            "risk factors not individually assessed",
        ],
    },
    "4.1": {
        "title": "Project Implementation Status",
        "parent_section": "VERIFICATION FINDINGS",
        "must_include": [
            "assessment of the actual implementation of the project activity",
            "comparison of actual implementation against the validated project design",
            "identification of any deviations from the registered PD",
            "assessment of whether deviations are material and properly justified",
            "confirmation that the project is operational during the monitoring period",
        ],
        "examples": [
            "The VVB confirms that the project has been implemented in accordance with the registered PD. As of the end of the monitoring period, 18,500 cookstoves have been distributed. One minor deviation was identified regarding the distribution timeline, which does not materially affect emission reductions.",
        ],
        "failure_modes": [
            "no assessment of actual implementation status",
            "implementation not compared against validated design",
            "deviations not identified or assessed for materiality",
            "no confirmation that project was operational during the monitoring period",
        ],
    },
    "4.2": {
        "title": "Accuracy of Reduction and Removal Calculations",
        "parent_section": "VERIFICATION FINDINGS",
        "must_include": [
            "assessment of the accuracy of emission reduction or removal calculations",
            "verification that formulae applied are consistent with the methodology",
            "verification of input parameter values against source data",
            "cross-checking of calculation spreadsheets for mathematical accuracy",
            "confirmation of the final verified emission reductions or removals quantity",
        ],
        "examples": [
            "The VVB has recalculated the emission reductions using independently sourced data and confirmed the reported figure of 35,280 tCO2e. All formulae are consistent with VM0050 v1.0. Input parameters were traced to supporting evidence.",
        ],
        "failure_modes": [
            "no independent recalculation performed",
            "formulae not checked against methodology requirements",
            "input parameters not traced to source data",
            "mathematical errors not identified or reported",
            "final verified quantity not clearly stated",
        ],
    },
    "4.3": {
        "title": "Quality of Evidence to Determine Reductions and Removals",
        "parent_section": "VERIFICATION FINDINGS",
        "must_include": [
            "assessment of the quality and reliability of evidence supporting claimed reductions",
            "evaluation of data management systems and QA/QC procedures",
            "assessment of sampling approaches and their statistical validity",
            "evaluation of the monitoring report's completeness and accuracy",
            "identification of any data quality issues and their resolution",
        ],
        "examples": [
            "The evidence supporting the claimed emission reductions is considered reliable. Data management systems include automated validation checks. The sampling approach follows a stratified random design achieving 95/10 confidence/precision. Minor data quality issues were identified and resolved through CARs.",
        ],
        "failure_modes": [
            "no assessment of evidence quality",
            "data management systems not evaluated",
            "sampling validity not assessed",
            "data quality issues identified but not resolved",
            "monitoring report completeness not evaluated",
        ],
    },
    "5.1": {
        "title": "Validation and Verification Summary",
        "parent_section": "VALIDATION AND VERIFICATION OPINION",
        "must_include": [
            "summary of the overall validation and verification findings",
            "statement on the total verified emission reductions or removals",
            "summary of material findings and their resolution",
            "confirmation that all required documentation has been reviewed",
        ],
        "examples": [
            "Based on the validation and verification assessment, the VVB has reviewed all required documentation and resolved all material findings. The total verified emission reductions for the monitoring period are 35,280 tCO2e.",
        ],
        "failure_modes": [
            "no summary of overall findings",
            "verified emission reductions quantity not stated",
            "material findings not summarized",
            "incomplete review of documentation not acknowledged",
        ],
    },
    "5.2": {
        "title": "Validation Conclusion",
        "parent_section": "VALIDATION AND VERIFICATION OPINION",
        "must_include": [
            "formal validation opinion (positive, negative, or qualified)",
            "statement that the project design complies with VCS Program requirements",
            "confirmation that the methodology has been correctly applied",
            "identification of any conditions or qualifications on the validation opinion",
        ],
        "examples": [
            "Based on the assessment, the VVB provides a positive validation opinion. The project design is in conformance with the VCS Standard v4.5 and all applicable VCS Program requirements. The methodology VM0050 v1.0 has been correctly applied.",
        ],
        "failure_modes": [
            "no formal validation opinion stated",
            "compliance with VCS requirements not confirmed",
            "methodology application not assessed in conclusion",
            "conditions or qualifications not clearly identified",
        ],
    },
    "5.3": {
        "title": "Verification conclusion",
        "parent_section": "VALIDATION AND VERIFICATION OPINION",
        "must_include": [
            "formal verification opinion (positive, negative, or qualified)",
            "statement of the verified GHG emission reductions or removals for the monitoring period",
            "confirmation that the monitoring report is materially correct",
            "monitoring period start and end dates",
            "identification of any conditions or qualifications on the verification opinion",
        ],
        "examples": [
            "Based on the assessment, the VVB provides a positive verification opinion. The GHG emission reductions for the monitoring period 01/01/2022 to 31/12/2022 are verified as 35,280 tCO2e. The monitoring report is free from material misstatement.",
        ],
        "failure_modes": [
            "no formal verification opinion stated",
            "verified emission reductions quantity not stated",
            "monitoring period dates not specified",
            "material correctness of monitoring report not confirmed",
            "conditions or qualifications not clearly identified",
        ],
    },
    "5.4": {
        "title": "Ex-ante vs Ex-post ERR Comparison",
        "parent_section": "VALIDATION AND VERIFICATION OPINION",
        "must_include": [
            "comparison of ex-ante estimated emission reductions with ex-post verified reductions",
            "explanation of significant variances between estimated and actual reductions",
            "assessment of whether variances indicate systematic issues",
            "table or summary showing estimated vs verified quantities",
        ],
        "examples": [
            "Ex-ante estimated reductions for this monitoring period: 32,000 tCO2e. Ex-post verified reductions: 35,280 tCO2e (10.3% variance). The variance is attributable to higher than expected adoption rates and does not indicate systematic issues with the quantification approach.",
        ],
        "failure_modes": [
            "no comparison of ex-ante vs ex-post values",
            "significant variances not explained",
            "no assessment of whether variances are systematic",
            "estimated and verified quantities not clearly presented",
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
