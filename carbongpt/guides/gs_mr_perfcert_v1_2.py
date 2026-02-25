"""
gs_mr_perfcert_v1_2.py — Gold Standard Monitoring Report guide
(Performance Certification v1.2).

MVP: Sections A (A.1–A.4) and B (B.1–B.3).
Designed to be extended with C–G later.
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
