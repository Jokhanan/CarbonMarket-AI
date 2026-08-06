"""
One-off script (v1.0 milestone): generates a complete VPA-DD on the real
project id=12 (Gh, Ghana, RECH v5.0) through the sourced pipelines
(parameter_block_drafting.py + prose_section_drafting.py) and exports it
to the real Gold Standard VPA-DD v3.0 .docx template.

Read-only against the project: does not write to write_sessions,
project_parameters, or project_open_questions — this is a generation +
export run, not a persisted editing session.
"""
import json
import sys

sys.path.insert(0, ".")

from carbongpt.repository.store import get_user_project
from carbongpt.core.ai_writer import generate_full_document
from carbongpt.core.doc_exporter import export_template_word

PROJECT_ID = 12


def main():
    project = get_user_project(PROJECT_ID)
    if not project:
        raise SystemExit(f"Project {PROJECT_ID} not found")

    project_info = {
        "id": project["id"],
        "name": project["name"],
        "standard": project.get("standard"),
        "methodology": project.get("methodology"),
        "country": project.get("country"),
        "description": project.get("description"),
        "project_intake": project.get("project_intake") or {},
        "project_settings": project.get("project_settings") or {},
        "document_language": project.get("document_language") or "en",
    }

    def progress(idx, total, section_id, title):
        print(f"[{idx + 1}/{total}] {section_id}: {title}", file=sys.stderr)

    results = generate_full_document(
        standard="GoldStandard",
        project_doc_type="vpa_dd",
        project_info=project_info,
        progress_callback=progress,
    )

    with open("scripts/_vpa_dd_v3_project12_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    success = sum(1 for r in results if r["status"] == "success")
    error = sum(1 for r in results if r["status"] == "error")
    print(f"\n{success} succeeded, {error} errored, {len(results)} total", file=sys.stderr)

    export_project_info = {
        "name": project["name"],
        "standard": project.get("standard"),
        "methodology": project.get("methodology"),
        "country": project.get("country"),
        "description": project.get("description"),
        "doc_type": "vpa_dd",
        "intake": {},
    }
    sections_content = [
        {"section_id": r["section_id"], "title": r["section_title"], "content": r["generated_text"]}
        for r in results
    ]
    buf = export_template_word(sections_content, export_project_info, template_type="vpa_dd")
    with open("scripts/VPA-DD_v3.0_project12_Gh.docx", "wb") as f:
        f.write(buf.getvalue())
    print("Wrote scripts/VPA-DD_v3.0_project12_Gh.docx", file=sys.stderr)


if __name__ == "__main__":
    main()
