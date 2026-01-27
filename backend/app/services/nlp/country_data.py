"""
Country reference data for tagging.
Maps country names, demonyms, cities, and abbreviations to ISO-3166 alpha-2 codes.
"""

from typing import Dict, List, Set

# Country mappings: ISO code -> list of keywords (names, demonyms, cities, abbreviations)
COUNTRY_KEYWORDS: Dict[str, List[str]] = {
    # United States
    "US": [
        "united states", "usa", "u.s.", "u.s.a", "america", "american", "americans",
        "washington dc", "new york", "california", "texas", "florida",
    ],
    
    # United Kingdom
    "GB": [
        "united kingdom", "uk", "u.k.", "britain", "great britain", "british",
        "england", "english", "scotland", "scottish", "wales", "welsh",
        "northern ireland", "london", "manchester", "birmingham",
    ],
    
    # Germany
    "DE": [
        "germany", "german", "germans", "deutschland",
        "berlin", "munich", "hamburg", "frankfurt",
    ],
    
    # France
    "FR": [
        "france", "french", "paris", "lyon", "marseille",
    ],
    
    # China
    "CN": [
        "china", "chinese", "beijing", "shanghai", "guangzhou", "shenzhen",
        "prc", "people's republic of china",
    ],
    
    # India
    "IN": [
        "india", "indian", "indians", "new delhi", "delhi", "mumbai",
        "bangalore", "bengaluru", "hyderabad",
    ],
    
    # Japan
    "JP": [
        "japan", "japanese", "tokyo", "osaka", "kyoto",
    ],
    
    # South Korea
    "KR": [
        "south korea", "korea", "korean", "koreans", "seoul", "busan",
        "republic of korea", "rok",
    ],
    
    # North Korea
    "KP": [
        "north korea", "dprk", "pyongyang", "democratic people's republic of korea",
    ],
    
    # Australia
    "AU": [
        "australia", "australian", "australians", "sydney", "melbourne",
        "brisbane", "perth", "canberra",
    ],
    
    # Canada
    "CA": [
        "canada", "canadian", "canadians", "toronto", "montreal", "vancouver",
        "ottawa", "calgary",
    ],
    
    # Spain
    "ES": [
        "spain", "spanish", "madrid", "barcelona", "seville",
    ],
    
    # Italy
    "IT": [
        "italy", "italian", "italians", "rome", "milan", "naples",
        "florence", "venice",
    ],
    
    # Netherlands
    "NL": [
        "netherlands", "dutch", "holland", "amsterdam", "rotterdam",
        "the hague",
    ],
    
    # Belgium
    "BE": [
        "belgium", "belgian", "belgians", "brussels", "antwerp",
    ],
    
    # Poland
    "PL": [
        "poland", "polish", "poles", "warsaw", "krakow", "gdansk",
    ],
    
    # Sweden
    "SE": [
        "sweden", "swedish", "swedes", "stockholm", "gothenburg",
    ],
    
    # Norway
    "NO": [
        "norway", "norwegian", "norwegians", "oslo", "bergen",
    ],
    
    # Denmark
    "DK": [
        "denmark", "danish", "danes", "copenhagen",
    ],
    
    # Brazil
    "BR": [
        "brazil", "brazilian", "brazilians", "brasilia", "sao paulo",
        "rio de janeiro", "rio",
    ],
    
    # Mexico
    "MX": [
        "mexico", "mexican", "mexicans", "mexico city", "guadalajara",
    ],
    
    # Argentina
    "AR": [
        "argentina", "argentinian", "argentinians", "buenos aires",
    ],
    
    # Chile
    "CL": [
        "chile", "chilean", "chileans", "santiago",
    ],
    
    # South Africa
    "ZA": [
        "south africa", "south african", "south africans",
        "johannesburg", "cape town", "pretoria", "durban",
    ],
    
    # Saudi Arabia
    "SA": [
        "saudi arabia", "saudi", "saudis", "riyadh", "jeddah",
    ],
    
    # United Arab Emirates
    "AE": [
        "united arab emirates", "uae", "u.a.e", "emirates", "dubai", "abu dhabi",
    ],
    
    # Israel
    "IL": [
        "israel", "israeli", "israelis", "jerusalem", "tel aviv",
    ],
    
    # Turkey
    "TR": [
        "turkey", "turkish", "turks", "ankara", "istanbul",
    ],
    
    # Russia
    "RU": [
        "russia", "russian", "russians", "moscow", "st petersburg",
        "petersburg", "soviet", "ussr",
    ],
    
    # Ukraine
    "UA": [
        "ukraine", "ukrainian", "ukrainians", "kyiv", "kiev", "odessa",
    ],
    
    # Egypt
    "EG": [
        "egypt", "egyptian", "egyptians", "cairo",
    ],
    
    # Nigeria
    "NG": [
        "nigeria", "nigerian", "nigerians", "lagos", "abuja",
    ],
    
    # Kenya
    "KE": [
        "kenya", "kenyan", "kenyans", "nairobi",
    ],
    
    # Indonesia
    "ID": [
        "indonesia", "indonesian", "indonesians", "jakarta",
    ],
    
    # Malaysia
    "MY": [
        "malaysia", "malaysian", "malaysians", "kuala lumpur",
    ],
    
    # Singapore
    "SG": [
        "singapore", "singaporean", "singaporeans",
    ],
    
    # Vietnam
    "VN": [
        "vietnam", "vietnamese", "hanoi", "ho chi minh",
    ],
    
    # Thailand
    "TH": [
        "thailand", "thai", "bangkok",
    ],
    
    # Philippines
    "PH": [
        "philippines", "filipino", "filipinos", "manila",
    ],
    
    # New Zealand
    "NZ": [
        "new zealand", "new zealander", "new zealanders", "kiwi", "kiwis",
        "wellington", "auckland",
    ],
    
    # Ireland
    "IE": [
        "ireland", "irish", "dublin",
    ],
    
    # Portugal
    "PT": [
        "portugal", "portuguese", "lisbon", "porto",
    ],
    
    # Greece
    "GR": [
        "greece", "greek", "greeks", "athens",
    ],
    
    # Austria
    "AT": [
        "austria", "austrian", "austrians", "vienna",
    ],
    
    # Switzerland
    "CH": [
        "switzerland", "swiss", "zurich", "geneva", "bern",
    ],
    
    # Finland
    "FI": [
        "finland", "finnish", "finns", "helsinki",
    ],
    
    # Czech Republic
    "CZ": [
        "czech republic", "czech", "czechs", "czechia", "prague",
    ],
    
    # Hungary
    "HU": [
        "hungary", "hungarian", "hungarians", "budapest",
    ],
    
    # Romania
    "RO": [
        "romania", "romanian", "romanians", "bucharest",
    ],
}


# Ambiguous terms that need context or should be excluded
# Georgia can be US state or country GE
AMBIGUOUS_KEYWORDS: Dict[str, str] = {
    "georgia": "GE",  # Country code, but needs careful handling
}


# Special region/organization mappings (not countries but useful metadata)
REGION_KEYWORDS: Dict[str, List[str]] = {
    "EU": [
        "european union", "eu", "e.u.", "brussels", "european commission",
        "european parliament", "eurozone",
    ],
}


def detect_countries_in_text(text: str) -> List[str]:
    """
    Detect country codes in text based on keyword mentions.
    
    Args:
        text: Input text (e.g., user question)
        
    Returns:
        List of ISO-3166 alpha-2 codes detected.
    """
    if not text:
        return []
        
    text_lower = text.lower()
    detected = set()
    
    # Sort codes to ensure consistent behavior if needed
    for code, keywords in COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            # Match word boundaries to avoid catching "India" in "Indiana"
            import re
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                detected.add(code)
                break  # Found this country, move to next code
                
    return sorted(list(detected))


def get_all_keywords() -> Set[str]:
    """Get set of all country keywords for validation."""
    all_keywords = set()
    for keywords in COUNTRY_KEYWORDS.values():
        all_keywords.update(keywords)
    return all_keywords


def get_country_for_keyword(keyword: str) -> str:
    """
    Get ISO country code for a keyword.
    
    Args:
        keyword: Lowercase keyword to search
        
    Returns:
        ISO alpha-2 code or empty string if not found
    """
    keyword = keyword.lower().strip()
    
    for code, keywords in COUNTRY_KEYWORDS.items():
        if keyword in keywords:
            return code
    
    # Check ambiguous keywords
    if keyword in AMBIGUOUS_KEYWORDS:
        return AMBIGUOUS_KEYWORDS[keyword]
    
    return ""
