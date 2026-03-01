import logging
import re
from carbongpt.repository.db import get_cursor
from carbongpt.repository.store import upsert_methodology

logger = logging.getLogger(__name__)

METHODOLOGY_FAMILIES = {
    "ACM": {"standard": "CDM/Verra", "category": "Large-scale Consolidated"},
    "AM": {"standard": "CDM/Verra", "category": "Large-scale Approved"},
    "AMS": {"standard": "CDM/Verra", "category": "Small-scale"},
    "AR-ACM": {"standard": "CDM/Verra", "category": "Afforestation/Reforestation Consolidated"},
    "AR-AM": {"standard": "CDM/Verra", "category": "Afforestation/Reforestation"},
    "AR-AMS": {"standard": "CDM/Verra", "category": "Afforestation/Reforestation Small-scale"},
    "VM": {"standard": "Verra", "category": "VCS Methodology"},
    "VMR": {"standard": "Verra", "category": "VCS Methodology Revision"},
    "VMD": {"standard": "Verra", "category": "VCS Module"},
    "GS": {"standard": "GoldStandard", "category": "Gold Standard Methodology"},
}

KNOWN_METHODOLOGIES = {
    "ACM0001": {"name": "Flaring or use of landfill gas", "sector": "Waste handling and disposal"},
    "ACM0002": {"name": "Grid-connected electricity generation from renewable sources", "sector": "Energy industries (renewable sources)"},
    "ACM0003": {"name": "Partial substitution of fossil fuels in cement or calcium production", "sector": "Manufacturing industries"},
    "ACM0005": {"name": "Increasing the blend in cement production", "sector": "Manufacturing industries"},
    "ACM0006": {"name": "Electricity and heat generation from biomass", "sector": "Energy industries (renewable sources)"},
    "ACM0007": {"name": "Conversion from single to combined cycle power generation", "sector": "Energy industries"},
    "ACM0010": {"name": "GHG emission reductions from manure management systems", "sector": "Agriculture"},
    "ACM0012": {"name": "Waste energy recovery", "sector": "Energy industries"},
    "ACM0018": {"name": "Electricity generation from biomass in power-only plants", "sector": "Energy industries (renewable sources)"},
    "ACM0022": {"name": "Alternative waste treatment processes", "sector": "Waste handling and disposal"},
    "AM0001": {"name": "Decomposition of fluoroform (HFC-23) waste streams", "sector": "Chemical industries"},
    "AM0025": {"name": "Avoided emissions from organic waste through alternative waste treatment", "sector": "Waste handling and disposal"},
    "AM0029": {"name": "Grid-connected electricity generation from renewable sources (for baseload)", "sector": "Energy industries (renewable sources)"},
    "AM0058": {"name": "Introduction of a new natural gas-based industrial CHP system", "sector": "Energy demand"},
    "AM0072": {"name": "Fossil fuel displacement by geothermal resources", "sector": "Energy industries (renewable sources)"},
    "AM0110": {"name": "Modal shift in transportation of cargo", "sector": "Transport"},
    "AM0121": {"name": "Waste energy recovery and utilization at an existing industrial facility", "sector": "Energy industries"},
    "AMS-I.A.": {"name": "Electricity generation by the user", "sector": "Energy industries (renewable sources)"},
    "AMS-I.B.": {"name": "Mechanical energy for the user with or without electricity", "sector": "Energy industries (renewable sources)"},
    "AMS-I.C.": {"name": "Thermal energy production with or without electricity", "sector": "Energy industries (renewable sources)"},
    "AMS-I.D.": {"name": "Grid-connected renewable electricity generation", "sector": "Energy industries (renewable sources)"},
    "AMS-I.E.": {"name": "Switch from non-renewable biomass for thermal applications by the user", "sector": "Energy demand"},
    "AMS-I.F.": {"name": "Renewable electricity generation for captive use and mini-grid", "sector": "Energy industries (renewable sources)"},
    "AMS-I.J.": {"name": "Solar water heating systems", "sector": "Energy demand"},
    "AMS-I.L.": {"name": "Electrification of rural communities using renewable energy", "sector": "Energy industries (renewable sources)"},
    "AMS-II.C.": {"name": "Demand-side energy efficiency activities for specific technologies", "sector": "Energy demand"},
    "AMS-II.E.": {"name": "Energy efficiency and fuel switching measures for buildings", "sector": "Energy demand"},
    "AMS-II.G.": {"name": "Energy efficiency measures in thermal applications of non-renewable biomass", "sector": "Energy demand", "applicability": "Cookstoves and other thermal energy devices replacing non-renewable biomass"},
    "AMS-II.J.": {"name": "Demand-side activities for efficient lighting technologies", "sector": "Energy demand"},
    "AMS-III.AR.": {"name": "Substituting fossil fuel based lighting with LED/CFL lighting systems", "sector": "Energy demand"},
    "AMS-III.AU.": {"name": "Methane emission reduction by adjusted water management practice in rice cultivation", "sector": "Agriculture"},
    "AMS-III.AV.": {"name": "Low greenhouse gas emitting water purification systems", "sector": "Energy demand"},
    "AMS-III.B.": {"name": "Switching fossil fuels", "sector": "Energy industries"},
    "AMS-III.BF.": {"name": "Reduction of electricity consumption by replacing electric lamps by LED", "sector": "Energy demand"},
    "AMS-III.BG.": {"name": "Emission reduction from thermal oxidation of HFC-23 waste streams", "sector": "Chemical industries"},
    "AMS-III.D.": {"name": "Methane recovery in animal manure management systems", "sector": "Agriculture"},
    "AMS-III.E.": {"name": "Avoidance of methane production from decay of biomass through controlled combustion", "sector": "Waste handling and disposal"},
    "AMS-III.F.": {"name": "Avoidance of methane emissions from composting", "sector": "Waste handling and disposal"},
    "AMS-III.G.": {"name": "Landfill methane recovery", "sector": "Waste handling and disposal"},
    "AMS-III.H.": {"name": "Methane recovery in wastewater treatment", "sector": "Waste handling and disposal"},
    "AMS-III.K.": {"name": "Avoidance of methane release from charcoal production", "sector": "Waste handling and disposal"},
    "AMS-III.R.": {"name": "Methane recovery in agricultural activities at household/small farm level", "sector": "Agriculture"},
    "AMS-III.Z.": {"name": "Fuel switch, process improvement and energy efficiency in brick manufacture", "sector": "Manufacturing industries"},
    "AR-ACM0003": {"name": "Afforestation and reforestation of lands except wetlands", "sector": "Agriculture Forestry and Other Land Use"},
    "AR-AMS0007": {"name": "Simplified baseline and monitoring methodology for small-scale A/R", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0001": {"name": "Methodology for Infrared Automatic Refrigerant Leak Detection Efficiency", "sector": "Manufacturing industries"},
    "VM0003": {"name": "Methodology for Improved Forest Management through Extension of Rotation Age", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0004": {"name": "Methodology for Conservation Projects that Avoid Planned Land Use Conversion", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0006": {"name": "Methodology for Carbon Accounting for Mosaic and Landscape-scale REDD Projects", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0007": {"name": "REDD+ Methodology Framework", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0009": {"name": "Methodology for Avoided Ecosystem Conversion", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0010": {"name": "Methodology for Improved Forest Management: Conversion from Logged to Protected Forest", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0011": {"name": "Methodology for Calculating GHG Benefits from Preventing Planned Degradation", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0012": {"name": "Improved Forest Management in Temperate and Boreal Forests", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0015": {"name": "Methodology for Avoided Unplanned Deforestation", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0017": {"name": "Adoption of Sustainable Agricultural Land Management", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0021": {"name": "Soil Carbon Quantification Methodology", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0022": {"name": "Quantifying N2O Emission Reductions in Agricultural Crops through Nitrogen Management", "sector": "Agriculture"},
    "VM0025": {"name": "Campus Clean Energy and Energy Efficiency", "sector": "Energy demand"},
    "VM0026": {"name": "Methodology for Sustainable Grassland Management", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0032": {"name": "Methodology for the Adoption of Sustainable Grasslands through Adjustment of Fire and Grazing", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0033": {"name": "Methodology for Tidal Wetland and Seagrass Restoration", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0036": {"name": "Methodology for Rewetting Drained Temperate Peatlands", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0037": {"name": "Methodology for Implementation of REDD+ Activities in Peat Swamp Forests", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0041": {"name": "Methodology for the Reduction of Enteric Methane Emissions from Ruminants through the Use of Feed Ingredients", "sector": "Agriculture"},
    "VM0042": {"name": "Methodology for Improved Agricultural Land Management", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0044": {"name": "Methodology for Biochar Utilization in Soil and Non-Soil Applications", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0046": {"name": "Methodology for Reducing Food Loss and Waste", "sector": "Waste handling and disposal"},
    "VM0047": {"name": "Afforestation, Reforestation, and Revegetation", "sector": "Agriculture Forestry and Other Land Use"},
    "VM0048": {"name": "Reducing Emissions from Deforestation and Forest Degradation", "sector": "Agriculture Forestry and Other Land Use"},
    "VMR0001": {"name": "Revisions to ACM0002 to Include Renewable Energy CPA under a CDM PoA", "sector": "Energy industries (renewable sources)"},
    "VMR0005": {"name": "Methodology for Improved Forest Management", "sector": "Agriculture Forestry and Other Land Use"},
    "VMR0006": {"name": "Methodology for Carbon Accounting for REDD+", "sector": "Agriculture Forestry and Other Land Use", "status": "deprecated", "superseded_by": "VM0048"},
    "GS-COOKSTOVE": {"name": "Technologies and Practices to Displace Decentralized Thermal Energy Consumption", "sector": "Energy demand", "standard": "GoldStandard"},
    "GS-TPDDTEC": {"name": "Technologies and Practices to Displace Decentralized Thermal Energy Consumption", "sector": "Energy demand", "standard": "GoldStandard", "applicability": "Cookstoves, water heating, space heating"},
    "GS-WASH": {"name": "Water Benefit Standard / WASH Methodology", "sector": "Energy demand", "standard": "GoldStandard"},
    "GS-AR": {"name": "Gold Standard Afforestation/Reforestation Methodology", "sector": "Agriculture Forestry and Other Land Use", "standard": "GoldStandard"},
    "GS-SOIL": {"name": "Gold Standard Soil Organic Carbon Framework Methodology", "sector": "Agriculture Forestry and Other Land Use", "standard": "GoldStandard"},
    "GS-METERED": {"name": "Metered & Measured Energy Methodology", "sector": "Energy demand", "standard": "GoldStandard"},
    "GS-MANGROVE": {"name": "Gold Standard Mangrove Methodology", "sector": "Agriculture Forestry and Other Land Use", "standard": "GoldStandard"},
}


def _classify_methodology(code):
    for prefix, info in sorted(METHODOLOGY_FAMILIES.items(), key=lambda x: -len(x[0])):
        if code.upper().startswith(prefix.upper()):
            return info
    return {"standard": "Other", "category": "Other"}


def populate_methodologies_from_projects():
    with get_cursor() as cur:
        cur.execute("SELECT methodology FROM carbon_projects WHERE methodology IS NOT NULL AND methodology != ''")
        rows = cur.fetchall()

    code_counts = {}
    code_names = {}
    for r in rows:
        m = r["methodology"]
        for part in m.replace(";", ",").split(","):
            part = part.strip()
            if not part or len(part) < 2:
                continue
            if part.split(" ")[0] in ("and", "or", "the", "not", "for", "with", "from", "process", "excluding", "Version"):
                continue
            code = part.split(" ")[0] if " " in part else part
            name_part = part[len(code):].strip() if " " in part else ""
            if not re.match(r'^[A-Z]', code):
                continue
            code_counts[code] = code_counts.get(code, 0) + 1
            if name_part and len(name_part) > len(code_names.get(code, "")):
                code_names[code] = name_part

    count = 0
    for code, proj_count in sorted(code_counts.items()):
        known = KNOWN_METHODOLOGIES.get(code, {})
        family = _classify_methodology(code)

        name = known.get("name") or code_names.get(code) or None
        standard = known.get("standard") or family.get("standard")
        category = known.get("category") or family.get("category")
        sector = known.get("sector")
        status = known.get("status", "active")
        applicability = known.get("applicability")
        superseded_by = known.get("superseded_by")

        upsert_methodology(
            code=code,
            name=name,
            standard=standard,
            category=category,
            sector=sector,
            status=status,
            applicability=applicability,
            superseded_by=superseded_by,
            project_count=proj_count,
        )
        count += 1

    logger.info("Populated %d methodologies from project data", count)
    return count
