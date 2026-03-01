import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

STANDARD_LABELS = {
    "GoldStandard": "Gold Standard",
    "Verra": "Verra VCS",
}


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


def export_template_word(sections_content, project_info, template_type="pdd"):
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
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
            for para_text in content.split("\n"):
                para_text = para_text.strip()
                if not para_text:
                    doc.add_paragraph()
                    continue
                if para_text.startswith("### "):
                    doc.add_heading(para_text[4:], level=4)
                elif para_text.startswith("## "):
                    doc.add_heading(para_text[3:], level=3)
                elif para_text.startswith("- ") or para_text.startswith("* "):
                    doc.add_paragraph(para_text[2:], style="List Bullet")
                elif para_text.startswith("[INSERT:") or para_text.startswith("[insert:"):
                    p = doc.add_paragraph()
                    run = p.add_run(para_text)
                    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
                    run.font.bold = True
                else:
                    doc.add_paragraph(para_text)

    buf = io.BytesIO()
    doc.save(buf)
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
