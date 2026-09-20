"""
schemes_data.py
────────────────
Static + location-filtered government agricultural schemes and contacts for India.
Structured as Python dicts so it's easy to extend or swap with a real API/DB later.
"""

SCHEMES = [
  {
    "id": "pm-kisan",
    "name": "PM-KISAN",
    "full_name": "Pradhan Mantri Kisan Samman Nidhi",
    "category": "Income Support",
    "icon": "💰",
    "benefit": "₹6,000/year direct income support in 3 equal installments",
    "eligibility": "All small and marginal farmers owning cultivable land",
    "documents": ["Aadhaar Card", "Bank Account (linked to Aadhaar)", "Land Records (Khasra/Khatauni)"],
    "how_to_apply": "Apply online at pmkisan.gov.in or visit nearest CSC/Gram Panchayat",
    "link": "https://pmkisan.gov.in",
    "deadline": "Ongoing",
    "crops": ["All Crops"],
    "states": ["All States"],
    "languages": {"te": "పీఎం కిసాన్ - వార్షిక ₹6,000 సహాయం", "hi": "पीएम किसान - वार्षिक ₹6,000 सहायता"},
  },
  {
    "id": "pmfby",
    "name": "PMFBY",
    "full_name": "Pradhan Mantri Fasal Bima Yojana",
    "category": "Crop Insurance",
    "icon": "🛡️",
    "benefit": "Crop insurance at low premium — Kharif: 2%, Rabi: 1.5%, Horticulture: 5%",
    "eligibility": "All farmers growing notified crops in notified areas",
    "documents": ["Aadhaar Card", "Bank Passbook", "Land Records", "Sowing Certificate"],
    "how_to_apply": "Apply at nearest bank branch, CSC, or pmfby.gov.in before cut-off date",
    "link": "https://pmfby.gov.in",
    "deadline": "Before sowing season ends",
    "crops": ["Wheat", "Rice", "Cotton", "Maize", "Soybean", "Groundnut", "Sugarcane"],
    "states": ["All States"],
    "languages": {"te": "పంట బీమా - తక్కువ ప్రీమియంతో పంట రక్షణ", "hi": "फसल बीमा - कम प्रीमियम पर फसल सुरक्षा"},
  },
  {
    "id": "kcc",
    "name": "KCC",
    "full_name": "Kisan Credit Card",
    "category": "Credit & Loans",
    "icon": "💳",
    "benefit": "Short-term credit up to ₹3 lakh at 4% interest rate (with subvention)",
    "eligibility": "Farmers, tenant farmers, sharecroppers, and SHGs",
    "documents": ["Aadhaar", "PAN Card", "Land Records", "Passport Photo", "Bank Account"],
    "how_to_apply": "Apply at any nationalized bank, cooperative bank or RRB",
    "link": "https://www.rbi.org.in",
    "deadline": "Ongoing",
    "crops": ["All Crops"],
    "states": ["All States"],
    "languages": {"te": "కిసాన్ క్రెడిట్ కార్డ్ - 4% వడ్డీతో రుణం", "hi": "किसान क्रेडिट कार्ड - 4% ब्याज पर ऋण"},
  },
  {
    "id": "pkvy",
    "name": "PKVY",
    "full_name": "Paramparagat Krishi Vikas Yojana",
    "category": "Organic Farming",
    "icon": "🌱",
    "benefit": "₹50,000/hectare for 3 years for organic farming cluster development",
    "eligibility": "Groups of 50+ farmers forming clusters of 50 acres",
    "documents": ["Group Registration", "Land Records", "Bank Account"],
    "how_to_apply": "Apply through State Agriculture Department or krishi.gov.in",
    "link": "https://pgsindia-ncof.gov.in",
    "deadline": "Check state portal",
    "crops": ["All Crops"],
    "states": ["All States"],
    "languages": {"te": "సేంద్రీయ వ్యవసాయం - ₹50,000/హెక్టారు సహాయం", "hi": "जैविक खेती - ₹50,000/हेक्टेयर सहायता"},
  },

  {
    "id": "smam",
    "name": "SMAM",
    "full_name": "Sub-Mission on Agricultural Mechanisation",
    "category": "Equipment Subsidy",
    "icon": "🚜",
    "benefit": "40-50% subsidy on farm machinery and equipment (SC/ST farmers get 50%)",
    "eligibility": "Individual farmers, FPOs, cooperatives",
    "documents": ["Aadhaar", "Land Records", "Caste Certificate (if applicable)", "Bank Account"],
    "how_to_apply": "Apply at District Agriculture Office or agrimachinery.nic.in",
    "link": "https://agrimachinery.nic.in",
    "deadline": "Ongoing",
    "crops": ["Wheat", "Rice", "Maize", "Sugarcane", "Cotton"],
    "states": ["All States"],
    "languages": {"te": "వ్యవసాయ యంత్రాలపై 40-50% సబ్సిడీ", "hi": "कृषि मशीनरी पर 40-50% सब्सिडी"},
  },
  {
    "id": "andhra-rytu-bandhu",
    "name": "Rythu Bandhu",
    "full_name": "Rythu Bandhu Scheme (Andhra Pradesh)",
    "category": "Income Support",
    "icon": "🌾",
    "benefit": "₹10,000/acre/season investment support for crop cultivation",
    "eligibility": "All farmer land owners in Andhra Pradesh",
    "documents": ["Aadhaar", "Pattadar Passbook / Land Records", "Bank Account"],
    "how_to_apply": "Automatically credited to farmer's account based on land records",
    "link": "https://apagrisnet.gov.in",
    "deadline": "Before each sowing season",
    "crops": ["All Crops"],
    "states": ["Andhra Pradesh", "Telangana"],
    "languages": {"te": "రైతు బంధు - ఎకరాకు ₹10,000 పెట్టుబడి సహాయం", "hi": "रायथू बंधु - एकड़ प्रति ₹10,000 निवेश सहायता"},
  },
  {
    "id": "soil-health-card",
    "name": "Soil Health Card",
    "full_name": "Soil Health Card Scheme",
    "category": "Soil Health",
    "icon": "🧪",
    "benefit": "Free soil testing + personalised fertiliser recommendations",
    "eligibility": "All farmers",
    "documents": ["Aadhaar Card", "Land Survey Number"],
    "how_to_apply": "Visit nearest Krishi Vigyan Kendra or soilhealth.dac.gov.in",
    "link": "https://soilhealth.dac.gov.in",
    "deadline": "Ongoing",
    "crops": ["All Crops"],
    "states": ["All States"],
    "languages": {"te": "నేల పరీక్ష మరియు ఎరువుల సలహా ఉచితంగా", "hi": "मिट्टी परीक्षण और उर्वरक सलाह मुफ्त"},
  },
]

CONTACTS = [
  {"id":"kisan-helpline",   "name":"Kisan Call Centre",            "type":"Helpline",         "phone":"1800-180-1551", "email":"kcc@nic.in",         "hours":"6AM–10PM daily", "icon":"📞", "states":["All States"]},
  {"id":"pm-kisan-help",    "name":"PM-KISAN Helpline",            "type":"Helpline",         "phone":"155261",        "email":"pmkisan-ict@gov.in",  "hours":"9AM–6PM",        "icon":"📞", "states":["All States"]},
  {"id":"fasal-bima-help",  "name":"PMFBY Helpline",               "type":"Insurance",        "phone":"1800-200-7710", "email":"help.agri@gov.in",    "hours":"9AM–5PM",        "icon":"🛡️", "states":["All States"]},
  {"id":"ap-agri-dept",     "name":"AP Agriculture Dept",          "type":"State Office",     "phone":"0866-2410497",  "email":"agri@ap.gov.in",      "hours":"10AM–5PM",       "icon":"🏛️", "states":["Andhra Pradesh"]},
  {"id":"ts-agri-dept",     "name":"Telangana Agriculture Dept",   "type":"State Office",     "phone":"040-23454848",  "email":"doa@telangana.gov.in","hours":"10AM–5PM",       "icon":"🏛️", "states":["Telangana"]},
  {"id":"nabard-help",      "name":"NABARD Farmer Helpline",       "type":"Credit",           "phone":"1800-022-0088", "email":"info@nabard.org",     "hours":"9AM–5PM",        "icon":"🏦", "states":["All States"]},
  {"id":"soil-health-help", "name":"Soil Health Card Helpline",    "type":"Testing",          "phone":"1800-180-1551", "email":"soil@nic.in",         "hours":"9AM–6PM",        "icon":"🧪", "states":["All States"]},
]

def get_schemes(crop_filter=None, state_filter=None, category_filter=None, lang="en"):
    results = []
    for s in SCHEMES:
        if crop_filter and crop_filter not in s["crops"] and "All Crops" not in s["crops"]:
            continue
        if state_filter and state_filter not in s["states"] and "All States" not in s["states"]:
            continue
        if category_filter and s["category"] != category_filter:
            continue
        # Strip internal 'languages' dict — frontend only needs 'local_description'
        scheme = {k: v for k, v in s.items() if k != "languages"}
        if lang != "en" and lang in s.get("languages", {}):
            scheme["local_description"] = s["languages"][lang]
        results.append(scheme)
    return results

def get_contacts(state_filter=None):
    if not state_filter:
        return CONTACTS
    return [c for c in CONTACTS
            if "All States" in c["states"] or state_filter in c["states"]]

def get_categories():
    return sorted(set(s["category"] for s in SCHEMES))

def get_states():
    states = set()
    for s in SCHEMES:
        for st in s["states"]:
            if st != "All States":
                states.add(st)
    return sorted(states)

# ── Additional national schemes ───────────────────────────────────────────────
SCHEMES.extend([
  {
    "id": "pmksn",
    "name": "PMKSY",
    "full_name": "Pradhan Mantri Krishi Sinchayee Yojana",
    "category": "Infrastructure",
    "icon": "💧",
    "benefit": "Irrigation infrastructure funding — 'Har Khet Ko Pani, More Crop Per Drop'",
    "eligibility": "All farmers needing irrigation infrastructure support",
    "documents": ["Aadhaar", "Land Records", "Bank Account"],
    "how_to_apply": "Apply through state agriculture department or pmksy.gov.in",
    "link": "https://pmksy.gov.in",
    "deadline": "Ongoing",
    "crops": ["All Crops"],
    "states": ["All States"],
    "languages": {"te": "నీటిపారుదల మౌలికసదుపాయాలు — హర్ ఖేత్ కో పాని", "hi": "सिंचाई अवसंरचना — हर खेत को पानी"},
  },
  {
    "id": "paramparagat",
    "name": "PKVY",
    "full_name": "Paramparagat Krishi Vikas Yojana",
    "category": "Organic Farming",
    "icon": "🌿",
    "benefit": "₹50,000/hectare over 3 years for organic farming cluster development",
    "eligibility": "Farmer groups (≥50 farmers) forming clusters of 50 acres",
    "documents": ["Aadhaar", "Land Records", "Group Registration Certificate"],
    "how_to_apply": "Form a cluster, register with district agriculture office",
    "link": "https://pgsindia-ncof.gov.in",
    "deadline": "Ongoing",
    "crops": ["All Crops"],
    "states": ["All States"],
    "languages": {"te": "సేంద్రీయ వ్యవసాయ క్లస్టర్ — ₹50,000/హెక్టారు", "hi": "जैविक खेती क्लस्टर — ₹50,000/हेक्टेयर"},
  },
  {
    "id": "rkvy",
    "name": "RKVY",
    "full_name": "Rashtriya Krishi Vikas Yojana",
    "category": "Infrastructure",
    "icon": "🏗️",
    "benefit": "Flexible funding for agriculture infrastructure, storage, processing",
    "eligibility": "State governments and farmer groups for capital investments",
    "documents": ["Project Proposal", "Land Records", "Bank Details"],
    "how_to_apply": "Apply through state agriculture department with project proposal",
    "link": "https://rkvy.nic.in",
    "deadline": "Ongoing",
    "crops": ["All Crops"],
    "states": ["All States"],
    "languages": {"te": "వ్యవసాయ మౌలిక సదుపాయాల అభివృద్ధి నిధి", "hi": "कृषि अवसंरचना विकास निधि"},
  },
  {
    "id": "nmoop",
    "name": "NMOOP",
    "full_name": "National Mission on Oilseeds and Oil Palm",
    "category": "Equipment Subsidy",
    "icon": "🌻",
    "benefit": "Subsidised seeds, IPM kits, sprinklers for oilseed/oil palm farmers",
    "eligibility": "Farmers growing groundnut, soybean, sunflower, mustard, oil palm",
    "documents": ["Aadhaar", "Land Records", "Bank Passbook"],
    "how_to_apply": "Contact district agriculture office or visit agri department website",
    "link": "https://nmoop.gov.in",
    "deadline": "Seasonal",
    "crops": ["Groundnut", "Soybean"],
    "states": ["All States"],
    "languages": {"te": "నూనె పంటలకు సబ్సిడీ విత్తనాలు మరియు పరికరాలు", "hi": "तिलहन फसलों के लिए सब्सिडी बीज और उपकरण"},
  },
  {
    "id": "sub-horticulture",
    "name": "MIDH",
    "full_name": "Mission for Integrated Development of Horticulture",
    "category": "Equipment Subsidy",
    "icon": "🍅",
    "benefit": "Up to 50% subsidy on planting material, drip irrigation, cold storage for horticulture",
    "eligibility": "Farmers growing fruits, vegetables, spices, flowers",
    "documents": ["Aadhaar", "Land Records", "Bank Account"],
    "how_to_apply": "Apply at district horticulture office or NHB/NHM portal",
    "link": "https://nhb.gov.in",
    "deadline": "Ongoing",
    "crops": ["Tomato", "Potato", "Chilli", "Onion", "Brinjal", "Banana"],
    "states": ["All States"],
    "languages": {"te": "ఉద్యానవన పంటలకు 50% సబ్సిడీ", "hi": "बागवानी फसलों पर 50% सब्सिडी"},
  },
])


def get_crop_matched_schemes(crop_name: str, state: str = None):
    """
    Returns schemes most relevant to a specific detected crop.
    Used by the analysis page to auto-show applicable schemes.
    """
    if not crop_name:
        return get_schemes()
    exact    = get_schemes(crop_filter=crop_name, state_filter=state)
    exact_ids = {s["id"] for s in exact}
    all_crop = [s for s in get_schemes(state_filter=state)
                if "All Crops" in s.get("crops", []) and s["id"] not in exact_ids]
    return exact + all_crop[:4]
