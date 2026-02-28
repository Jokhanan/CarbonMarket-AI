import hashlib
import logging
import os
import re
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

REPO_DIR = Path(__file__).resolve().parent.parent.parent / "document_repository"
REPO_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "CarbonGPT/1.0 (compliance-research-tool)"
RATE_LIMIT_DELAY = 2


def _download_file(url: str, dest_path: Path) -> bool:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=60,
            stream=True,
        )
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.warning("Failed to download %s: %s", url, e)
        return False


def _content_hash(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_already_stored(reference_id: str) -> dict | None:
    try:
        from carbongpt.repository.store import find_document_by_reference
        return find_document_by_reference(reference_id)
    except Exception:
        return None


VERRA_PROGRAM_DOCS = [
    ("VCS_STANDARD_V4_7", "VCS Standard v4.7",
     "https://verra.org/wp-content/uploads/2024/04/VCS-Standard-v4.7-FINAL-4.15.24.pdf",
     "standard_text"),
    ("VCS_PROGRAM_GUIDE_V4_2", "VCS Program Guide v4.2",
     "https://verra.org/wp-content/uploads/2022/06/VCS-Program-Guide-v4.2.pdf",
     "guidance"),
    ("VCS_REG_ISSUANCE_V4_1", "VCS Registration and Issuance Process v4.1",
     "https://verra.org/wp-content/uploads/2022/10/Registration-and-Issuance-Process_v4.1.pdf",
     "guidance"),
    ("VCS_METH_REQUIREMENTS_V4_4", "VCS Methodology Requirements v4.4",
     "https://verra.org/wp-content/uploads/2023/08/VCS-Methodology-Requirements-v4.4.pdf",
     "guidance"),
    ("VCS_AFOLU_NONPERM_V4_0", "AFOLU Non-Permanence Risk Tool v4.0",
     "https://verra.org/wp-content/uploads/2019/09/AFOLU_Non-Permanence_Risk-Tool_v4.0.pdf",
     "tool"),
]

VERRA_SEED_PROJECTS = [
    (934, "Kasigau Corridor REDD+ Phase II"),
    (1360, "Cordillera Azul National Park REDD+"),
    (612, "Rimba Raya Biodiversity Reserve REDD+"),
    (985, "Southern Cardamom REDD+"),
    (1396, "Katingan Peatland Restoration and Conservation"),
    (944, "Kulera Landscape REDD+ (Malawi)"),
    (2250, "Kariba REDD+ (Zimbabwe)"),
    (1650, "Mai Ndombe REDD+ (DRC)"),
    (1764, "Madre de Dios Amazon REDD+ (Peru)"),
    (1566, "Alto Mayo Conservation Initiative REDD+ (Peru)"),
]

DOC_TYPES_TO_DOWNLOAD = {"example_pdd", "example_mr", "example_fvr", "example_valver"}


def _classify_verra_doc(filename: str, doc_name: str) -> str:
    fn = filename.lower()
    dn = doc_name.lower()
    combined = fn + " " + dn
    if any(k in combined for k in ["monit_rep", "monitoring_rep", "monitoring report", "mon_rep", "_mr_", "monit rep"]):
        return "example_mr"
    if any(k in combined for k in ["verif_rep", "verification_rep", "verification report", "verif rep", "ver_rep", "vcr_", "vcs_ccb_verif"]):
        return "example_fvr"
    if any(k in combined for k in ["valid_rep", "validation_rep", "validation report", "valid rep", "val_rep", "fvr"]):
        return "example_valver"
    if any(k in combined for k in ["proj_desc", "project_desc", "project description", "pdd", "project design"]):
        return "example_pdd"
    if any(k in combined for k in ["verif_sta", "verification_sta", "valid_sta", "validation_sta"]):
        return "example_valver"
    if any(k in combined for k in ["iss_rep", "issuance_rep", "pp_iss", "pp_reg"]):
        return "example_other"
    if any(k in combined for k in [".xlsx", ".xls", "calculation", "er_calc", "emission"]):
        return "example_other"
    return "example_other"


def _fetch_verra_registry_project_docs(project_id: int, project_name: str) -> list[dict]:
    docs = []
    seen_urls: set[str] = set()
    detail_url = f"https://registry.verra.org/app/projectDetail/VCS/{project_id}"
    try:
        resp = requests.get(detail_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        html = resp.text

        doc_pattern = re.compile(
            r'\[([^\]]*\.(?:pdf|docx|xlsx)[^\]]*)\]\((https://registry\.verra\.org/mymodule/ProjectDoc/Project_ViewFile\.asp\?[^)]+)\)',
            re.IGNORECASE,
        )
        link_pattern = re.compile(
            r'href="(https://registry\.verra\.org/mymodule/ProjectDoc/Project_ViewFile\.asp\?[^"]+)"[^>]*>([^<]*)',
            re.IGNORECASE,
        )
        bare_pattern = re.compile(
            r'href="([^"]*(?:\.pdf|\.docx|\.xlsx)[^"]*)"',
            re.IGNORECASE,
        )

        matches = []
        for m in doc_pattern.finditer(html):
            matches.append((m.group(2), m.group(1)))
        for m in link_pattern.finditer(html):
            matches.append((m.group(1), m.group(2)))
        for m in bare_pattern.finditer(html):
            url = m.group(1)
            if not url.startswith("http"):
                url = f"https://registry.verra.org{url}"
            fname = url.rsplit("/", 1)[-1].split("?")[0]
            matches.append((url, fname))

        for url, doc_name in matches:
            if url in seen_urls:
                continue
            seen_urls.add(url)

            doc_name_clean = doc_name.strip().replace("\\", "")
            cat = _classify_verra_doc(doc_name_clean, doc_name_clean)

            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', doc_name_clean[:40]).upper()
            doc_code = f"VERRA_REG_{project_id}_{safe_name}"
            title = f"VCS {project_id} {project_name} - {doc_name_clean.replace('.pdf', '').replace('.xlsx', '').replace('_', ' ').title()}"

            docs.append({
                "code": doc_code[:80],
                "title": title[:120],
                "pdf_url": url,
                "source": "verra",
                "category": cat,
                "project_id": project_id,
            })
    except Exception as e:
        logger.warning("Failed to fetch Verra registry project %d: %s", project_id, e)

    return docs


def discover_verra_project_ids(max_projects: int = 200, id_range: tuple = (1, 4500)) -> list[tuple[int, str]]:
    projects = []
    start_id, end_id = id_range
    step = max(1, (end_id - start_id) // (max_projects * 3))
    probed = 0
    for pid in range(start_id, end_id, step):
        if len(projects) >= max_projects:
            break
        try:
            url = f"https://registry.verra.org/app/projectDetail/VCS/{pid}"
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
            if resp.status_code != 200:
                continue
            html = resp.text
            if "Project_ViewFile" not in html:
                continue
            name_match = re.search(r'<h[12][^>]*>([^<]+)</h[12]>', html)
            if not name_match:
                name_match = re.search(r'<title>([^<]+)</title>', html)
            name = name_match.group(1).strip()[:100] if name_match else f"VCS Project {pid}"
            projects.append((pid, name))
            probed += 1
            if probed % 10 == 0:
                logger.info("Discovered %d Verra projects so far (probed up to ID %d)", len(projects), pid)
        except Exception:
            pass
        time.sleep(0.5)

    logger.info("Discovered %d Verra projects with documents in ID range %d-%d", len(projects), start_id, end_id)
    return projects


def discover_gs_project_ids(max_projects: int = 200, id_range: tuple = (1, 6000)) -> list[tuple[int, str, str]]:
    projects = []
    start_id, end_id = id_range
    step = max(1, (end_id - start_id) // (max_projects * 3))
    for pid in range(start_id, end_id, step):
        if len(projects) >= max_projects:
            break
        try:
            url = f"https://registry.goldstandard.org/projects/details/{pid}"
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
            if resp.status_code != 200:
                continue
            html = resp.text
            gs_id_match = re.search(r'GS\s*ID\s*[\n\r\s]*(\d+)', html)
            if not gs_id_match:
                continue
            gs_id = gs_id_match.group(1)
            name_match = re.search(r'<h[12][^>]*>([^<]+)</h[12]>', html)
            if not name_match:
                name_match = re.search(r'<title>([^<]+)</title>', html)
            name = name_match.group(1).strip()[:100] if name_match else f"GS Project {gs_id}"
            name = re.sub(r'\s*\(\d+\)\s*$', '', name).strip()
            assurance_match = re.search(r'assurance-platform\.goldstandard\.org/project-documents/(GS\d+)', html)
            assurance_id = assurance_match.group(1) if assurance_match else f"GS{gs_id}"
            projects.append((pid, name, assurance_id))
            if len(projects) % 10 == 0:
                logger.info("Discovered %d Gold Standard projects so far (probed up to ID %d)", len(projects), pid)
        except Exception:
            pass
        time.sleep(0.5)

    logger.info("Discovered %d Gold Standard projects in ID range %d-%d", len(projects), start_id, end_id)
    return projects


def _classify_gs_doc(doc_name: str) -> str:
    dn = doc_name.lower()
    if any(k in dn for k in ["monitoring report", "mr_", "monitoring_report", "monit"]):
        return "example_mr"
    if any(k in dn for k in ["verification report", "vcr", "verification_report", "verif"]):
        return "example_fvr"
    if any(k in dn for k in ["validation report", "validation_report", "fvr", "val_rep"]):
        return "example_valver"
    if any(k in dn for k in ["pdd", "project design", "project_design", "gs4gg_pdd", "gs pdd"]):
        return "example_pdd"
    if any(k in dn for k in [".xlsx", ".xls", "er sheet", "er_sheet", "er-", "emission"]):
        return "example_other"
    return "example_other"


def _fetch_gs_project_docs(registry_id: int, project_name: str, assurance_id: str) -> list[dict]:
    docs = []
    seen_names: set[str] = set()
    assurance_url = f"https://assurance-platform.goldstandard.org/project-documents/{assurance_id}"
    try:
        resp = requests.get(assurance_url, headers={"User-Agent": USER_AGENT}, timeout=20)
        if resp.status_code != 200:
            return docs
        html = resp.text

        doc_pattern = re.compile(
            r'(?:Required|Other|Confidential)\s*\(([^)]+\.(?:pdf|xlsx|docx))\)',
            re.IGNORECASE,
        )
        for m in doc_pattern.finditer(html):
            doc_name = m.group(1).strip()
            if doc_name in seen_names:
                continue
            seen_names.add(doc_name)

            cat = _classify_gs_doc(doc_name)
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', doc_name[:40]).upper()
            doc_code = f"GS_REG_{assurance_id}_{safe_name}"
            title = f"GS {assurance_id} {project_name} - {doc_name.replace('.pdf', '').replace('.xlsx', '')}"

            download_url = f"{assurance_url}#download:{doc_name}"

            docs.append({
                "code": doc_code[:80],
                "title": title[:120],
                "pdf_url": download_url,
                "source": "goldstandard",
                "category": cat,
                "project_id": registry_id,
                "assurance_id": assurance_id,
                "doc_name": doc_name,
                "download_available": False,
            })
    except Exception as e:
        logger.warning("Failed to fetch GS project docs for %s: %s", assurance_id, e)

    return docs


def fetch_verra_methodology_list_api() -> list[dict]:
    methodologies = []
    seen_codes: set[str] = set()
    try:
        for page in range(1, 20):
            url = f"https://verra.org/wp-json/wp/v2/methodologies?per_page=100&page={page}"
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
            if resp.status_code != 200:
                break
            items = resp.json()
            if not items:
                break

            for item in items:
                slug = item.get("slug", "")
                title_raw = item.get("title", {}).get("rendered", "")
                link = item.get("link", "")

                title_clean = re.sub(r'<[^>]+>', '', title_raw).strip()
                title_clean = title_clean.replace("&#8211;", "-").replace("&#8217;", "'").replace("&amp;", "&")

                code = None
                for pattern in [r'(vmr\d{4})', r'(vm\d{4})']:
                    m = re.search(pattern, slug, re.IGNORECASE)
                    if m:
                        code = m.group(1).upper()
                        break

                if not code:
                    m = re.search(r'(VMR\d{4}|VM\d{4})', title_clean)
                    if m:
                        code = m.group(1)

                if not code or code in seen_codes:
                    continue

                seen_codes.add(code)
                methodologies.append({
                    "code": code,
                    "detail_url": link,
                    "title": title_clean[:120],
                    "source": "verra",
                    "category": "methodology",
                })

            time.sleep(RATE_LIMIT_DELAY)
    except Exception as e:
        logger.warning("WordPress API failed, falling back to HTML scrape: %s", e)

    return methodologies


def fetch_verra_methodology_list() -> list[dict]:
    api_results = fetch_verra_methodology_list_api()
    if len(api_results) > 10:
        logger.info("Found %d Verra methodologies via WordPress API", len(api_results))
        return api_results

    url = "https://verra.org/program-methodology/vcs-program-standard/vcs-program-methodologies-active/"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        logger.error("Failed to fetch Verra methodology list: %s", e)
        return api_results if api_results else []

    methodologies = list(api_results)
    existing_codes = {m["code"] for m in methodologies}

    link_pattern = re.compile(
        r'href="(https://verra\.org/methodologies/(vm\d{4})[^"]*)"',
        re.IGNORECASE,
    )

    for match in link_pattern.finditer(html):
        detail_url = match.group(1)
        code = match.group(2).upper()
        if code not in existing_codes:
            existing_codes.add(code)
            methodologies.append({
                "code": code,
                "detail_url": detail_url,
                "source": "verra",
                "category": "methodology",
            })

    logger.info("Found %d Verra methodologies total", len(methodologies))
    return methodologies


def fetch_verra_methodology_pdf(detail_url: str) -> dict | None:
    try:
        resp = requests.get(detail_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        logger.warning("Failed to fetch methodology detail page %s: %s", detail_url, e)
        return None

    pdf_pattern = re.compile(
        r'href="(https://verra\.org/[^"]*\.pdf)"',
        re.IGNORECASE,
    )
    title_pattern = re.compile(r'<h1[^>]*>([^<]+)</h1>', re.IGNORECASE)

    title_match = title_pattern.search(html)
    title = title_match.group(1).strip() if title_match else "Unknown Methodology"

    pdf_urls = []
    for m in pdf_pattern.finditer(html):
        pdf_url = m.group(1)
        if "methodology" in pdf_url.lower() or "vm0" in pdf_url.lower() or "vmr" in pdf_url.lower():
            pdf_urls.append(pdf_url)

    if not pdf_urls:
        for m in pdf_pattern.finditer(html):
            pdf_urls.append(m.group(1))

    if not pdf_urls:
        return None

    return {
        "title": title,
        "pdf_url": pdf_urls[0],
        "all_pdf_urls": pdf_urls,
    }


CDM_METHODOLOGY_PDFS = {
    "booklet": (
        "CDM Methodology Booklet (all approved methodologies)",
        "https://cdm.unfccc.int/methodologies/documentation/meth_booklet.pdf",
    ),
}

CDM_TOOL_PDFS = [
    ("TOOL01", "Tool for demonstration and assessment of additionality",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-01-v7.0.0.pdf"),
    ("TOOL02", "Combined tool to identify baseline scenario and demonstrate additionality",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-02-v7.0.pdf"),
    ("TOOL03", "Tool to calculate CO2 emissions from fossil fuel combustion",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-03-v3.pdf"),
    ("TOOL04", "Emissions from solid waste disposal sites",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-04-v8.0.0.pdf"),
    ("TOOL05", "Baseline/project/leakage emissions from electricity consumption",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-05-v3.0.pdf"),
    ("TOOL07", "Tool to calculate emission factor for electricity system",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-07-v7.0.pdf"),
    ("TOOL10", "Tool to determine the remaining lifetime of equipment",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-10-v1.pdf"),
    ("TOOL12", "Project and leakage emissions from transportation of freight",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-12-v1.1.0.pdf"),
    ("TOOL14", "Project and leakage emissions from composting",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-14-v1.pdf"),
    ("TOOL19", "Demonstration of additionality of microscale project activities",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-19-v10.0.pdf"),
    ("TOOL21", "Demonstration of additionality of small-scale project activities",
     "https://cdm.unfccc.int/methodologies/PAmethodologies/tools/am-tool-21-v13.0.pdf"),
]

CDM_PROGRAM_DOCS = [
]


def fetch_cdm_methodology_list() -> list[dict]:
    methodologies = []

    booklet_title, booklet_url = CDM_METHODOLOGY_PDFS["booklet"]
    methodologies.append({
        "code": "CDM_BOOKLET",
        "title": booklet_title,
        "detail_url": booklet_url,
        "pdf_url": booklet_url,
        "source": "cdm",
        "category": "methodology",
    })

    for code, title, pdf_url in CDM_TOOL_PDFS:
        methodologies.append({
            "code": f"CDM_{code}",
            "title": f"CDM {title}",
            "detail_url": pdf_url,
            "pdf_url": pdf_url,
            "source": "cdm",
            "category": "methodology",
        })

    for code, title, pdf_url, category in CDM_PROGRAM_DOCS:
        methodologies.append({
            "code": code,
            "title": title,
            "detail_url": pdf_url,
            "pdf_url": pdf_url,
            "source": "cdm",
            "category": category,
        })

    try:
        tools_url = "https://cdm.unfccc.int/methodologies/PAmethodologies/approved"
        resp = requests.get(tools_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        html = resp.text

        tool_pattern = re.compile(
            r'href="(https://cdm\.unfccc\.int/methodologies/PAmethodologies/tools/[^"]*\.pdf)',
            re.IGNORECASE,
        )
        for match in tool_pattern.finditer(html):
            pdf_url = match.group(1).split("/history_view")[0]
            filename = pdf_url.rsplit("/", 1)[-1]
            tool_code = filename.replace(".pdf", "").replace("-", "_").upper()[:30]
            ref_code = f"CDM_{tool_code}"
            if ref_code not in [m["code"] for m in methodologies]:
                title = filename.replace(".pdf", "").replace("-", " ").replace("_", " ").title()
                methodologies.append({
                    "code": ref_code,
                    "title": f"CDM {title}",
                    "detail_url": pdf_url,
                    "pdf_url": pdf_url,
                    "source": "cdm",
                    "category": "methodology",
                })
    except Exception as e:
        logger.warning("Failed to fetch CDM tools: %s", e)

    logger.info("Found %d CDM documents", len(methodologies))
    return methodologies


GS_KNOWN_METHODOLOGY_PDFS = [
    ("GS_EE_ICS_Metered_Cooking", "Methodology for Metered and Measured Energy Cooking Devices v1.1",
     "https://globalgoals.goldstandard.org/standards/431_V1.1_EE_ICS_Methodology-for-Metered-and-Measured-Energy-Cooking-Devices.pdf"),
    ("GS_LUF_AR_GHG", "Afforestation/Reforestation Methodology v2.0",
     "https://globalgoals.goldstandard.org/standards/403_V2.0_LUF_AR-Methodology-GHGs-emission-reduction-and-Sequestration-Methodology.pdf"),
    ("GS_BCFW_Mangroves", "Sustainable Management of Mangroves v1.0",
     "https://globalgoals.goldstandard.org/standards/443_V1.0_BCFW_Sustainable-Management-of-Mangroves.pdf"),
    ("GS_LUF_SOC", "Soil Organic Carbon Framework Methodology v1.0",
     "https://globalgoals.goldstandard.org/standards/402_V1.0_LUF_AGR_FM_Soil-Organic-Carbon-Framework-Methodolgy.pdf"),
    ("GS_WASH_Water", "Water Access and WASH Methodology v1.0",
     "https://globalgoals.goldstandard.org/standards/425_V1.0_WBCs_Wash_Water-Access-and-Water-Sanitation-and-Hygiene-WASH-Projects.pdf"),
    ("GS_Meth_Approval", "Methodology Approval Procedure v2.0",
     "https://globalgoals.goldstandard.org/standards/401_V2.0_SDGIQ_Methodology-approval-procedure.pdf"),
    ("GS_Meth_Requirements", "Requirements for Methodology Development v1.0",
     "https://globalgoals.goldstandard.org/standards/446_V1.0_Requirements-for-methodology-development.pdf"),
    ("GS_Meth_Status_Update", "Methodology Status Update v1.1 (2024)",
     "https://globalgoals.goldstandard.org/standards/RU_2024_v1.1_Methodology-status-update.pdf"),
    ("GS_Additionality_Policy", "Determining Additionality of a Policy v1.0",
     "https://globalgoals.goldstandard.org/standards/442_V1.0_Determining-Additionality-of-a-Policy.pdf"),
    ("GS_EE_ICS_Simplified_Cooking", "Reduced Emissions from Cooking and Heating - TPDDTEC v4.0",
     "https://globalgoals.goldstandard.org/standards/407_V4.0_EE_ICS_Reduced-Emissions-from-Cooking-and-Heating-TPDDTEC.pdf"),
]

GS_PROGRAM_DOCS = [
    ("GS_PRINCIPLES_REQUIREMENTS", "Gold Standard for the Global Goals - Principles and Requirements v2.0",
     "https://globalgoals.goldstandard.org/standards/101_V2.0_PAR_Principles-Requirements.pdf",
     "standard_text"),
    ("GS_SAFEGUARDING_PRINCIPLES", "Gold Standard Safeguarding Principles and Requirements v1.2",
     "https://globalgoals.goldstandard.org/standards/103_V1.2_PAR_Safeguarding-Principles-Requirements.pdf",
     "guidance"),
    ("GS_STAKEHOLDER_CONSULTATION", "Gold Standard Stakeholder Consultation and Engagement Requirements v1.2",
     "https://globalgoals.goldstandard.org/standards/102_V1.2_PAR_Stakeholder-Consultation-Requirements.pdf",
     "guidance"),
    ("GS_GHG_OUTCOMES", "Gold Standard GHG Emissions Reduction and Sequestration Product Requirements v2.0",
     "https://globalgoals.goldstandard.org/standards/104_V2.0_PAR_GHG-Emissions-Reduction-Sequestration-Product-Requirements.pdf",
     "guidance"),
    ("GS_SDG_IMPACT", "Gold Standard SDG Impact Quantification Requirements v1.0",
     "https://globalgoals.goldstandard.org/standards/105_V1.0_PAR_SDG-Impact-Quantification.pdf",
     "guidance"),
    ("GS_ACTIVITY_REQUIREMENTS", "Gold Standard Activity Requirements v2.0",
     "https://globalgoals.goldstandard.org/standards/110_V2.0_PAR_Activity-Requirements.pdf",
     "guidance"),
    ("GS_VVB_REQUIREMENTS", "Gold Standard VVB Requirements v1.2",
     "https://globalgoals.goldstandard.org/standards/111_V1.2_PAR_VVB-Requirements.pdf",
     "guidance"),
    ("GS_POA_REQUIREMENTS", "Gold Standard Programme of Activities Requirements v2.0",
     "https://globalgoals.goldstandard.org/standards/109_V2.0_PAR_POA-Requirements.pdf",
     "guidance"),
    ("GS_CREDITING_PERIOD", "Gold Standard Crediting Period and Project Lifetime v1.0",
     "https://globalgoals.goldstandard.org/standards/107_V1.0_PAR_Crediting-period-and-project-lifetime.pdf",
     "guidance"),
]

GS_TEMPLATE_DOCS = [
    ("GS_MR_GUIDE", "Gold Standard Monitoring Report Guide v1.1",
     "https://globalgoals.goldstandard.org/standards/TGuide-PerfCert_V1.1-Monitoring-Report.pdf",
     "template"),
    ("GS_PDD_GUIDE", "Gold Standard Project Design Document Guide v1.4",
     "https://globalgoals.goldstandard.org/standards/TGuide-PreReview_V1.4-Project-Design-Document.pdf",
     "template"),
    ("GS_VALIDATION_GUIDE", "Gold Standard Validation Report Guide v1.0",
     "https://globalgoals.goldstandard.org/standards/TGuide-CertDesign_V1.0-Validation-Report.pdf",
     "template"),
    ("GS_VERIFICATION_GUIDE", "Gold Standard Verification Report Guide v1.0",
     "https://globalgoals.goldstandard.org/standards/TGuide-PerfCert_V1.0-Verification-Report.pdf",
     "template"),
]


def fetch_gs_methodology_list() -> list[dict]:
    methodologies = []

    for code, title, pdf_url in GS_KNOWN_METHODOLOGY_PDFS:
        methodologies.append({
            "code": code,
            "title": title,
            "detail_url": pdf_url,
            "pdf_url": pdf_url,
            "source": "goldstandard",
            "category": "methodology",
        })

    for code, title, pdf_url, category in GS_PROGRAM_DOCS:
        methodologies.append({
            "code": code,
            "title": title,
            "detail_url": pdf_url,
            "pdf_url": pdf_url,
            "source": "goldstandard",
            "category": category,
        })

    for code, title, pdf_url, category in GS_TEMPLATE_DOCS:
        methodologies.append({
            "code": code,
            "title": title,
            "detail_url": pdf_url,
            "pdf_url": pdf_url,
            "source": "goldstandard",
            "category": category,
        })

    gs_standards_url = "https://globalgoals.goldstandard.org/methodology-standards-paris-agreement-alignment-and-other-updates/"
    try:
        resp = requests.get(gs_standards_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        html = resp.text

        pdf_pattern = re.compile(
            r'href="(https://globalgoals\.goldstandard\.org/standards/[^"]*\.pdf)"',
            re.IGNORECASE,
        )
        for match in pdf_pattern.finditer(html):
            pdf_url = match.group(1)
            filename = pdf_url.rsplit("/", 1)[-1]
            code = filename.replace(".pdf", "").replace("-", "_")[:40]
            if code not in [m["code"] for m in methodologies]:
                title = filename.replace(".pdf", "").replace("-", " ").replace("_", " ")
                methodologies.append({
                    "code": code,
                    "title": title,
                    "detail_url": pdf_url,
                    "pdf_url": pdf_url,
                    "source": "goldstandard",
                    "category": "methodology",
                })
    except Exception as e:
        logger.warning("Failed to fetch additional GS methodologies: %s", e)

    logger.info("Found %d Gold Standard documents", len(methodologies))
    return methodologies


def fetch_verra_program_docs() -> list[dict]:
    docs = []
    for code, title, url, category in VERRA_PROGRAM_DOCS:
        file_type = "docx" if url.endswith(".docx") else "pdf"
        docs.append({
            "code": code,
            "title": title,
            "detail_url": url,
            "pdf_url": url,
            "source": "verra",
            "category": category,
            "file_type": file_type,
        })
    return docs


def fetch_verra_registry_docs(
    max_projects: int = 10,
    discover: bool = False,
    doc_types: set[str] | None = None,
) -> list[dict]:
    all_docs = []
    if doc_types is None:
        doc_types = DOC_TYPES_TO_DOWNLOAD

    if discover and max_projects > len(VERRA_SEED_PROJECTS):
        projects = discover_verra_project_ids(max_projects=max_projects)
    else:
        projects = VERRA_SEED_PROJECTS[:max_projects]

    for project_id, project_name in projects:
        time.sleep(RATE_LIMIT_DELAY)
        docs = _fetch_verra_registry_project_docs(project_id, project_name)
        relevant = [d for d in docs if d["category"] in doc_types]
        all_docs.extend(relevant)
        logger.info(
            "Found %d docs (%d relevant) for Verra project %d (%s)",
            len(docs), len(relevant), project_id, project_name,
        )
    return all_docs


def fetch_gs_registry_docs(
    max_projects: int = 10,
    discover: bool = False,
    doc_types: set[str] | None = None,
) -> list[dict]:
    all_docs = []
    if doc_types is None:
        doc_types = DOC_TYPES_TO_DOWNLOAD

    projects = discover_gs_project_ids(max_projects=max_projects)

    for registry_id, project_name, assurance_id in projects:
        time.sleep(RATE_LIMIT_DELAY)
        docs = _fetch_gs_project_docs(registry_id, project_name, assurance_id)
        relevant = [d for d in docs if d["category"] in doc_types]
        all_docs.extend(relevant)
        logger.info(
            "Found %d docs (%d relevant) for GS project %s (%s)",
            len(docs), len(relevant), assurance_id, project_name,
        )
    return all_docs


def sync_methodologies(
    sources: list[str] = None,
    max_per_source: int = 50,
    dry_run: bool = False,
    include_program_docs: bool = True,
    include_registry_projects: bool = False,
    max_registry_projects: int = 5,
    discover_projects: bool = False,
) -> dict:
    if sources is None:
        sources = ["verra", "cdm", "goldstandard"]

    results = {
        "sources_checked": sources,
        "total_found": 0,
        "already_stored": 0,
        "newly_downloaded": 0,
        "ingestion_started": 0,
        "errors": 0,
        "skipped_no_download": 0,
        "details": [],
    }

    all_documents = []

    if "verra" in sources:
        verra_list = fetch_verra_methodology_list()
        all_documents.extend(verra_list[:max_per_source])

        if include_program_docs:
            program_docs = fetch_verra_program_docs()
            all_documents.extend(program_docs)

        if include_registry_projects:
            registry_docs = fetch_verra_registry_docs(
                max_projects=max_registry_projects,
                discover=discover_projects,
            )
            all_documents.extend(registry_docs)

    if "cdm" in sources:
        cdm_list = fetch_cdm_methodology_list()
        all_documents.extend(cdm_list[:max_per_source])

    if "goldstandard" in sources:
        gs_list = fetch_gs_methodology_list()
        all_documents.extend(gs_list[:max_per_source])

        if include_registry_projects:
            gs_registry_docs = fetch_gs_registry_docs(
                max_projects=max_registry_projects,
                discover=discover_projects,
            )
            all_documents.extend(gs_registry_docs)

    results["total_found"] = len(all_documents)

    api_key = os.getenv("OPENAI_API_KEY")

    for doc in all_documents:
        code = doc["code"]
        source = doc["source"]
        reference_id = f"{source}_{code}"
        category = doc.get("category", "methodology")
        file_type = doc.get("file_type", "pdf")

        existing = _is_already_stored(reference_id)
        if existing:
            results["already_stored"] += 1
            results["details"].append({
                "code": code,
                "source": source,
                "category": category,
                "status": "already_stored",
                "doc_id": existing.get("id"),
            })
            continue

        if dry_run:
            results["details"].append({
                "code": code,
                "source": source,
                "category": category,
                "status": "would_download",
                "title": doc.get("title", code),
            })
            continue

        if doc.get("download_available") is False:
            results["skipped_no_download"] += 1
            results["details"].append({
                "code": code,
                "source": source,
                "category": category,
                "status": "metadata_only",
                "title": doc.get("title", code),
            })
            continue

        pdf_url = doc.get("pdf_url")
        title = doc.get("title", code)

        if not pdf_url and source == "verra":
            time.sleep(RATE_LIMIT_DELAY)
            detail = fetch_verra_methodology_pdf(doc["detail_url"])
            if detail:
                pdf_url = detail["pdf_url"]
                title = detail.get("title", code)

        if not pdf_url:
            results["details"].append({
                "code": code,
                "source": source,
                "category": category,
                "status": "no_pdf_found",
            })
            results["errors"] += 1
            continue

        ext = "docx" if file_type == "docx" or pdf_url.endswith(".docx") else "pdf"
        filename = f"{reference_id}.{ext}"
        dest_path = REPO_DIR / filename

        if dest_path.exists():
            results["already_stored"] += 1
            results["details"].append({
                "code": code,
                "source": source,
                "category": category,
                "status": "file_exists",
            })
            continue

        time.sleep(RATE_LIMIT_DELAY)
        if not _download_file(pdf_url, dest_path):
            results["errors"] += 1
            results["details"].append({
                "code": code,
                "source": source,
                "category": category,
                "status": "download_failed",
            })
            continue

        results["newly_downloaded"] += 1

        standard_slug_map = {
            "verra": "verra",
            "cdm": "cdm",
            "goldstandard": "goldstandard",
        }

        try:
            from carbongpt.repository.store import create_document, list_standard_versions

            sv_id = None
            slug = standard_slug_map.get(source)
            if slug:
                versions = list_standard_versions()
                for v in versions:
                    if v.get("standard_slug") == slug or (
                        slug == "verra" and "verra" in v.get("standard_name", "").lower()
                    ):
                        sv_id = v["id"]
                        break

            doc_id = create_document(
                standard_version_id=sv_id,
                category=category,
                title=title,
                file_path=str(dest_path),
                file_type=ext,
                reference_id=reference_id,
                doc_version=None,
                file_size_bytes=dest_path.stat().st_size,
            )

            results["details"].append({
                "code": code,
                "source": source,
                "category": category,
                "status": "downloaded",
                "doc_id": doc_id,
                "pdf_url": pdf_url,
            })

            if api_key and ext == "pdf":
                import threading
                from carbongpt.repository.ingestion import ingest_document

                thread = threading.Thread(
                    target=_safe_ingest,
                    args=(doc_id, str(dest_path), api_key),
                    daemon=True,
                )
                thread.start()
                results["ingestion_started"] += 1
        except Exception as e:
            logger.error("Failed to store document %s: %s", code, e)
            results["errors"] += 1
            results["details"].append({
                "code": code,
                "source": source,
                "category": category,
                "status": "store_failed",
                "error": str(e),
            })

    return results


def _safe_ingest(doc_id, file_path, api_key):
    try:
        from carbongpt.repository.ingestion import ingest_document
        ingest_document(doc_id, file_path, api_key)
    except Exception as e:
        logger.error("Ingestion failed for doc %s: %s", doc_id, e)


_scheduler_started = False


def start_weekly_sync():
    global _scheduler_started
    if _scheduler_started:
        return
    _scheduler_started = True

    import threading

    interval = int(os.getenv("CARBONGPT_SYNC_INTERVAL_HOURS", "168"))  # 168 = 7 days
    interval_seconds = interval * 3600

    def _run_periodic():
        time.sleep(30)
        logger.info("Running initial methodology sync on startup...")
        try:
            result = sync_methodologies(max_per_source=50, include_program_docs=True)
            logger.info(
                "Initial sync complete: %d found, %d new, %d errors",
                result["total_found"],
                result["newly_downloaded"],
                result["errors"],
            )
        except Exception as e:
            logger.error("Initial sync failed: %s", e)
        while True:
            time.sleep(interval_seconds)
            logger.info("Running scheduled methodology sync...")
            try:
                result = sync_methodologies(max_per_source=50, include_program_docs=True)
                logger.info(
                    "Scheduled sync complete: %d found, %d new, %d errors",
                    result["total_found"],
                    result["newly_downloaded"],
                    result["errors"],
                )
            except Exception as e:
                logger.error("Scheduled sync failed: %s", e)

    thread = threading.Thread(target=_run_periodic, daemon=True)
    thread.start()
    logger.info("Methodology sync scheduler started (interval: %d hours)", interval)
