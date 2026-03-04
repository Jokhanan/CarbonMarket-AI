import logging
import re
from carbongpt.repository.db import get_cursor
from carbongpt.repository.store import upsert_methodology

logger = logging.getLogger(__name__)

METHODOLOGY_FAMILIES = {
    "ACM": {"standard": "CDM", "category": "Large-scale Consolidated"},
    "AM0": {"standard": "CDM", "category": "Large-scale Approved"},
    "AMS": {"standard": "CDM", "category": "Small-scale"},
    "AR-ACM": {"standard": "CDM", "category": "Afforestation/Reforestation Consolidated"},
    "AR-AM0": {"standard": "CDM", "category": "Afforestation/Reforestation Approved"},
    "AR-AMS": {"standard": "CDM", "category": "Afforestation/Reforestation Small-scale"},
    "VM0": {"standard": "Verra", "category": "VCS Methodology"},
    "VMR": {"standard": "Verra", "category": "VCS Methodology Revision"},
    "VMD": {"standard": "Verra", "category": "VCS Module"},
}

CDM_METHODOLOGY_NAMES = {
    "ACM0001": ("Flaring or use of landfill gas", "Waste handling and disposal"),
    "ACM0002": ("Grid-connected electricity generation from renewable sources", "Energy industries (renewable sources)"),
    "ACM0003": ("Partial substitution of fossil fuels in cement or calcium production", "Manufacturing industries"),
    "ACM0005": ("Increasing the blend in cement production", "Manufacturing industries"),
    "ACM0006": ("Electricity and heat generation from biomass", "Energy industries (renewable sources)"),
    "ACM0007": ("Conversion from single to combined cycle power generation", "Energy industries"),
    "ACM0008": ("Abatement of methane from coal mines", "Fugitive emissions from fuels"),
    "ACM0009": ("Fuel switching from coal or petroleum fuels to natural gas", "Energy industries"),
    "ACM0010": ("GHG emission reductions from manure management systems", "Agriculture"),
    "ACM0011": ("Consolidated baseline methodology for fuel switching from coal and/or petroleum fuels to natural gas in existing power plants for electricity generation", "Energy industries"),
    "ACM0012": ("Waste energy recovery", "Energy industries"),
    "ACM0013": ("New grid connected fossil fuel fired power plants using a less GHG intensive technology", "Energy industries"),
    "ACM0014": ("Treatment of wastewater", "Waste handling and disposal"),
    "ACM0016": ("Mass Rapid Transit Projects", "Transport"),
    "ACM0017": ("Production of biodiesel for use as fuel", "Energy industries (renewable sources)"),
    "ACM0018": ("Electricity generation from biomass in power-only plants", "Energy industries (renewable sources)"),
    "ACM0019": ("N2O abatement from nitric acid production", "Chemical industries"),
    "ACM0021": ("Reduction of emissions from charcoal production by improved kiln design and/or abatement of methane", "Manufacturing industries"),
    "ACM0022": ("Alternative waste treatment processes", "Waste handling and disposal"),
    "ACM0026": ("Fossil fuel based cogeneration for identified recipient facilities", "Energy industries"),
    "AM0001": ("Decomposition of fluoroform (HFC-23) waste streams", "Chemical industries"),
    "AM0007": ("Analysis of the least-cost fuel option for seasonally-operating biomass cogeneration plants", "Energy industries (renewable sources)"),
    "AM0009": ("Recovery and utilization of gas from oil wells that would otherwise be flared or vented", "Fugitive emissions from fuels"),
    "AM0010": ("GHG emission reductions through fumigation of warehoused grain with carbon dioxide", "Agriculture"),
    "AM0014": ("Natural gas-based package cogeneration", "Energy industries"),
    "AM0016": ("Greenhouse gas mitigation from improved animal husbandry and manure management", "Agriculture"),
    "AM0019": ("Renewable energy project activities replacing part of the electricity production of one single fossil fuel fired power plant", "Energy industries (renewable sources)"),
    "AM0023": ("Leak reduction from a natural gas distribution grid", "Fugitive emissions from fuels"),
    "AM0024": ("Methodology for greenhouse gas reductions through landfill gas thermal treatment", "Waste handling and disposal"),
    "AM0025": ("Avoided emissions from organic waste through alternative waste treatment", "Waste handling and disposal"),
    "AM0026": ("Methodology for zero-emissions grid-connected electricity generation from renewable sources in Chile or in countries with merit order based dispatch", "Energy industries (renewable sources)"),
    "AM0028": ("Catalytic N2O destruction in the tail gas of Nitric Acid or Caprolactam production plants", "Chemical industries"),
    "AM0029": ("Grid-connected electricity generation from renewable sources (for baseload)", "Energy industries (renewable sources)"),
    "AM0030": ("PFC emission reductions from anode effect mitigation at primary aluminium smelting facilities", "Manufacturing industries"),
    "AM0031": ("Bus rapid transit projects", "Transport"),
    "AM0034": ("Displacement of fossil fuel fired electricity generation through grid-connected electricity from biomass residues", "Energy industries (renewable sources)"),
    "AM0036": ("Fuel switch from fossil fuels to biomass residues in heat generation equipment", "Energy industries"),
    "AM0046": ("Distribution of efficient light bulbs to households", "Energy demand"),
    "AM0047": ("Production of biodiesel based on waste oils and/or waste fats from biogenic origin for use as fuel", "Energy industries (renewable sources)"),
    "AM0048": ("New cogeneration facilities supplying electricity and/or steam to multiple customers and displacing grid/off-grid electricity", "Energy industries"),
    "AM0057": ("Avoided emissions from biomass wastes through use as feed stock in pulp and paper,ite orite plants", "Manufacturing industries"),
    "AM0058": ("Introduction of a new natural gas-based combined heat and power or cogeneration system", "Energy demand"),
    "AM0059": ("GHG emission reductions through expansion of the area under sustainable forest management", "Agriculture Forestry and Other Land Use"),
    "AM0064": ("Utilization of waste in limestone andite production", "Manufacturing industries"),
    "AM0065": ("Replacement of SF6 with alternate cover gas in magnesium industry", "Manufacturing industries"),
    "AM0070": ("Manufacturing of energy efficient domestic refrigerators", "Energy demand"),
    "AM0072": ("Fossil fuel displacement by geothermal resources for space heating", "Energy industries (renewable sources)"),
    "AM0073": ("GHG emission reductions through multi-site manure collection and treatment in a central plant", "Agriculture"),
    "AM0080": ("Mitigation of greenhouse gases emissions with treatment of wastewater in aerobic wastewater treatment plants", "Waste handling and disposal"),
    "AM0082": ("Switch from non-renewable biomass for thermal applications by the user", "Energy demand"),
    "AM0086": ("Distribution of efficient light bulbs to households", "Energy demand"),
    "AM0089": ("Production of diesel using a mixed feedstock of jatropha and fossil fuels", "Energy industries (renewable sources)"),
    "AM0090": ("Modal shift in transportation of freight", "Transport"),
    "AM0110": ("Modal shift in transportation of cargo", "Transport"),
    "AM0121": ("Waste energy recovery and utilization at an existing industrial facility", "Energy industries"),
    "AM0123": ("Fuel switch from fossil fuel to biomass residues in boilers for heat generation", "Energy industries"),
    "AMS-I.A.": ("Electricity generation by the user", "Energy industries (renewable sources)"),
    "AMS-I.B.": ("Mechanical energy for the user with or without electricity", "Energy industries (renewable sources)"),
    "AMS-I.C.": ("Thermal energy production with or without electricity", "Energy industries (renewable sources)"),
    "AMS-I.D.": ("Grid-connected renewable electricity generation", "Energy industries (renewable sources)"),
    "AMS-I.E.": ("Switch from non-renewable biomass for thermal applications by the user", "Energy demand"),
    "AMS-I.F.": ("Renewable electricity generation for captive use and mini-grid", "Energy industries (renewable sources)"),
    "AMS-I.I.": ("Biogas/biomass thermal applications for households/small users", "Energy industries (renewable sources)"),
    "AMS-I.J.": ("Solar water heating systems", "Energy demand"),
    "AMS-I.K.": ("Solar cookers for households", "Energy demand"),
    "AMS-I.L.": ("Electrification of rural communities using renewable energy", "Energy industries (renewable sources)"),
    "AMS-II.B.": ("Supply side energy efficiency improvements - generation", "Energy industries"),
    "AMS-II.C.": ("Demand-side energy efficiency activities for specific technologies", "Energy demand"),
    "AMS-II.D.": ("Energy efficiency and fuel switching measures for industrial facilities", "Energy demand"),
    "AMS-II.E.": ("Energy efficiency and fuel switching measures for buildings", "Energy demand"),
    "AMS-II.F.": ("Energy efficiency and fuel switching measures for agricultural facilities and activities", "Agriculture"),
    "AMS-II.G.": ("Energy efficiency measures in thermal applications of non-renewable biomass", "Energy demand"),
    "AMS-II.H.": ("Energy efficiency - loss reduction and/or fuel switching measures in existing industrial cogeneration systems", "Energy industries"),
    "AMS-II.J.": ("Demand-side activities for efficient lighting technologies", "Energy demand"),
    "AMS-II.L.": ("Demand-side activities for efficient outdoor and street lighting technologies", "Energy demand"),
    "AMS-II.M.": ("Demand-side energy efficiency activities for installation of low-flow hot water savings devices", "Energy demand"),
    "AMS-II.S.": ("Energy efficiency in motor systems", "Energy demand"),
    "AMS-III.AF.": ("Avoidance of methane emissions through excavating and composting partially decayed municipal solid waste", "Waste handling and disposal"),
    "AMS-III.AJ.": ("Recovery and recycling of materials from solid wastes", "Waste handling and disposal"),
    "AMS-III.AK.": ("Biodiesel production and use for transport applications", "Transport"),
    "AMS-III.AO.": ("Methane recovery through controlled anaerobic digestion", "Waste handling and disposal"),
    "AMS-III.AQ.": ("Introduction of Bio-CNG in transportation applications", "Transport"),
    "AMS-III.AR.": ("Substituting fossil fuel based lighting with LED/CFL lighting systems", "Energy demand"),
    "AMS-III.AS.": ("Switch from fossil fuel to biomass in existing manufacturing facilities for non-energy applications", "Manufacturing industries"),
    "AMS-III.AU.": ("Methane emission reduction by adjusted water management practice in rice cultivation", "Agriculture"),
    "AMS-III.AV.": ("Low greenhouse gas emitting water purification systems", "Energy demand"),
    "AMS-III.B.": ("Switching fossil fuels", "Energy industries"),
    "AMS-III.BA.": ("Recovery and recycling of materials from E-waste", "Waste handling and disposal"),
    "AMS-III.BB.": ("Electrification of communities through grid extension or construction of new mini-grids", "Energy industries (renewable sources)"),
    "AMS-III.BC.": ("Emission reductions through improved efficiency of vehicle fleets", "Transport"),
    "AMS-III.BF.": ("Reduction of electricity consumption by replacing electric lamps by LED", "Energy demand"),
    "AMS-III.BG.": ("Emission reduction through sustainable charcoal production and consumption", "Energy demand"),
    "AMS-III.BL.": ("Integrated methodology for electrification of communities", "Energy industries (renewable sources)"),
    "AMS-III.BM.": ("Lightweight two and three wheeled personal transportation", "Transport"),
    "AMS-III.C.": ("Emission reductions by electric and hybrid vehicles", "Transport"),
    "AMS-III.D.": ("Methane recovery in animal manure management systems", "Agriculture"),
    "AMS-III.E.": ("Avoidance of methane production from decay of biomass through controlled combustion", "Waste handling and disposal"),
    "AMS-III.F.": ("Avoidance of methane emissions through controlled biological treatment of biomass", "Waste handling and disposal"),
    "AMS-III.G.": ("Landfill methane recovery", "Waste handling and disposal"),
    "AMS-III.H.": ("Methane recovery in wastewater treatment", "Waste handling and disposal"),
    "AMS-III.I.": ("Avoidance of methane production in wastewater treatment through replacement of anaerobic systems by aerobic systems", "Waste handling and disposal"),
    "AMS-III.J.": ("Avoidance of fossil fuel combustion for carbon dioxide production to be used as raw material for industrial processes", "Manufacturing industries"),
    "AMS-III.K.": ("Avoidance of methane release from charcoal production", "Waste handling and disposal"),
    "AMS-III.L.": ("Avoidance of methane production from biomass decay through controlled pyrolysis", "Waste handling and disposal"),
    "AMS-III.M.": ("Reduction in consumption of electricity by recovering soda from paper manufacturing process", "Manufacturing industries"),
    "AMS-III.Q.": ("Waste energy recovery", "Energy industries"),
    "AMS-III.R.": ("Methane recovery in agricultural activities at household/small farm level", "Agriculture"),
    "AMS-III.S.": ("Introduction of low-emission vehicles/technologies to commercial vehicle fleets", "Transport"),
    "AMS-III.Y.": ("Methane avoidance through separation of solids from wastewater or manure treatment systems", "Waste handling and disposal"),
    "AMS-III.Z.": ("Fuel switch, process improvement and energy efficiency in brick manufacture", "Manufacturing industries"),
    "AR-ACM0001": ("Afforestation and reforestation of degraded land", "Agriculture Forestry and Other Land Use"),
    "AR-ACM0002": ("Afforestation or reforestation of degraded land without displacement of pre-project activities", "Agriculture Forestry and Other Land Use"),
    "AR-ACM0003": ("Afforestation and reforestation of lands except wetlands", "Agriculture Forestry and Other Land Use"),
    "AR-AM0002": ("Restoration of degraded lands through afforestation/reforestation", "Agriculture Forestry and Other Land Use"),
    "AR-AM0003": ("Afforestation and reforestation of degraded land through tree planting, assisted natural regeneration and control of animal grazing", "Agriculture Forestry and Other Land Use"),
    "AR-AM0005": ("Afforestation and reforestation project activities implemented for industrial and/or commercial uses", "Agriculture Forestry and Other Land Use"),
    "AR-AM0007": ("Afforestation and reforestation of land currently under agricultural or pastoral use", "Agriculture Forestry and Other Land Use"),
    "AR-AM0010": ("Afforestation and reforestation project activities implemented on unmanaged grassland in reserve/protected areas", "Agriculture Forestry and Other Land Use"),
    "AR-AM0014": ("Afforestation and reforestation of degraded mangrove habitats", "Agriculture Forestry and Other Land Use"),
    "AR-AMS0001": ("Simplified baseline and monitoring methodology for small-scale CDM A/R project activities implemented on grasslands or croplands", "Agriculture Forestry and Other Land Use"),
    "AR-AMS0002": ("Simplified baseline and monitoring methodology for small-scale CDM A/R project activities implemented on settlements", "Agriculture Forestry and Other Land Use"),
    "AR-AMS0003": ("Simplified baseline and monitoring methodology for small-scale CDM afforestation and reforestation project activities implemented on wetlands", "Agriculture Forestry and Other Land Use"),
    "AR-AMS0004": ("Simplified baseline and monitoring methodology for small-scale agroforestry - afforestation and reforestation project activities under the CDM", "Agriculture Forestry and Other Land Use"),
    "AR-AMS0005": ("Simplified baseline and monitoring methodology for small-scale afforestation and reforestation project activities under the CDM implemented on lands having low inherent potential to support living biomass", "Agriculture Forestry and Other Land Use"),
    "AR-AMS0006": ("Simplified baseline and monitoring methodology for small-scale CDM A/R project activities implemented on lands with limited residual vegetation", "Agriculture Forestry and Other Land Use"),
    "AR-AMS0007": ("Simplified baseline and monitoring methodology for small-scale A/R CDM project activities implemented on lands having low inherent potential to support living biomass", "Agriculture Forestry and Other Land Use"),
}

VCS_METHODOLOGY_NAMES = {
    "VM0001": ("Refrigerant Leak Detection Efficiency", "Manufacturing industries"),
    "VM0002": ("New Cogeneration Facilities Supplying Less Carbon Intensive Electricity to Grid and Steam to Facilities", "Manufacturing industries"),
    "VM0003": ("Improved Forest Management through Extension of Rotation Age", "Agriculture Forestry and Other Land Use"),
    "VM0004": ("Avoided Planned Land Use Conversion in Peat Swamp Forests", "Agriculture Forestry and Other Land Use"),
    "VM0005": ("Conversion of Low-Productive Forest to High-Productive Forest", "Agriculture Forestry and Other Land Use"),
    "VM0006": ("Carbon Accounting for Mosaic and Landscape-scale REDD Projects", "Agriculture Forestry and Other Land Use"),
    "VM0007": ("REDD+ Methodology Framework (REDD+MF)", "Agriculture Forestry and Other Land Use"),
    "VM0008": ("Weatherization of Single Family and Multi-Family Buildings", "Energy demand"),
    "VM0009": ("Avoided Ecosystem Conversion", "Agriculture Forestry and Other Land Use"),
    "VM0010": ("Improved Forest Management: Conversion from Logged to Protected Forest", "Agriculture Forestry and Other Land Use"),
    "VM0011": ("Calculating GHG Benefits from Preventing Planned Degradation", "Agriculture Forestry and Other Land Use"),
    "VM0012": ("Improved Forest Management in Temperate and Boreal Forests (LtPF)", "Agriculture Forestry and Other Land Use"),
    "VM0013": ("Calculating Emission Reductions from Jet Engine Washing", "Transport"),
    "VM0014": ("Interception and Destruction of Fugitive Methane from Coal Bed Methane (CBM) Seeps", "Fugitive emissions from fuels"),
    "VM0015": ("Avoided Unplanned Deforestation", "Agriculture Forestry and Other Land Use"),
    "VM0016": ("Destruction of Ozone-Depleting Substances and Hydrofluorocarbons", "Chemical industries"),
    "VM0017": ("Adoption of Sustainable Agricultural Land Management", "Agriculture Forestry and Other Land Use"),
    "VM0018": ("Energy Efficiency and Solid Waste Diversion Activities within a Sustainable Community", "Energy demand"),
    "VM0019": ("Fuel Switch from Gasoline to Ethanol in Flex-Fuel Vehicle Fleets", "Transport"),
    "VM0020": ("Transport Energy Efficiency from Lightweight Pallets", "Transport"),
    "VM0021": ("Soil Carbon Quantification Methodology", "Agriculture Forestry and Other Land Use"),
    "VM0022": ("Quantifying N2O Emissions Reductions in Agricultural Crops through Nitrogen Management", "Agriculture"),
    "VM0023": ("Reduction of GHG Emissions in Propylene Oxide Production", "Chemical industries"),
    "VM0024": ("Coastal Wetland Creation", "Agriculture Forestry and Other Land Use"),
    "VM0025": ("Campus Clean Energy and Energy Efficiency", "Energy demand"),
    "VM0026": ("Sustainable Grassland Management (SGM)", "Agriculture Forestry and Other Land Use"),
    "VM0027": ("Rewetting Drained Tropical Peatlands", "Agriculture Forestry and Other Land Use"),
    "VM0028": ("Carpooling", "Transport"),
    "VM0029": ("Avoided Forest Degradation through Fire Management", "Agriculture Forestry and Other Land Use"),
    "VM0030": ("Pavement Application using Sulphur Substitute", "Manufacturing industries"),
    "VM0031": ("Precast Concrete Production using Sulphur Substitute", "Manufacturing industries"),
    "VM0032": ("Adoption of Sustainable Grasslands through Adjustment of Fire and Grazing", "Agriculture Forestry and Other Land Use"),
    "VM0033": ("Tidal Wetland and Seagrass Restoration", "Agriculture Forestry and Other Land Use"),
    "VM0034": ("Canadian Forest Carbon Offset Methodology", "Agriculture Forestry and Other Land Use"),
    "VM0035": ("Improved Forest Management through Reduced Impact Logging", "Agriculture Forestry and Other Land Use"),
    "VM0036": ("Avoided Conversion of Temperate and Boreal Peatlands", "Agriculture Forestry and Other Land Use"),
    "VM0037": ("Implementation of REDD+ Activities in Landscapes Affected by Mosaic Deforestation and Degradation", "Agriculture Forestry and Other Land Use"),
    "VM0038": ("Electric Vehicle Charging Systems", "Transport"),
    "VM0039": ("Use of Foam Stabilized Base and Emulsion Asphalt Mixtures in Pavement Application", "Manufacturing industries"),
    "VM0040": ("Greenhouse Gas Capture and Utilization in Plastic Materials", "Manufacturing industries"),
    "VM0041": ("Reduction of Enteric Methane Emissions from Ruminants through the Use of Feed Ingredients", "Agriculture"),
    "VM0042": ("Improved Agricultural Land Management", "Agriculture Forestry and Other Land Use"),
    "VM0043": ("CO2 Utilization in Concrete Production", "Manufacturing industries"),
    "VM0044": ("Biochar Utilization in Soil and Non-Soil Applications", "Agriculture Forestry and Other Land Use"),
    "VM0045": ("Improved Forest Management Using Dynamic Matched Baselines from National Forest Inventories", "Agriculture Forestry and Other Land Use"),
    "VM0046": ("Reducing Food Loss and Waste", "Waste handling and disposal"),
    "VM0047": ("Afforestation, Reforestation and Revegetation", "Agriculture Forestry and Other Land Use"),
    "VM0048": ("Reducing Emissions from Deforestation and Forest Degradation", "Agriculture Forestry and Other Land Use"),
    "VM0049": ("Carbon Capture and Storage", "Energy industries"),
    "VM0050": ("Energy Efficiency and Fuel-Switch Measures in Cookstoves", "Energy demand"),
    "VM0051": ("Improved Management in Rice Production Systems", "Agriculture"),
    "VM0052": ("Accelerated Retirement of Coal-Fired Power Plants Using a Just Transition Approach", "Energy industries"),
    "VMR0001": ("Revisions to ACM0002 to Include Renewable Energy CPA under a CDM PoA", "Energy industries (renewable sources)"),
    "VMR0002": ("Revisions to ACM0008 to Include Methane Capture and Destruction from Abandoned Mines", "Fugitive emissions from fuels"),
    "VMR0003": ("Revisions to AMS-III.Y to Include Use of Organic Bedding Material", "Agriculture"),
    "VMR0004": ("Improved Efficiency of Fleet Vehicles", "Transport"),
    "VMR0005": ("Installation of Low-Flow Water Devices", "Energy demand"),
    "VMR0006": ("Energy Efficiency and Fuel Switch Measures in Thermal Applications", "Energy demand"),
    "VMR0007": ("Recovery and Recycling of Materials from Solid Wastes (AMS-III.AJ. Revision)", "Waste handling and disposal"),
    "VMR0008": ("Recovery and Recycling of Materials from E-waste (AMS-III.BA. Revision)", "Waste handling and disposal"),
    "VMR0009": ("Avoided Emissions from Biomass Wastes through Use as Feedstock (AM0057 Revision)", "Energy industries"),
    "VMR0010": ("Electricity Supply for Ships", "Transport"),
    "VMR0011": ("Switch from Non-Renewable Biomass for Thermal Applications by the User", "Energy demand"),
    "VMR0012": ("Production of Geopolymer Cement", "Manufacturing industries"),
    "VMR0013": ("Lightweight Two- and Three-Wheeled Personal Transportation (AMS-III.BM. Revision)", "Transport"),
    "VMR0014": ("Electric and Hybrid Vehicles and Mobile Machinery (AMS-III.C. Revision)", "Transport"),
    "VMR0015": ("Low Greenhouse Gas Emitting Safe Drinking Water Production Systems (AMS-III.AV. Revision)", "Energy demand"),
    "VMR0016": ("Flaring or Use of Landfill Gas (ACM0001 Revision)", "Waste handling and disposal"),
    "VMD0038": ("Leakage from Displacement of Cattle", "Agriculture Forestry and Other Land Use"),
}

GS_METHODOLOGIES = {
    "GS-TPDDTEC": {
        "name": "Technologies and Practices to Displace Decentralized Thermal Energy Consumption (TPDDTEC)",
        "sector": "Energy demand",
        "applicability": "Cookstoves, water heating, space heating, and other thermal energy devices displacing decentralized thermal energy consumption from non-renewable sources",
        "source_url": "https://globalgoals.goldstandard.org/standards/431_V4.0_EE_Technologies-and-Practices-to-Displace-Decentralized-Thermal-Energy-Consumption.pdf",
    },
    "GS-SIMPLIFIED-COOKSTOVE": {
        "name": "Simplified Methodology for Clean and Efficient Cookstoves",
        "sector": "Energy demand",
        "applicability": "Improved cookstoves for household use, replacing traditional three-stone fires or inefficient stoves",
    },
    "GS-IMPROVED-COOKSTOVE": {
        "name": "Methodology for Improved Cookstoves and Kitchen Regimes",
        "sector": "Energy demand",
        "applicability": "Improved cookstoves and kitchen ventilation/regime changes for household cooking",
    },
    "GS-MS-COOKSTOVE": {
        "name": "Microscale Simplified Methodology for Efficient Cookstoves",
        "sector": "Energy demand",
        "applicability": "Microscale improved cookstove projects",
    },
    "GS-SAFE-WATER": {
        "name": "Methodology for Emission Reductions from Safe Drinking Water Supply",
        "sector": "Energy demand",
        "applicability": "Water purification and treatment systems that displace boiling of water",
    },
    "GS-WASH": {
        "name": "Water Access and WASH Methodology",
        "sector": "Energy demand",
        "applicability": "Water, sanitation and hygiene projects displacing fuel use for water treatment",
        "source_url": "https://globalgoals.goldstandard.org/standards/432_V1.1_EE_Water-Access-and-WASH-Methodology.pdf",
    },
    "GS-METERED-ENERGY": {
        "name": "Methodology for Metered and Measured Energy Cooking Devices",
        "sector": "Energy demand",
        "applicability": "Electric and LPG cooking devices with metered energy measurement",
    },
    "GS-BIODIGESTER": {
        "name": "Baseline and Monitoring Methodology for Biodigester",
        "sector": "Energy demand",
        "applicability": "Biodigester/biogas systems for households and small farms",
    },
    "GS-MANURE": {
        "name": "Revised Methodology for Manure Management Systems and MSW",
        "sector": "Agriculture",
        "applicability": "Animal manure management and municipal solid waste treatment",
    },
    "GS-BIODIESEL": {
        "name": "Biodiesel from Waste Oil or Fat",
        "sector": "Energy industries (renewable sources)",
        "applicability": "Production of biodiesel from waste cooking oil or animal fat",
    },
    "GS-AR": {
        "name": "Afforestation/Reforestation GHG Emissions Reduction and Sequestration Methodology",
        "sector": "Agriculture Forestry and Other Land Use",
        "applicability": "Afforestation and reforestation projects on degraded or non-forest land",
    },
    "GS-SOIL": {
        "name": "Soil Organic Carbon Framework Methodology",
        "sector": "Agriculture Forestry and Other Land Use",
        "applicability": "Agricultural practices that increase soil organic carbon",
    },
    "GS-ENTERIC": {
        "name": "Methodology for Reducing Methane Emissions from Enteric Fermentation in Beef Cattle through Application of Feed Supplements",
        "sector": "Agriculture",
        "applicability": "Feed additives that reduce enteric methane from cattle",
    },
    "GS-RICE": {
        "name": "Methane Emission Reduction by Adjusted Water Management Practice in Rice Cultivation",
        "sector": "Agriculture",
        "applicability": "Alternate wetting and drying (AWD) in rice paddies",
    },
    "GS-ANIMAL-WASTE": {
        "name": "Methodology for Animal Waste Management and Biogas Application",
        "sector": "Agriculture",
        "applicability": "Biogas from animal waste in farming operations",
    },
    "GS-ELECTRIFICATION": {
        "name": "Microscale Electrification and Energization",
        "sector": "Energy industries (renewable sources)",
        "applicability": "Off-grid and mini-grid renewable energy systems for rural electrification",
    },
    "GS-FUEL-SWITCH-BIOMASS": {
        "name": "Ecologically Sound Fuel Switch to Biomass",
        "sector": "Energy demand",
        "applicability": "Fuel switching from fossil fuels to sustainable biomass",
    },
    "GS-HULL-COATINGS": {
        "name": "Advanced Hull Coatings for Maritime Vessels",
        "sector": "Transport",
        "applicability": "Improved hull coatings that reduce fuel consumption in shipping",
    },
    "GS-SHIPPING-EE": {
        "name": "Retrofit Energy Efficiency Measures in Shipping",
        "sector": "Transport",
        "applicability": "Energy efficiency retrofits for existing maritime vessels",
    },
    "GS-COAL-IGNITION": {
        "name": "Alternative Ignition Coal Fires",
        "sector": "Energy demand",
        "applicability": "Top-lit updraft (TLUD) or alternative coal ignition methods reducing emissions",
    },
    "GS-CHARCOAL": {
        "name": "Emission Reduction through Sustainable Charcoal Production and Consumption",
        "sector": "Energy demand",
        "applicability": "Improved charcoal production kilns and efficient charcoal stoves",
    },
}

_GS_RAW_TO_CODE = [
    (r"GS\s+TPDDTEC", "GS-TPDDTEC"),
    (r"The Gold Standard Simplified Methodology for Clean and Efficient Cookstoves", "GS-SIMPLIFIED-COOKSTOVE"),
    (r"GS MS Simplified Methodology for Efficient Cookstoves", "GS-MS-COOKSTOVE"),
    (r"GS Methodology for Improved Cook\s*stoves and Kitchen Regimes", "GS-IMPROVED-COOKSTOVE"),
    (r"GS Methodology for emission reductions from safe drinking water supply", "GS-SAFE-WATER"),
    (r"GS Water Access and WASH Methodology", "GS-WASH"),
    (r"Methodology for Metered.*Measured Energy Cooking Devices", "GS-METERED-ENERGY"),
    (r"GS Baseline and Monitoring Methodology Biodigester", "GS-BIODIGESTER"),
    (r"GS Revised Methodology for Manure Management Systems", "GS-MANURE"),
    (r"GS Biodiesel from Waste Oil or Fat", "GS-BIODIESEL"),
    (r"Afforestation/Reforestation GHG Emissions Reduction", "GS-AR"),
    (r"Soil Organic Carbon Framework Methodology", "GS-SOIL"),
    (r"Methodology [Ff]or [Rr]educing [Mm]ethane [Ee]missions [Ff]rom [Ee]nteric [Ff]ermentation", "GS-ENTERIC"),
    (r"Methane Emission Reduction [Bb]y Adjusted Water Management Practice [Ii]n Rice", "GS-RICE"),
    (r"Methodology for animal waste management and biogas", "GS-ANIMAL-WASTE"),
    (r"GS MS Microscale Electrification and Energization", "GS-ELECTRIFICATION"),
    (r"GS SS Ecologically Sound Fuel Switch to Biomass", "GS-FUEL-SWITCH-BIOMASS"),
    (r"GS Advanced Hull Coatings", "GS-HULL-COATINGS"),
    (r"GS Retrofit Energy Efficiency Measures in Shipping", "GS-SHIPPING-EE"),
    (r"GS Alternative Ignition Coal Fires", "GS-COAL-IGNITION"),
    (r"AMS-III\.BG.*[Cc]harcoal", "GS-CHARCOAL"),
]

CDM_CODE_RE = re.compile(
    r'^((?:AR-)?(?:ACM|AMS|AM)\d*(?:-[A-Z]+(?:\.[A-Z]+)?\.?)?|VM[DR]?\d{4})'
)

SKIP_VALUES = {"Not provided", "Other", "Not", "Other"}


def _normalize_cdm_code(raw_code):
    raw_code = raw_code.strip().rstrip(".")
    raw_code = re.sub(r'\s+', '', raw_code)
    raw_code = raw_code.replace(":", "")
    if raw_code.startswith("AMS-") and not raw_code.endswith("."):
        parts = raw_code.split(".")
        if len(parts) >= 2:
            raw_code = raw_code + "."
    return raw_code


def _extract_version(raw_str):
    m = re.search(r'[vV]\s*(\d+(?:\.\d+)?)', raw_str)
    if m:
        return m.group(1)
    m = re.search(r'[Vv]ersion\s+(\d+(?:\.\d+)?)', raw_str)
    if m:
        return m.group(1)
    return None


def _map_gs_raw_to_code(raw_methodology):
    if not raw_methodology:
        return None, None
    for pattern, code in _GS_RAW_TO_CODE:
        if re.search(pattern, raw_methodology, re.IGNORECASE):
            version = _extract_version(raw_methodology)
            return code, version
    return None, None


def _parse_methodology_string(raw_str, registry):
    results = []
    if not raw_str or raw_str.strip() in SKIP_VALUES:
        return results

    if registry == "goldstandard":
        gs_code, gs_version = _map_gs_raw_to_code(raw_str)
        if gs_code:
            results.append((gs_code, gs_version))

        cdm_matches = CDM_CODE_RE.findall(raw_str)
        for code in cdm_matches:
            code = _normalize_cdm_code(code)
            results.append((code, None))

        if not results:
            cdm_match = CDM_CODE_RE.match(raw_str.split(" ")[0] if " " in raw_str else raw_str)
            if cdm_match:
                code = _normalize_cdm_code(cdm_match.group(1))
                results.append((code, None))

        return results

    parts = re.split(r'[;,]', raw_str)
    for part in parts:
        part = part.strip()
        if not part or part in SKIP_VALUES:
            continue
        m = CDM_CODE_RE.match(part)
        if m:
            code = _normalize_cdm_code(m.group(1))
            results.append((code, None))
    return results


def _classify_methodology(code):
    for prefix, info in sorted(METHODOLOGY_FAMILIES.items(), key=lambda x: -len(x[0])):
        if code.upper().startswith(prefix.upper()):
            return info
    if code.startswith("GS-"):
        return {"standard": "GoldStandard", "category": "Gold Standard Methodology"}
    return {"standard": "Other", "category": "Other"}


def _get_known_info(code):
    if code in CDM_METHODOLOGY_NAMES:
        name, sector = CDM_METHODOLOGY_NAMES[code]
        return {"name": name, "sector": sector}
    if code in VCS_METHODOLOGY_NAMES:
        name, sector = VCS_METHODOLOGY_NAMES[code]
        return {"name": name, "sector": sector}
    if code in GS_METHODOLOGIES:
        return GS_METHODOLOGIES[code]
    return {}


def populate_methodologies_from_projects():
    with get_cursor() as cur:
        cur.execute(
            "SELECT methodology, registry FROM carbon_projects "
            "WHERE methodology IS NOT NULL AND methodology != ''"
        )
        rows = cur.fetchall()

    code_counts = {}
    code_versions = {}
    for r in rows:
        raw = r["methodology"]
        registry = r["registry"]
        parsed = _parse_methodology_string(raw, registry)
        for code, version in parsed:
            code_counts[code] = code_counts.get(code, 0) + 1
            if version:
                code_versions.setdefault(code, set()).add(version)

    with get_cursor() as cur:
        cur.execute("DELETE FROM methodologies")

    count = 0
    for code in sorted(code_counts.keys()):
        proj_count = code_counts[code]
        known = _get_known_info(code)
        family = _classify_methodology(code)

        name = known.get("name")
        standard = known.get("standard") or family.get("standard")
        category = known.get("category") or family.get("category")
        sector = known.get("sector")
        applicability = known.get("applicability")
        source_url = known.get("source_url")
        status = known.get("status", "active")
        superseded_by = known.get("superseded_by")

        versions = code_versions.get(code, set())
        description = None
        if versions:
            sorted_versions = sorted(versions, key=lambda v: [int(x) for x in v.split(".")] if all(x.isdigit() for x in v.split(".")) else [0])
            description = f"Known versions: {', '.join('v' + v for v in sorted_versions)}"

        upsert_methodology(
            code=code,
            name=name,
            standard=standard,
            category=category,
            sector=sector,
            status=status,
            applicability=applicability,
            description=description,
            source_url=source_url,
            superseded_by=superseded_by,
            project_count=proj_count,
        )
        count += 1

    logger.info("Populated %d methodologies from project data", count)
    return count


def enrich_from_verra_api():
    try:
        from carbongpt.repository.methodology_sync import fetch_verra_methodology_list_api
    except ImportError:
        logger.warning("Cannot import methodology_sync for enrichment")
        return 0

    api_results = fetch_verra_methodology_list_api()
    if not api_results:
        logger.info("No results from Verra API for enrichment")
        return 0

    verra_names = {}
    for item in api_results:
        code = item.get("code", "")
        title = item.get("title", "")
        if not code or not title:
            continue
        clean = re.sub(r'^(Revision to |Minor Revision to |Proposed Revision to |Major Revision to )', '', title)
        clean = re.sub(r'^' + re.escape(code) + r'\s*', '', clean)
        clean = re.sub(r',\s*v[\d.]+$', '', clean).strip()
        if clean:
            verra_names[code] = clean

    updated = 0
    with get_cursor() as cur:
        cur.execute("SELECT code, name FROM methodologies WHERE standard = 'Verra'")
        rows = cur.fetchall()

    for row in rows:
        code = row["code"]
        existing_name = row["name"]
        if existing_name and existing_name.strip():
            continue
        api_name = verra_names.get(code)
        if api_name:
            with get_cursor() as cur:
                cur.execute(
                    "UPDATE methodologies SET name = %s, updated_at = NOW() WHERE code = %s",
                    (api_name, code),
                )
            updated += 1
            logger.info("Enriched %s: %s", code, api_name)

    logger.info("Enriched %d Verra methodologies from API", updated)
    return updated
