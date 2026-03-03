import io
import os
import re
import copy
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

STANDARD_LABELS = {
    "GoldStandard": "Gold Standard",
    "Verra": "Verra VCS",
}

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "document_repository")

TEMPLATE_FILES = {
    ("GoldStandard", "pdd"): "gs_pdd_template_v1.5.docx",
    ("Verra", "pdd"): "ae547f753ee34b55927782d5243c4737_VCS-Project-Description-Template-v4.4-FINAL2_1772118270885.docx",
    ("Verra", "mr"): "a7eeb5a6d7264480ac6292ebbb308929_VCS-Monitoring-Report-Template-v4.4-FINAL2.docx",
}

GS_SECTION_RE = re.compile(
    r"^([A-F]\.\d+(?:\.\d+)?)\b", re.IGNORECASE
)
VCS_SECTION_RE = re.compile(
    r"^(\d+\.\d+(?:\.\d+)?)\b"
)


def _resolve_template_path(standard, doc_type):
    fname = TEMPLATE_FILES.get((standard, doc_type))
    if not fname:
        return None
    path = os.path.join(TEMPLATE_DIR, fname)
    if os.path.isfile(path):
        return path
    return None


def _parse_markdown_content(content_text):
    lines = content_text.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("|") and i + 1 < len(lines):
            table_lines = [stripped]
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                table_lines.append(lines[j].strip())
                j += 1
            if len(table_lines) >= 2:
                blocks.append(("table", table_lines))
                i = j
                continue

        if stripped.startswith("#### "):
            blocks.append(("heading4", stripped[5:].strip()))
        elif stripped.startswith("### "):
            blocks.append(("heading4", stripped[4:].strip()))
        elif stripped.startswith("## "):
            blocks.append(("heading3", stripped[3:].strip()))
        elif stripped.startswith("# "):
            blocks.append(("heading3", stripped[2:].strip()))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append(("bullet", stripped[2:].strip()))
        elif re.match(r"^\d+\.\s", stripped):
            blocks.append(("numbered", re.sub(r"^\d+\.\s", "", stripped).strip()))
        elif stripped.startswith("[INSERT:") or stripped.startswith("[insert:"):
            blocks.append(("insert_placeholder", stripped))
        elif stripped.startswith("**") and stripped.endswith("**") and len(stripped) > 4:
            blocks.append(("bold_line", stripped[2:-2].strip()))
        elif stripped == "---":
            pass
        elif stripped == "":
            blocks.append(("empty", ""))
        else:
            blocks.append(("paragraph", stripped))
        i += 1
    return blocks


def _parse_md_table(table_lines):
    rows = []
    for line in table_lines:
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c != ""]
        if cells and all(re.match(r"^[-:]+$", c) for c in cells):
            continue
        if cells:
            rows.append(cells)
    return rows


def _insert_content_into_doc(doc, insert_after_element, content_text, project_info=None):
    from docx.shared import Pt, RGBColor
    from docx.oxml.ns import qn

    blocks = _parse_markdown_content(content_text)
    parent = insert_after_element.getparent()
    ref_element = insert_after_element

    def _add_para_after(text, style_name=None, bold=False, italic=False, color=None, font_size=None):
        nonlocal ref_element
        new_para = copy.deepcopy(doc.paragraphs[0]._element)
        for child in list(new_para):
            new_para.remove(child)

        p_el = doc.element.makeelement(qn("w:p"), {})
        r_el = doc.element.makeelement(qn("w:r"), {})
        rpr = doc.element.makeelement(qn("w:rPr"), {})

        if bold:
            rpr.append(doc.element.makeelement(qn("w:b"), {}))
        if italic:
            rpr.append(doc.element.makeelement(qn("w:i"), {}))
        if color:
            color_el = doc.element.makeelement(qn("w:color"), {qn("w:val"): color})
            rpr.append(color_el)
        if font_size:
            sz_el = doc.element.makeelement(qn("w:sz"), {qn("w:val"): str(font_size * 2)})
            rpr.append(sz_el)

        r_el.append(rpr)
        t_el = doc.element.makeelement(qn("w:t"), {})
        t_el.text = text
        t_el.set(qn("xml:space"), "preserve")
        r_el.append(t_el)
        p_el.append(r_el)

        ref_element.addnext(p_el)
        ref_element = p_el
        return p_el

    def _add_table_after(rows_data):
        nonlocal ref_element
        if not rows_data:
            return

        ncols = max(len(r) for r in rows_data)
        tbl_el = doc.element.makeelement(qn("w:tbl"), {})

        tbl_pr = doc.element.makeelement(qn("w:tblPr"), {})
        tbl_style = doc.element.makeelement(qn("w:tblStyle"), {qn("w:val"): "TableGrid"})
        tbl_pr.append(tbl_style)
        tbl_w = doc.element.makeelement(qn("w:tblW"), {qn("w:w"): "5000", qn("w:type"): "pct"})
        tbl_pr.append(tbl_w)
        tbl_borders = doc.element.makeelement(qn("w:tblBorders"), {})
        for border_name in ["top", "left", "bottom", "right", "insideH", "insideV"]:
            b = doc.element.makeelement(qn(f"w:{border_name}"), {
                qn("w:val"): "single", qn("w:sz"): "4",
                qn("w:space"): "0", qn("w:color"): "000000"
            })
            tbl_borders.append(b)
        tbl_pr.append(tbl_borders)
        tbl_el.append(tbl_pr)

        tbl_grid = doc.element.makeelement(qn("w:tblGrid"), {})
        for _ in range(ncols):
            tbl_grid.append(doc.element.makeelement(qn("w:gridCol"), {}))
        tbl_el.append(tbl_grid)

        for ri, row_cells in enumerate(rows_data):
            tr = doc.element.makeelement(qn("w:tr"), {})
            for ci in range(ncols):
                tc = doc.element.makeelement(qn("w:tc"), {})
                p = doc.element.makeelement(qn("w:p"), {})
                r = doc.element.makeelement(qn("w:r"), {})
                rpr = doc.element.makeelement(qn("w:rPr"), {})
                sz = doc.element.makeelement(qn("w:sz"), {qn("w:val"): "20"})
                rpr.append(sz)
                if ri == 0:
                    rpr.append(doc.element.makeelement(qn("w:b"), {}))
                r.append(rpr)
                t = doc.element.makeelement(qn("w:t"), {})
                t.text = row_cells[ci] if ci < len(row_cells) else ""
                t.set(qn("xml:space"), "preserve")
                r.append(t)
                p.append(r)
                tc.append(p)
                tr.append(tc)
            tbl_el.append(tr)

        ref_element.addnext(tbl_el)
        ref_element = tbl_el

    for block_type, block_data in blocks:
        if block_type == "table":
            rows = _parse_md_table(block_data)
            if rows:
                _add_table_after(rows)
        elif block_type == "heading3":
            _add_para_after(block_data, bold=True, font_size=13)
        elif block_type == "heading4":
            _add_para_after(block_data, bold=True, font_size=11)
        elif block_type == "bullet":
            _add_para_after(f"\u2022  {block_data}")
        elif block_type == "numbered":
            _add_para_after(block_data)
        elif block_type == "insert_placeholder":
            _add_para_after(block_data, bold=True, color="CC0000")
        elif block_type == "bold_line":
            _add_para_after(block_data, bold=True)
        elif block_type == "empty":
            _add_para_after("")
        elif block_type == "paragraph":
            _add_para_after(block_data)


def _fill_gs_template(doc, sections_map, project_info):
    paragraphs = list(doc.paragraphs)

    GS_SUBSECTION_ALIASES = {
        "Eligibility of the project under Gold Standard": "A.1.1",
        "Legal ownership of products generated by the project": "A.1.2",
        "B.5.1 Prior Consideration": "B.5.1",
        "B.5.2 Ongoing Financial Need": "B.5.2",
        "B.6.1 Explanation of methodological choices": "B.6.1",
        "B.6.2 Data and parameters fixed ex ante": "B.6.2",
        "B.6.3 Ex ante estimation of SDG Impact": "B.6.3",
        "B.6.4 Summary of ex ante estimates": "B.6.4",
        "B.7.1 Data and parameters to be monitored": "B.7",
        "B.7.2 Sampling plan": "B.7",
        "B.7.3 Other elements of monitoring plan": "B.7",
        "C.1.1 Start date of project": "C.1",
        "C.1.2 Expected operational lifetime of project": "C.1",
        "C.2.1 Start date of crediting period": "C.2",
        "C.2.2 Total length of crediting period": "C.2",
    }

    kpi_table = doc.tables[0] if doc.tables else None
    if kpi_table:
        for row in kpi_table.rows:
            label = row.cells[0].text.strip().lower()
            if "project" in label and "name" in label:
                row.cells[1].text = project_info.get("name", "")
            elif "country" in label:
                row.cells[1].text = project_info.get("country", "")
            elif "methodology" in label:
                row.cells[1].text = project_info.get("methodology", "")

    filled_sids = set()

    for i, para in enumerate(paragraphs):
        text = para.text.strip()

        sid = None
        m = GS_SECTION_RE.match(text)
        if m:
            sid = m.group(1).upper()
        else:
            for alias_prefix, alias_sid in GS_SUBSECTION_ALIASES.items():
                if text.startswith(alias_prefix):
                    sid = alias_sid
                    break

        if not sid:
            continue

        content = sections_map.get(sid, "")
        if not content:
            continue
        if sid in filled_sids:
            j = i + 1
            if j < len(paragraphs) and paragraphs[j].text.strip() == ">>":
                para_el = paragraphs[j]._element
                parent = para_el.getparent()
                if parent is not None:
                    parent.remove(para_el)
            continue
        filled_sids.add(sid)

        j = i + 1
        while j < len(paragraphs):
            next_text = paragraphs[j].text.strip()
            next_style = paragraphs[j].style.name if paragraphs[j].style else ""
            if next_text == ">>" or (next_text == "" and "Block Text" not in next_style and "Heading" not in next_style):
                para_el = paragraphs[j]._element
                parent = para_el.getparent()
                if parent is not None:
                    parent.remove(para_el)
                    j += 1
                    continue
            break

        _insert_content_into_doc(doc, para._element, content, project_info)

    _remove_remaining_placeholders_gs(doc, sections_map)


def _remove_remaining_placeholders_gs(doc, sections_map):
    for para in list(doc.paragraphs):
        text = para.text.strip()
        if text != ">>":
            continue
        para_el = para._element
        prev = para_el.getprevious()
        if prev is not None:
            prev_text = prev.text or ""
            for r in prev.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                prev_text = r.text or ""
            prev_full = ""
            for r in prev.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                prev_full += (r.text or "")
            prev_full = prev_full.strip()

            m = GS_SECTION_RE.match(prev_full)
            if m:
                sid = m.group(1).upper()
                if sid in sections_map:
                    parent = para_el.getparent()
                    if parent is not None:
                        parent.remove(para_el)
                    continue

            for alias_prefix in [
                "B.5.1", "B.5.2", "B.6.1", "B.6.2", "B.6.3", "B.6.4",
                "B.7.1", "B.7.2", "B.7.3",
                "C.1.1", "C.1.2", "C.2.1", "C.2.2",
                "Eligibility of the project", "Legal ownership",
                "Additionality", "Applicability", "Compliance",
                "Level of accuracy", "Scale of the project",
                "Stakeholder consultation", "Sustainable development",
                "Safeguarding assessment",
            ]:
                if prev_full.startswith(alias_prefix):
                    parent = para_el.getparent()
                    if parent is not None:
                        parent.remove(para_el)
                    break


def _fill_vcs_template(doc, sections_map, project_info):
    from docx.shared import Pt

    paragraphs = list(doc.paragraphs)

    title_para = None
    for para in paragraphs:
        if para.style and para.style.name == "Template Title" and "Project" in para.text:
            title_para = para
            break
    if title_para:
        title_para.clear()
        title_para.add_run(project_info.get("name", "Project Title"))

    filled_sids = set()

    for i, para in enumerate(paragraphs):
        style_name = para.style.name if para.style else ""
        if "Heading" not in style_name:
            continue

        text = para.text.strip()
        m = VCS_SECTION_RE.match(text)
        if not m:
            continue
        sid = m.group(1)

        if not sid:
            continue

        content = sections_map.get(sid, "")
        if not content:
            continue
        if sid in filled_sids:
            continue
        filled_sids.add(sid)

        j = i + 1
        instructions_removed = 0
        while j < len(paragraphs) and instructions_removed < 20:
            next_style = paragraphs[j].style.name if paragraphs[j].style else ""
            next_text = paragraphs[j].text.strip()

            if next_style in ("Instruction", "Bullets", "List Paragraph"):
                para_el = paragraphs[j]._element
                parent = para_el.getparent()
                if parent is not None:
                    parent.remove(para_el)
                    instructions_removed += 1
                    continue
            elif next_text == "" and next_style == "Normal":
                para_el = paragraphs[j]._element
                parent = para_el.getparent()
                if parent is not None:
                    parent.remove(para_el)
                    instructions_removed += 1
                    continue
            else:
                break

        _insert_content_into_doc(doc, para._element, content, project_info)


def export_template_word(sections_content, project_info, template_type="pdd"):
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    standard = project_info.get("standard", "")
    template_path = _resolve_template_path(standard, template_type)

    sections_map = {}
    for sec in sections_content:
        sid = sec.get("section_id", "")
        content = sec.get("content", "")
        if content and content.strip():
            sections_map[sid] = content

    if template_path and sections_map:
        try:
            doc = Document(template_path)
            if standard == "GoldStandard":
                _fill_gs_template(doc, sections_map, project_info)
            elif standard == "Verra":
                _fill_vcs_template(doc, sections_map, project_info)
            else:
                _fill_gs_template(doc, sections_map, project_info)

            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.error("Template-based export failed, falling back to generic: %s", e, exc_info=True)

    return _export_generic_word(sections_content, project_info, template_type)


def _export_generic_word(sections_content, project_info, template_type="pdd"):
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    std_label = STANDARD_LABELS.get(project_info.get("standard", ""), project_info.get("standard", ""))
    doc_type_labels = {
        "pdd": "Project Design Document",
        "mr": "Monitoring Report",
        "vpa_dd": "VPA Design Document",
        "poa_dd": "PoA Design Document",
    }
    doc_type_label = doc_type_labels.get(template_type, template_type.upper())

    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(doc_type_label)
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(0x2E, 0x7D, 0x32)

    subtitle_para = doc.add_paragraph()
    subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle_para.add_run(std_label)
    subtitle_run.font.size = Pt(14)
    subtitle_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_paragraph()

    info_items = [
        ("Project Name", project_info.get("name", "[Project Name]")),
        ("Standard", std_label),
        ("Methodology", project_info.get("methodology", "[Methodology]")),
        ("Country", project_info.get("country", "[Country]")),
        ("Document Version", "Draft v1.0"),
        ("Date", datetime.now().strftime("%d %B %Y")),
    ]

    table = doc.add_table(rows=len(info_items), cols=2)
    table.style = "Table Grid"
    for i, (label, value) in enumerate(info_items):
        row = table.rows[i]
        row.cells[0].text = label
        row.cells[0].paragraphs[0].runs[0].bold = True if row.cells[0].paragraphs[0].runs else False
        row.cells[1].text = value

    doc.add_page_break()

    toc_heading = doc.add_heading("Table of Contents", level=1)
    for sec in sections_content:
        sid = sec.get("section_id", "")
        title = sec.get("title", "")
        toc_para = doc.add_paragraph(f"{sid}  {title}")
        toc_para.paragraph_format.space_after = Pt(2)

    doc.add_page_break()

    for sec in sections_content:
        sid = sec.get("section_id", "")
        title = sec.get("title", "")
        content = sec.get("content", "")
        status = sec.get("status", "placeholder")

        heading = doc.add_heading(f"{sid} {title}", level=2)

        if status == "placeholder":
            placeholder_para = doc.add_paragraph()
            run = placeholder_para.add_run("[This section requires input from the project developer]")
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

        if content:
            blocks = _parse_markdown_content(content)
            for block_type, block_data in blocks:
                if block_type == "table":
                    rows = _parse_md_table(block_data)
                    if rows:
                        ncols = max(len(r) for r in rows)
                        tbl = doc.add_table(rows=len(rows), cols=ncols)
                        tbl.style = "Table Grid"
                        for ri, row_cells in enumerate(rows):
                            for ci in range(ncols):
                                cell_text = row_cells[ci] if ci < len(row_cells) else ""
                                tbl.rows[ri].cells[ci].text = cell_text
                                if ri == 0:
                                    for run in tbl.rows[ri].cells[ci].paragraphs[0].runs:
                                        run.bold = True
                elif block_type == "heading3":
                    doc.add_heading(block_data, level=3)
                elif block_type == "heading4":
                    doc.add_heading(block_data, level=4)
                elif block_type == "bullet":
                    doc.add_paragraph(block_data, style="List Bullet")
                elif block_type == "insert_placeholder":
                    p = doc.add_paragraph()
                    run = p.add_run(block_data)
                    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
                    run.font.bold = True
                elif block_type == "bold_line":
                    p = doc.add_paragraph()
                    run = p.add_run(block_data)
                    run.bold = True
                elif block_type == "empty":
                    doc.add_paragraph()
                elif block_type == "paragraph":
                    doc.add_paragraph(block_data)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def export_calculation_excel(calc_result, project_info=None, parsed_methodology=None):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, numbers

    wb = Workbook()

    header_font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
    subheader_font = Font(name="Calibri", size=10, bold=True)
    subheader_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    number_format = "#,##0.00"

    ws = wb.active
    ws.title = "Emission Reductions"

    proj_name = (project_info or {}).get("name", "Carbon Project")
    meth_code = calc_result.get("methodology_code", "")
    method_name = calc_result.get("calculation_method", "")

    row = 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
    cell = ws.cell(row=row, column=1, value=f"Emission Reduction Calculation - {proj_name}")
    cell.font = Font(name="Calibri", size=14, bold=True)
    row += 1

    info_data = [
        ("Project", proj_name),
        ("Methodology", f"{meth_code} - {method_name}"),
        ("Standard", STANDARD_LABELS.get((project_info or {}).get("standard", ""), "")),
        ("Country", (project_info or {}).get("country", "")),
        ("Generated", datetime.now().strftime("%Y-%m-%d %H:%M")),
    ]
    for label, value in info_data:
        ws.cell(row=row, column=1, value=label).font = Font(bold=True)
        ws.cell(row=row, column=2, value=value)
        row += 1
    row += 1

    headers = ["Year", "Baseline Emissions (tCO2e)", "Project Emissions (tCO2e)",
               "Leakage (tCO2e)", "Net Emission Reductions (tCO2e)"]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = thin_border
    row += 1

    data_start_row = row
    for yr in calc_result.get("annual_calculations", []):
        ws.cell(row=row, column=1, value=yr.get("year", "")).border = thin_border
        ws.cell(row=row, column=2, value=yr.get("baseline_emissions_tco2e", 0)).border = thin_border
        ws.cell(row=row, column=2).number_format = number_format
        ws.cell(row=row, column=3, value=yr.get("project_emissions_tco2e", 0)).border = thin_border
        ws.cell(row=row, column=3).number_format = number_format
        ws.cell(row=row, column=4, value=yr.get("leakage_tco2e", 0)).border = thin_border
        ws.cell(row=row, column=4).number_format = number_format
        ws.cell(row=row, column=5, value=yr.get("net_emission_reductions_tco2e", 0)).border = thin_border
        ws.cell(row=row, column=5).number_format = number_format
        row += 1
    data_end_row = row - 1

    total_row = row
    ws.cell(row=total_row, column=1, value="TOTAL").font = Font(bold=True)
    ws.cell(row=total_row, column=1).border = thin_border
    for col in range(2, 6):
        col_letter = chr(64 + col)
        cell = ws.cell(row=total_row, column=col)
        cell.value = f"=SUM({col_letter}{data_start_row}:{col_letter}{data_end_row})"
        cell.font = Font(bold=True)
        cell.number_format = number_format
        cell.border = thin_border
    row += 2

    ws.cell(row=row, column=1, value="Parameters Used").font = subheader_font
    ws.cell(row=row, column=1).fill = subheader_fill
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    row += 1

    param_headers = ["Parameter", "Value", "Unit", "Source"]
    for col_idx, h in enumerate(param_headers, 1):
        cell = ws.cell(row=row, column=col_idx, value=h)
        cell.font = Font(bold=True)
        cell.border = thin_border
    row += 1

    for p in calc_result.get("parameters_used", []):
        ws.cell(row=row, column=1, value=p.get("parameter", "")).border = thin_border
        ws.cell(row=row, column=2, value=p.get("value", "")).border = thin_border
        ws.cell(row=row, column=3, value=p.get("unit", "")).border = thin_border
        ws.cell(row=row, column=4, value=p.get("source", "")).border = thin_border
        row += 1

    if calc_result.get("assumptions"):
        row += 1
        ws.cell(row=row, column=1, value="Assumptions").font = subheader_font
        ws.cell(row=row, column=1).fill = subheader_fill
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
        row += 1
        for a in calc_result["assumptions"]:
            ws.cell(row=row, column=1, value=a)
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
            row += 1

    if calc_result.get("annual_calculations"):
        first_yr = calc_result["annual_calculations"][0]
        if first_yr.get("calculation_steps"):
            ws_steps = wb.create_sheet("Calculation Steps")
            sr = 1
            ws_steps.cell(row=sr, column=1, value="Detailed Calculation Steps").font = Font(size=14, bold=True)
            sr += 2
            for yr_data in calc_result["annual_calculations"]:
                ws_steps.cell(row=sr, column=1, value=f"Year {yr_data.get('year', '?')}").font = Font(bold=True, size=11)
                sr += 1
                step_headers = ["Step", "Formula", "Values Substituted", "Result"]
                for ci, sh in enumerate(step_headers, 1):
                    ws_steps.cell(row=sr, column=ci, value=sh).font = Font(bold=True)
                    ws_steps.cell(row=sr, column=ci).border = thin_border
                sr += 1
                for step in yr_data.get("calculation_steps", []):
                    ws_steps.cell(row=sr, column=1, value=step.get("step", "")).border = thin_border
                    ws_steps.cell(row=sr, column=2, value=step.get("formula", "")).border = thin_border
                    ws_steps.cell(row=sr, column=3, value=step.get("values", "")).border = thin_border
                    ws_steps.cell(row=sr, column=4, value=step.get("result", "")).border = thin_border
                    sr += 1
                sr += 1

    if calc_result.get("monitoring_parameters"):
        ws_mon = wb.create_sheet("Monitoring Parameters")
        mr = 1
        ws_mon.cell(row=mr, column=1, value="Monitoring Parameters").font = Font(size=14, bold=True)
        mr += 2
        mon_headers = ["Parameter", "Unit", "Monitoring Frequency", "Measurement Method"]
        for ci, mh in enumerate(mon_headers, 1):
            cell = ws_mon.cell(row=mr, column=ci, value=mh)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = thin_border
        mr += 1
        for mp in calc_result["monitoring_parameters"]:
            ws_mon.cell(row=mr, column=1, value=mp.get("parameter", "")).border = thin_border
            ws_mon.cell(row=mr, column=2, value=mp.get("unit", "")).border = thin_border
            ws_mon.cell(row=mr, column=3, value=mp.get("frequency", "")).border = thin_border
            ws_mon.cell(row=mr, column=4, value=mp.get("method", "")).border = thin_border
            mr += 1

    for sheet in wb.worksheets:
        for col_cells in sheet.columns:
            max_len = 0
            col_letter = col_cells[0].column_letter
            for cell in col_cells:
                val = str(cell.value or "")
                max_len = max(max_len, min(len(val), 50))
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def generate_filled_template(project_info, generated_sections, calc_result=None):
    sections_content = []
    for sec in generated_sections:
        sections_content.append({
            "section_id": sec.get("id", sec.get("section_id", "")),
            "title": sec.get("title", ""),
            "content": sec.get("content", ""),
            "status": "generated" if sec.get("content") else "placeholder",
        })

    if calc_result and not calc_result.get("error"):
        from carbongpt.core.calculation_engine import format_calculation_narrative
        calc_narrative = format_calculation_narrative(calc_result)
        calc_section_ids = {"B.6", "B.6.1", "4.1", "4.2", "4.3", "4.4"}
        inserted = False
        for sec in sections_content:
            sid = sec.get("section_id", "")
            if sid in calc_section_ids or "emission" in sec.get("title", "").lower():
                if not sec.get("content"):
                    sec["content"] = calc_narrative
                    sec["status"] = "generated"
                    inserted = True
                    break
        if not inserted:
            sections_content.append({
                "section_id": "CALC",
                "title": "Emission Reduction Calculations",
                "content": calc_narrative,
                "status": "generated",
            })

    doc_type = project_info.get("doc_type", "pdd")
    return export_template_word(sections_content, project_info, template_type=doc_type)
