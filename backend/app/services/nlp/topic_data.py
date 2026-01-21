"""
Topic taxonomy data for energy transition news tagging.
"""

from typing import Dict, List, Tuple

# Topic taxonomy: topic_id -> (positive_keywords, negative_keywords)
# Positive keywords: increase score when matched
# Negative keywords: decrease score when matched (helps differentiate similar topics)

TOPIC_KEYWORDS: Dict[str, Tuple[List[str], List[str]]] = {
    "policy_regulation": (
        # Positive keywords
        [
            "policy", "regulation", "regulatory", "legislation", "law", "mandate",
            "government", "federal", "state", "national", "parliament", "congress",
            "directive", "compliance", "subsidy", "subsidies", "tax credit",
            "incentive", "carbon tax", "emissions trading", "cap and trade",
            "net zero", "climate target", "climate goal", "climate pledge",
            "paris agreement", "cop27", "cop28", "cop29", "climate summit",
            "renewable energy standard", "res", "clean energy standard",
            "energy policy", "climate policy", "environmental policy",
        ],
        # Negative keywords
        ["technical", "engineering", "manufacturing"],
    ),
    
    "power_grid": (
        [
            "grid", "power grid", "electricity grid", "transmission", "distribution",
            "grid infrastructure", "grid modernization", "smart grid",
            "interconnection", "interconnector", "grid connection",
            "transmission line", "power line", "substation",
            "grid operator", "grid stability", "grid reliability",
            "grid congestion", "grid capacity", "grid expansion",
            "energy storage grid", "grid scale", "utility scale",
            "load balancing", "frequency regulation", "ancillary services",
            "demand response", "virtual power plant", "vpp",
        ],
        ["solar panel", "wind turbine", "battery cell"],
    ),
    
    "renewables_solar": (
        [
            "solar", "photovoltaic", "pv", "solar panel", "solar farm",
            "solar power", "solar energy", "solar project", "solar plant",
            "solar installation", "rooftop solar", "utility scale solar",
            "concentrated solar", "csp", "solar thermal",
            "solar cell", "solar module", "bifacial", "perovskite",
            "solar capacity", "solar generation", "solar irradiance",
        ],
        ["wind", "battery", "hydrogen"],
    ),
    
    "renewables_wind": (
        [
            "wind", "wind power", "wind energy", "wind farm", "wind turbine",
            "wind project", "wind installation", "wind capacity",
            "onshore wind", "offshore wind", "floating wind",
            "wind generation", "wind developer", "wind industry",
            "turbine blade", "nacelle", "wind speed", "capacity factor",
        ],
        ["solar", "battery", "hydrogen"],
    ),
    
    "storage_batteries": (
        [
            "battery", "batteries", "energy storage", "battery storage",
            "lithium ion", "lithium-ion", "li-ion", "solid state battery",
            "battery cell", "battery pack", "battery system",
            "battery technology", "battery chemistry", "battery capacity",
            "battery manufacturer", "battery plant", "gigafactory",
            "flow battery", "vanadium", "grid scale storage",
            "stationary storage", "utility scale battery",
            "charge", "discharge", "cycling", "degradation",
        ],
        ["electric vehicle", "ev", "car", "automotive"],
    ),
    
    "hydrogen": (
        [
            "hydrogen", "h2", "green hydrogen", "blue hydrogen", "grey hydrogen",
            "hydrogen production", "electrolyzer", "electrolysis",
            "hydrogen fuel", "hydrogen economy", "hydrogen strategy",
            "fuel cell", "hydrogen storage", "hydrogen transport",
            "ammonia", "synthetic fuel", "e-fuel", "power to gas",
            "hydrogen pipeline", "hydrogen infrastructure",
        ],
        ["battery", "solar", "wind"],
    ),
    
    "ev_transport": (
        [
            "electric vehicle", "ev", "evs", "electric car", "electric truck",
            "electric bus", "battery electric vehicle", "bev",
            "plug-in hybrid", "phev", "hybrid electric",
            "charging station", "charging infrastructure", "ev charger",
            "fast charging", "dc fast charging", "level 2 charging",
            "vehicle to grid", "v2g", "bidirectional charging",
            "automotive", "automobile", "passenger vehicle",
            "tesla", "rivian", "lucid", "nio", "byd electric",
            "ev adoption", "ev sales", "ev market", "ev battery",
        ],
        ["stationary storage", "grid scale"],
    ),
    
    "carbon_markets_ccus": (
        [
            "carbon capture", "ccs", "ccus", "carbon storage",
            "carbon sequestration", "direct air capture", "dac",
            "carbon removal", "carbon credit", "carbon offset",
            "carbon market", "carbon trading", "carbon price",
            "emissions reduction", "co2 capture", "carbon dioxide removal",
            "negative emissions", "carbon neutral", "carbon negative",
            "voluntary carbon market", "compliance carbon market",
        ],
        [],
    ),
    
    "oil_gas_transition": (
        [
            "oil and gas", "fossil fuel", "petroleum", "natural gas",
            "oil company", "gas company", "oil major", "supermajor",
            "bp", "shell", "exxon", "chevron", "totalenergies", "equinor",
            "energy transition", "diversification", "renewable transition",
            "fossil fuel phase out", "stranded assets",
            "oil production", "gas production", "upstream", "downstream",
            "refinery", "petrochemical", "lng", "liquefied natural gas",
        ],
        ["renewable only", "clean energy only"],
    ),
    
    "corporate_finance": (
        [
            "investment", "financing", "funding", "capital",
            "merger", "acquisition", "m&a", "deal", "transaction",
            "ipo", "initial public offering", "private equity", "venture capital",
            "stock", "share price", "valuation", "market cap",
            "earnings", "revenue", "profit", "loss", "financial results",
            "investor", "shareholder", "dividend", "bond", "debt",
            "fundraising", "capital raise", "series a", "series b",
            "billion dollar", "million dollar", "usd", "eur",
        ],
        [],
    ),
    
    "critical_minerals_supply_chain": (
        [
            "lithium", "cobalt", "nickel", "rare earth", "graphite",
            "copper", "manganese", "vanadium",
            "mining", "mineral", "supply chain", "raw material",
            "critical mineral", "strategic mineral",
            "mineral processing", "refining", "smelting",
            "mineral exploration", "mineral deposit", "mineral reserves",
            "supply security", "supply risk", "geopolitical risk",
            "mineral demand", "mineral shortage", "mineral price",
        ],
        [],
    ),
}


# Topic display names
TOPIC_NAMES: Dict[str, str] = {
    "policy_regulation": "Policy & Regulation",
    "power_grid": "Power Grid & Infrastructure",
    "renewables_solar": "Solar Energy",
    "renewables_wind": "Wind Energy",
    "storage_batteries": "Battery Storage",
    "hydrogen": "Hydrogen & Fuel Cells",
    "ev_transport": "Electric Vehicles & Transport",
    "carbon_markets_ccus": "Carbon Markets & CCUS",
    "oil_gas_transition": "Oil & Gas Transition",
    "corporate_finance": "Corporate & Finance",
    "critical_minerals_supply_chain": "Critical Minerals & Supply Chain",
}


def get_all_topics() -> List[str]:
    """Get list of all topic IDs."""
    return list(TOPIC_KEYWORDS.keys())


def get_topic_name(topic_id: str) -> str:
    """Get display name for topic."""
    return TOPIC_NAMES.get(topic_id, topic_id)
