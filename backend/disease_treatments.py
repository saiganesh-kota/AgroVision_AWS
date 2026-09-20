"""
disease_treatments.py — AgroVision AI Disease Treatment Knowledge Base
═══════════════════════════════════════════════════════════════════════
Covers all 77 classes from class_names.json.

Each disease entry includes:
  • Multiple chemical treatment options (protective + systemic/curative)
  • Organic / bio-agent alternatives
  • Traditional / indigenous Indian farming remedies
  • Application timing, method, resistance management
  • Cultural practices (4-6 actionable items)
  • Safety precautions + expected recovery timeline

The ML+RL engine still decides the final action — this file only
provides the domain knowledge (what to do once the action is chosen).
"""

import json
import os

# ── Action definitions ────────────────────────────────────────────────────
ALL_ACTIONS = ["fungicide", "bactericide", "soil_fix", "ph_correction", "irrigation", "monitor"]

PATHOGEN_ENC = {
    "none": 0, "fungal": 1, "oomycete (fungal-like)": 1,
    "fungal (trunk disease complex)": 1, "fungal (trunk disease)": 1,
    "bacterial": 2, "viral": 3, "pest": 4, "algal": 1, "unknown": 1,
}

ACTION_TYPE = {
    "fungicide": "Chemical", "bactericide": "Chemical",
    "soil_fix": "Organic", "ph_correction": "Organic",
    "irrigation": "Organic", "monitor": "None",
}

ACTION_COST_INR = {
    "fungicide": 240, "bactericide": 280, "soil_fix": 180,
    "ph_correction": 150, "irrigation": 120, "monitor": 60,
}

TREATMENT_DISPLAY_NAME = {
    "fungicide": "Fungicide Spray", "bactericide": "Bactericide Spray",
    "soil_fix": "Soil Improvement", "ph_correction": "pH Adjustment",
    "irrigation": "Water Management", "monitor": "Monitoring",
}

_ALL_CROP_NAMES = sorted([
    "apple", "banana", "blueberry", "brinjal", "cherry", "chilli",
    "citrus", "coffee", "corn", "cotton", "grape", "groundnut",
    "maize", "mango", "onion", "orange", "peach", "pepper",
    "potato", "raspberry", "rice", "soybean", "squash",
    "strawberry", "sugarcane", "tea", "tomato", "wheat",
])
CROP_ENC = {c: i for i, c in enumerate(_ALL_CROP_NAMES)}

CROP_NAME_ALIASES = {
    "corn": "maize", "corn (maize)": "maize", "paddy": "rice",
    "eggplant": "brinjal", "capsicum": "chilli", "pepper": "chilli",
    "bell pepper": "pepper", "bell_pepper": "pepper",
    "peanut": "groundnut", "groundnuts": "groundnut", "cane": "sugarcane",
    "sour cherry": "cherry", "citrus greening": "citrus", "oranges": "orange",
}


def ensure_configs_exist(base_dir: str):
    """Create shared config files if they are missing.

    This keeps older imports working even if a clean checkout is missing the
    generated JSON files expected by the pipeline and RL layers.
    """
    actions_path = os.path.join(base_dir, "actions_config.json")
    if not os.path.exists(actions_path):
        payload = {
            "actions": ALL_ACTIONS,
            "rl_hyperparams": {"epsilon": 0.2, "alpha": 0.12, "gamma": 0.85},
            "meta": {
                action: {
                    "name": TREATMENT_DISPLAY_NAME[action],
                    "type": ACTION_TYPE[action],
                    "cost_inr": ACTION_COST_INR[action],
                }
                for action in ALL_ACTIONS
            },
        }
        with open(actions_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

# ══════════════════════════════════════════════════════════════════════════════
# DISEASE_DB  —  77 classes matched to class_names.json indices 0-76
# ══════════════════════════════════════════════════════════════════════════════
DISEASE_DB = {

    # ════════════ APPLE ══════════════════════════════════════════════════════

    "Apple___Apple_scab": {
        "pathogen_type": "fungal", "pathogen": "Venturia inaequalis",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Mancozeb 75WP or Captan 50WP",
            "dosage": "2-2.5g per litre of water",
            "frequency": "Every 7-10 days from bud break to petal fall",
            "organic_alt": "Bordeaux mixture 1% or wettable sulfur 3g/L",
            "chemical_options": [
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 7-10 days", "type": "Protective contact", "notes": "Start at green-tip stage"},
                {"name": "Captan 50WP", "dosage": "2.5g/L", "frequency": "Every 7-10 days", "type": "Protective contact"},
                {"name": "Myclobutanil 10WP", "dosage": "1g/L", "frequency": "Every 14 days", "type": "Systemic curative — FRAC 3"},
                {"name": "Kresoxim-methyl 44.3SC", "dosage": "1ml/L", "frequency": "Every 14-21 days", "type": "Systemic preventive — FRAC 11, max 2/season"},
            ],
            "organic_options": [
                {"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 10-14 days"},
                {"name": "Wettable sulfur 80WP", "dosage": "3g/L", "frequency": "Every 7-10 days — not above 35°C"},
            ],
            "traditional_remedies": [
                {"name": "Wood ash spray", "method": "Dissolve 250g ash in 10L water, strain, spray", "notes": "Raises surface pH — inhibits germination"},
            ],
            "when_to_apply": "Start at green-tip. Most critical: pink-bud to petal fall.",
            "resistance_management": "Rotate M3 → FRAC 3 → FRAC 11 → M3.",
            "safety": "PHI 7 days for both Mancozeb and Captan.",
            "expected_recovery": "New leaves clean after 2-3 sprays.",
        }},
        "cultural_practices": [
            "Rake and destroy fallen leaves in autumn — reduces inoculum 70%",
            "Prune for open canopy — 30% light penetration target",
            "Plant scab-resistant varieties: Freedom, Liberty, Enterprise",
            "Avoid overhead irrigation",
            "Remove mummified fruit",
        ],
    },

    "Apple___Black_rot": {
        "pathogen_type": "fungal", "pathogen": "Botryosphaeria obtusa",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Captan 50WP or Thiophanate-methyl 70WP",
            "dosage": "2-2.5g/L", "frequency": "Every 10-14 days from petal fall",
            "organic_alt": "Bordeaux mixture 1% or copper hydroxide 3g/L",
            "chemical_options": [
                {"name": "Captan 50WP", "dosage": "2.5g/L", "frequency": "Every 10-14 days"},
                {"name": "Thiophanate-methyl 70WP", "dosage": "1g/L", "frequency": "Every 14 days (max 2)"},
                {"name": "Ziram 76WG", "dosage": "2.5g/L", "frequency": "Every 10-14 days"},
            ],
            "organic_options": [{"name": "Copper hydroxide 50WP", "dosage": "3g/L", "frequency": "Every 14 days"}],
            "traditional_remedies": [{"name": "Turmeric + lime paste on wounds", "notes": "Traditional antifungal wound sealant"}],
            "when_to_apply": "Begin immediately after petal fall.",
            "resistance_management": "Alternate Captan with copper.",
            "safety": "PHI 7 days.",
            "expected_recovery": "Active infections cannot be reversed; sprays prevent new ones.",
        }},
        "cultural_practices": [
            "Prune and burn cankered branches — 15cm below margin",
            "Remove mummified fruit",
            "Sanitise pruning tools between trees",
            "Seal wounds with Bordeaux paste",
        ],
    },

    "Apple___Cedar_apple_rust": {
        "pathogen_type": "fungal", "pathogen": "Gymnosporangium juniperi-virginianae",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "rust",
        "treatments": {"fungicide": {
            "product": "Myclobutanil 10WP or Propiconazole 25EC",
            "dosage": "Myclobutanil: 1g/L | Propiconazole: 1ml/L",
            "frequency": "Every 10-14 days from pink bud through 3-4 weeks post petal fall",
            "organic_alt": "Wettable sulfur 3g/L",
            "chemical_options": [
                {"name": "Myclobutanil 10WP", "dosage": "1g/L", "frequency": "Every 10-14 days"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days"},
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "Every 14 days (max 2)"},
            ],
            "organic_options": [{"name": "Wettable sulfur 80WP", "dosage": "3g/L", "frequency": "Every 7-10 days"}],
            "traditional_remedies": [{"name": "Remove nearby juniper/cedar trees", "notes": "Breaks the disease's dual-host life cycle permanently"}],
            "when_to_apply": "Critical: when orange gel masses appear on juniper in spring.",
            "resistance_management": "Rotate FRAC 3 with FRAC 11.",
            "safety": "PHI 7-14 days.",
            "expected_recovery": "Existing lesions persist; new growth protected.",
        }},
        "cultural_practices": [
            "Plant rust-resistant varieties: William's Pride, Redfree",
            "Remove junipers within 300m where feasible",
            "Scout junipers in early spring",
        ],
    },

    "Apple___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment needed", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Preventive copper monthly"}},
        "cultural_practices": ["Balanced NPK", "Open canopy pruning", "Monitor weekly for scab, rust, fire blight"],
    },

    # ════════════ BANANA ══════════════════════════════════════════════════════

    "Banana___cordana": {
        "pathogen_type": "fungal", "pathogen": "Cordana musae",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Mancozeb 75WP or Propiconazole 25EC",
            "dosage": "Mancozeb: 2g/L | Propiconazole: 1ml/L",
            "frequency": "Every 14 days during humid/rainy season",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 14 days"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14-21 days"},
                {"name": "Hexaconazole 5SC", "dosage": "2ml/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14 days"}],
            "traditional_remedies": [{"name": "Cow urine spray 1:10", "notes": "Traditional antifungal practice in Tamil Nadu organic banana"}],
            "when_to_apply": "Early morning, before temperatures rise.",
            "resistance_management": "Alternate Mancozeb with Propiconazole.",
            "safety": "PHI 28 days.",
            "expected_recovery": "New leaves clean after 2-3 sprays.",
        }},
        "cultural_practices": [
            "Remove infected leaves at base — do not tear",
            "Avoid overhead irrigation",
            "Maintain 2.5m × 2.5m spacing",
        ],
    },

    "Banana___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment needed", "dosage": "N/A", "frequency": "Fortnightly", "organic_alt": "Monthly preventive spray"}},
        "cultural_practices": ["Balanced fertilisation — high potassium", "Remove dead leaves", "Monitor for Black Sigatoka"],
    },

    "Banana___pestalotiopsis": {
        "pathogen_type": "fungal", "pathogen": "Pestalotiopsis spp.",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Copper Oxychloride 50WP or Mancozeb 75WP",
            "dosage": "3g/L | 2g/L", "frequency": "Every 10-14 days especially after rain",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 10-14 days"},
                {"name": "Carbendazim 50WP", "dosage": "1g/L", "frequency": "Every 14 days (max 2)"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14-21 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14 days"}],
            "traditional_remedies": [{"name": "Garlic extract spray", "notes": "Allicin antifungal — used in Kerala organic farming"}],
            "when_to_apply": "Spray after pruning or storm damage — fungus enters through wounds.",
            "resistance_management": "Avoid repeated Carbendazim.",
            "safety": "PHI 14 days.",
            "expected_recovery": "New growth clean within 3-4 weeks.",
        }},
        "cultural_practices": ["Remove infected leaves promptly by cutting not tearing", "Seal cut surfaces with Bordeaux paste", "Avoid mechanical injury"],
    },

    "Banana___sigatoka": {
        "pathogen_type": "fungal", "pathogen": "Mycosphaerella fijiensis (Black Sigatoka)",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Propiconazole 25EC + Mancozeb tank mix",
            "dosage": "Propiconazole: 1ml/L + Mancozeb: 1g/L",
            "frequency": "Every 21 days — strictly rotate fungicide groups",
            "organic_alt": "Mineral oil sprays 15-20ml/L",
            "chemical_options": [
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 21 days", "type": "Curative up to 5 days post-infection"},
                {"name": "Trifloxystrobin + Propiconazole", "dosage": "0.5g/L", "frequency": "Every 21-28 days", "type": "Premium dual-mode"},
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 14 days"},
                {"name": "Chlorothalonil 75WP", "dosage": "2g/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [{"name": "Mineral oil 15-20ml/L + surfactant", "frequency": "Every 14 days", "notes": "Disrupts spore germination mechanically"}],
            "traditional_remedies": [{"name": "Pseudomonas fluorescens spray", "notes": "Bio-control used in TN IDM programs"}],
            "when_to_apply": "Spray when 5th leaf from heart shows first water-soaked symptoms.",
            "resistance_management": "MAJOR resistance risk. Rotate FRAC 3 → M3 → FRAC 11 → back. Never use FRAC 11 more than 2x consecutively.",
            "safety": "PHI 28 days. Respiratory protection essential.",
            "expected_recovery": "Cannot be eliminated — ongoing management; can cut yield 50% if unmanaged.",
        }},
        "cultural_practices": [
            "Remove diseased leaves weekly — desuckering",
            "Use FHIA hybrid varieties for better tolerance",
            "Drip irrigation — overhead spreads spores",
            "Adequate potassium — deficient plants show 2-3x severity",
        ],
    },

    # ════════════ BLUEBERRY ═══════════════════════════════════════════════════

    "Blueberry___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment needed", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Preventive sulfur at bud swell"}},
        "cultural_practices": ["Maintain soil pH 4.5-5.5", "Monitor for Mummy Berry and Botrytis at bloom", "Annual pruning"],
    },

    # ════════════ CHERRY ══════════════════════════════════════════════════════

    "Cherry_(including_sour)___Powdery_mildew": {
        "pathogen_type": "fungal", "pathogen": "Podosphaera clandestina",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Myclobutanil 10WP or Wettable Sulfur 80WP",
            "dosage": "Myclobutanil: 1g/L | Sulfur: 3g/L",
            "frequency": "Every 7-14 days from bud break through harvest",
            "organic_alt": "Wettable sulfur 3g/L",
            "chemical_options": [
                {"name": "Myclobutanil 10WP", "dosage": "1g/L", "frequency": "Every 14 days"},
                {"name": "Tebuconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days"},
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "Every 14 days (max 2)"},
            ],
            "organic_options": [
                {"name": "Wettable sulfur 80WP", "dosage": "3g/L", "frequency": "Every 7-10 days"},
                {"name": "Potassium bicarbonate", "dosage": "5g/L", "frequency": "Every 7-10 days"},
            ],
            "traditional_remedies": [{"name": "Milk spray (skim milk)", "method": "400ml skim milk + 600ml water weekly", "notes": "30-40% efficacy in university studies"}],
            "when_to_apply": "Begin at bud break.",
            "resistance_management": "Rotate DMI and QoI; include one sulfur spray per cycle.",
            "safety": "PHI 7 days. Sulfur: avoid within 14 days of oil sprays.",
            "expected_recovery": "New growth clean within 2-3 weeks.",
        }},
        "cultural_practices": ["Open canopy pruning", "Avoid overhead irrigation", "Remove infected shoot tips", "Avoid excess nitrogen"],
    },

    "Cherry_(including_sour)___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment needed", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Preventive sulfur at bud break"}},
        "cultural_practices": ["Monitor weekly for powdery mildew", "Annual pruning in late winter", "Avoid drought stress"],
    },

    # ════════════ CITRUS ══════════════════════════════════════════════════════

    "Citrus___black-spot": {
        "pathogen_type": "fungal", "pathogen": "Phyllosticta citricarpa",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Copper Oxychloride 50WP or Mancozeb 75WP",
            "dosage": "3g/L | 2g/L", "frequency": "At petal fall + 6 and 10 weeks after",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "3 sprays: petal fall, 6wk, 10wk"},
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Same timing"},
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "Every 3-4 weeks (max 3)"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 3-4 weeks"}],
            "traditional_remedies": [{"name": "Garlic-chilli spray", "notes": "Used in Vidarbha organic citrus"}],
            "when_to_apply": "Begin at petal fall.",
            "resistance_management": "Alternate copper with strobilurin.",
            "safety": "PHI 14 days.",
            "expected_recovery": "Existing fruit will not recover; spray prevents new infection.",
        }},
        "cultural_practices": ["Remove fallen infected fruit promptly", "Prune for airflow", "Spray before rain events"],
    },

    "Citrus___citrus-canker": {
        "pathogen_type": "bacterial", "pathogen": "Xanthomonas axonopodis pv. citri",
        "valid_actions": ["bactericide", "monitor"], "weather_class": "bacterial_spot",
        "treatments": {"bactericide": {
            "product": "Copper Hydroxide 77WP or Copper Oxychloride 50WP",
            "dosage": "3g/L", "frequency": "Every 21 days during rainy season + after pruning",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Copper Hydroxide 77WP", "dosage": "3g/L", "frequency": "Every 21 days"},
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 21 days"},
                {"name": "Streptomycin sulfate 17WP", "dosage": "200ppm", "frequency": "Every 14 days — check local regulation"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 21 days"}],
            "traditional_remedies": [{"name": "Neem oil + copper spray", "notes": "Used in IPM programs in Maharashtra citrus"}],
            "when_to_apply": "At every new flush. Always spray after pruning.",
            "resistance_management": "Copper resistance reported — switch to streptomycin if failing.",
            "safety": "QUARANTINE disease — report to district agriculture office.",
            "expected_recovery": "NO CURE for infected tissue.",
            "notes": "Spreads by wind, rain, insects, tools, human movement.",
        }},
        "cultural_practices": ["Remove and burn cankered twigs", "Disinfect tools between cuts", "Windbreaks reduce spread", "Avoid wounding in rainy season"],
    },

    # ════════════ COFFEE ══════════════════════════════════════════════════════

    "Coffee___masks": {
        "pathogen_type": "fungal", "pathogen": "Coffee Leaf Rust (Hemileia vastatrix)",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "rust",
        "treatments": {"fungicide": {
            "product": "Copper Oxychloride 50WP or Propiconazole 25EC",
            "dosage": "Copper: 3g/L | Propiconazole: 1ml/L",
            "frequency": "Preventive at start of rainy season — every 3-4 weeks",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 3-4 weeks"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 3-4 weeks — CCRI recommended"},
                {"name": "Hexaconazole 5SC", "dosage": "2ml/L", "frequency": "Every 3-4 weeks"},
                {"name": "Triadimefon 25WP", "dosage": "1g/L", "frequency": "Every 3-4 weeks"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 3-4 weeks"}],
            "traditional_remedies": [{"name": "Panchagavya spray", "notes": "Used in Coorg and Chikmagalur organic coffee"}],
            "when_to_apply": "Begin 2-3 weeks BEFORE expected monsoon onset.",
            "resistance_management": "Rotate copper with triazole.",
            "safety": "PHI 14 days. Max 4 copper sprays/year.",
            "expected_recovery": "New growth clean after 2-3 sprays.",
        }},
        "cultural_practices": ["Remove severely infected leaves", "Maintain proper shade balance", "Adequate K reduces severity", "Plant rust-resistant varieties: Catimor, Colombia"],
    },

    # ════════════ CORN / MAIZE ════════════════════════════════════════════════

    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
        "pathogen_type": "fungal", "pathogen": "Cercospora zeae-maydis",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Azoxystrobin 23SC or Propiconazole 25EC",
            "dosage": "1ml/L", "frequency": "At first symptom — repeat after 14 days",
            "organic_alt": "Crop rotation with non-host",
            "chemical_options": [
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "At V6-V8; repeat at tasseling"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days (max 2)"},
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 10-14 days"},
                {"name": "Pyraclostrobin", "dosage": "1ml/L", "frequency": "Every 14-21 days"},
            ],
            "organic_options": [{"name": "Pseudomonas fluorescens spray", "dosage": "10g/L", "frequency": "2 sprays"}],
            "traditional_remedies": [{"name": "Cattle urine spray 1:10", "notes": "Traditional Karnataka practice"}],
            "when_to_apply": "Scout at V6. Threshold: lesions on 3+ leaves below ear at tasseling.",
            "resistance_management": "Documented strobilurin resistance — alternate FRAC 11 with FRAC 3.",
            "safety": "PHI 7-14 days.",
            "expected_recovery": "Protect upper canopy through timely spray.",
        }},
        "cultural_practices": ["Crop rotation — most effective single tool", "Tillage buries residue", "Resistant hybrids", "Adequate nitrogen"],
    },

    "Corn_(maize)___Common_rust_": {
        "pathogen_type": "fungal", "pathogen": "Puccinia sorghi",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "rust",
        "treatments": {"fungicide": {
            "product": "Propiconazole 25EC or Tebuconazole 25EC",
            "dosage": "1ml/L", "frequency": "1-2 sprays from first pustule",
            "organic_alt": "Resistant hybrid variety",
            "chemical_options": [
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "At first pustule"},
                {"name": "Tebuconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days (max 2)"},
                {"name": "Azoxystrobin + Propiconazole", "dosage": "1ml/L", "frequency": "Single spray"},
            ],
            "organic_options": [{"name": "Wettable sulfur 80WP", "dosage": "3g/L", "frequency": "Every 10 days"}],
            "traditional_remedies": [{"name": "Wood ash dusting", "notes": "Low-cost option for subsistence farmers"}],
            "when_to_apply": "Scout from knee-high. Spray if >1% leaf area showing pustules.",
            "resistance_management": "Resistant hybrids primary strategy.",
            "safety": "PHI 14 days.",
            "expected_recovery": "Sporulation stops 48-72 hours after spray.",
        }},
        "cultural_practices": ["Plant early to avoid peak rust", "Use rust-resistant hybrids — most economical strategy", "Adequate nutrition"],
    },

    "Corn_(maize)___Northern_Leaf_Blight": {
        "pathogen_type": "fungal", "pathogen": "Exserohilum turcicum",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Azoxystrobin 23SC or Propiconazole 25EC",
            "dosage": "1ml/L", "frequency": "At first lesion — repeat after 14 days",
            "organic_alt": "Resistant hybrid + bio-control spray",
            "chemical_options": [
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "At VT if severity >5%"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days (max 2)"},
                {"name": "Picoxystrobin + Cyproconazole", "dosage": "0.5ml/L", "frequency": "Once at tasseling"},
            ],
            "organic_options": [{"name": "Pseudomonas fluorescens 10g/L", "frequency": "2 sprays"}],
            "traditional_remedies": [{"name": "Cow dung + water foliar spray", "notes": "Traditional organic farming practice"}],
            "when_to_apply": "Threshold: 3 leaves below ear at VT.",
            "resistance_management": "QoI resistance reported — rotate with FRAC 3.",
            "safety": "PHI 7-14 days.",
            "expected_recovery": "Ear leaf protection at tasseling most critical.",
        }},
        "cultural_practices": ["Tillage buries residue 50-70% reduction", "Crop rotation eliminates most inoculum", "Resistant hybrids", "Recommended sowing date"],
    },

    "Corn_(maize)___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment needed", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Preventive bio-control spray at V6"}},
        "cultural_practices": ["Scout weekly for rust and blight", "Balanced NPK especially nitrogen", "Monitor for fall army worm"],
    },

    # ════════════ GRAPE ═══════════════════════════════════════════════════════

    "Grape___Black_rot": {
        "pathogen_type": "fungal", "pathogen": "Guignardia bidwellii",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Mancozeb 75WP + Myclobutanil 10WP tank mix",
            "dosage": "Mancozeb: 2g/L + Myclobutanil: 1g/L",
            "frequency": "Every 10-14 days from bud break to veraison",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 10-14 days"},
                {"name": "Myclobutanil 10WP", "dosage": "1g/L", "frequency": "Every 14 days"},
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "Every 14-21 days (max 4)"},
                {"name": "Tebuconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [
                {"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 10-14 days"},
                {"name": "Copper hydroxide 50WP", "dosage": "3g/L", "frequency": "Every 10-14 days"},
                {"name": "Wettable sulfur 80WP", "dosage": "3g/L", "frequency": "Every 7-10 days below 32°C"},
            ],
            "traditional_remedies": [
                {"name": "Panchagavya 3% spray", "notes": "Used on organic table grape farms in Nashik"},
                {"name": "Neem oil 0.5%", "notes": "Preventive — best in IPM approach"},
            ],
            "when_to_apply": "Most critical: 2 weeks before to 3 weeks after bloom.",
            "resistance_management": "Rotate M3 → FRAC 3 → FRAC 11 → M3.",
            "safety": "Myclobutanil PHI 7 days. Mancozeb PHI 77 days for table grapes.",
            "expected_recovery": "Infected berries mummify — remove immediately.",
        }},
        "cultural_practices": [
            "Remove mummified berries before bud break",
            "Open canopy pruning — most important tool",
            "Leaf removal in fruit zone post-bloom",
            "Avoid late nitrogen",
        ],
    },

    "Grape___Esca_(Black_Measles)": {
        "pathogen_type": "fungal (trunk disease complex)", "pathogen": "Phaeomoniella chlamydospora / Phaeoacremonium spp.",
        "valid_actions": ["soil_fix", "monitor"], "weather_class": "trunk_disease",
        "treatments": {"soil_fix": {
            "product": "Fungicidal wound sealant — Thiophanate-methyl paste or Bordeaux paste",
            "dosage": "Apply undiluted within 10 minutes of cutting",
            "frequency": "Every pruning operation — no curative treatment exists",
            "organic_alt": "Bordeaux paste",
            "chemical_options": [
                {"name": "Thiophanate-methyl 70WP paste", "dosage": "Thick paste on cuts", "frequency": "Immediately"},
                {"name": "Trichoderma viride wound paste", "dosage": "Commercial paste on wounds", "frequency": "Immediately"},
            ],
            "organic_options": [{"name": "Bordeaux paste", "dosage": "Thick paste — within 10 min of cut", "frequency": "Every cut"}],
            "traditional_remedies": [
                {"name": "Garlic clove insertion", "notes": "Traditional European vineyard practice"},
                {"name": "Double-pruning technique", "notes": "Reduces Esca infections significantly"},
            ],
            "when_to_apply": "Prune ONLY in dry weather.",
            "resistance_management": "Not applicable — no curative treatment.",
            "safety": "Wear gloves with Thiophanate-methyl.",
            "expected_recovery": "NO CURE — trunk renewal only long-term option.",
            "notes": "Once internal wood infected, no treatment can reach it. ALL management PREVENTIVE.",
        }},
        "cultural_practices": [
            "Disinfect pruning tools between EVERY vine",
            "Prune ONLY in dry weather",
            "Wound sealant within 10 minutes of every cut",
            "Trunk renewal on affected vines",
        ],
    },

    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": {
        "pathogen_type": "fungal", "pathogen": "Pseudocercospora vitis",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Mancozeb 75WP or Copper Oxychloride 50WP",
            "dosage": "Mancozeb: 2g/L | Copper: 3g/L",
            "frequency": "Every 12-14 days during humid monsoon",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 12-14 days"},
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 14 days"},
                {"name": "Hexaconazole 5SC", "dosage": "2ml/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14 days"}],
            "traditional_remedies": [{"name": "Bordeaux paste trunk wash at dormancy", "notes": "Kills overwintering spores"}],
            "when_to_apply": "First angular spots — morning spray.",
            "resistance_management": "Rotate M3 → M1 → FRAC 3.",
            "safety": "Mancozeb PHI 77 days. Copper PHI 14 days.",
            "expected_recovery": "New growth clean within 2-3 sprays.",
        }},
        "cultural_practices": ["Canopy leaf removal in fruit zone", "Drip irrigation", "Preventive sprays before monsoon"],
    },

    "Grape___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment — preventive programme", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Preventive Bordeaux before monsoon"}},
        "cultural_practices": ["Preventive spray programme before monsoon", "Annual pruning for open canopy", "Monitor weekly for Black Rot, Downy Mildew, Powdery Mildew"],
    },

    # ════════════ GROUNDNUT ═══════════════════════════════════════════════════

    "Groundnut___early_leaf_spot": {
        "pathogen_type": "fungal", "pathogen": "Cercospora arachidicola",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Chlorothalonil 75WP or Mancozeb 75WP",
            "dosage": "2g/L", "frequency": "Every 10-14 days from 30-35 DAS",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Chlorothalonil 75WP", "dosage": "2g/L", "frequency": "Every 10-14 days from 30 DAS"},
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 10-14 days"},
                {"name": "Tebuconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days (max 2)"},
                {"name": "Carbendazim + Mancozeb tank mix", "dosage": "1g/L + 2g/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [
                {"name": "Pseudomonas fluorescens 10g/L", "frequency": "2-3 sprays from 30 DAS"},
                {"name": "Trichoderma viride seed treatment", "dosage": "4g/kg seed", "frequency": "Once"},
                {"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14 days from 30 DAS"},
            ],
            "traditional_remedies": [
                {"name": "NSKE 5%", "notes": "Government-approved bio-pesticide for groundnut IPM"},
                {"name": "Turmeric + chilli spray", "notes": "Traditional Rayalaseema practice"},
            ],
            "when_to_apply": "Begin at 30-35 DAS regardless of disease presence.",
            "resistance_management": "Alternate M3 with FRAC 3.",
            "safety": "Chlorothalonil PHI 7 days. Mancozeb PHI 7 days.",
            "expected_recovery": "New growth clean within 14-21 days.",
        }},
        "cultural_practices": [
            "Seed treatment: Thiram + Carbendazim before sowing",
            "Certified disease-free seeds",
            "No evening irrigation",
            "Crop rotation: groundnut → sorghum/maize",
        ],
    },

    "Groundnut___healthy_leaf": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment needed", "dosage": "N/A", "frequency": "Weekly from 30 DAS", "organic_alt": "Preventive NSKE 5% at 30 DAS"}},
        "cultural_practices": ["Begin preventive spray at 30 DAS", "Apply gypsum 500kg/ha at pegging", "Scout weekly for Tikka and rust"],
    },

    "Groundnut___late_leaf_spot": {
        "pathogen_type": "fungal", "pathogen": "Cercosporidium personatum",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Chlorothalonil 75WP or Propiconazole 25EC",
            "dosage": "Chlorothalonil: 2g/L | Propiconazole: 1ml/L",
            "frequency": "Every 10-14 days from 45 DAS",
            "organic_alt": "Copper oxychloride 3g/L",
            "chemical_options": [
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days from 45 DAS"},
                {"name": "Chlorothalonil 75WP", "dosage": "2g/L", "frequency": "Every 10-14 days"},
                {"name": "Hexaconazole 5SC", "dosage": "2ml/L", "frequency": "Every 14 days"},
                {"name": "Difenoconazole 25EC", "dosage": "0.5ml/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [{"name": "Pseudomonas fluorescens Pf1", "frequency": "Sprays at 30, 45, 60 DAS"}],
            "traditional_remedies": [{"name": "Cow urine + Asafoetida spray", "notes": "Traditional Rayalaseema practice"}],
            "when_to_apply": "Do NOT reduce spray frequency — LLS causes 50-70% yield loss.",
            "resistance_management": "Do NOT use benzimidazoles primary for LLS.",
            "safety": "Propiconazole PHI 14 days.",
            "expected_recovery": "Consistent schedule reduces Tikka severity 60-80%.",
        }},
        "cultural_practices": [
            "Do NOT stop spraying late season — most damaging from 60-90 DAS",
            "Gypsum 500kg/ha at pegging",
            "Soil drainage critical",
            "Harvest at 90% pod maturity",
        ],
    },

    "Groundnut___nutrition_deficiency": {
        "pathogen_type": "none", "pathogen": "Abiotic — not infectious",
        "valid_actions": ["soil_fix", "ph_correction", "irrigation", "monitor"], "weather_class": "abiotic",
        "treatments": {"soil_fix": {
            "product": "Targeted micronutrient based on soil test: Fe, Zn, B, Ca",
            "dosage": "FeSO4 0.5% | ZnSO4 0.5% | Borax 0.2% | Gypsum 500kg/ha",
            "frequency": "2-3 foliar sprays at 10-day intervals",
            "organic_alt": "Vermicompost + neem cake",
            "chemical_options": [
                {"name": "FeSO4 + citric acid foliar", "dosage": "5g/L + 2.5g citric acid/L", "type": "Iron deficiency"},
                {"name": "ZnSO4 21% foliar", "dosage": "5g/L", "type": "Zinc deficiency"},
                {"name": "Borax 20%", "dosage": "2g/L", "type": "Boron deficiency — pod fill"},
                {"name": "Gypsum (Calcium Sulfate)", "dosage": "500kg/ha at pegging", "type": "MOST IMPORTANT — prevents empty pods"},
            ],
            "organic_options": [
                {"name": "Neem cake 200kg/ha", "frequency": "Once before sowing"},
                {"name": "Vermicompost 2t/ha", "frequency": "Once at sowing"},
            ],
            "traditional_remedies": [
                {"name": "Bone meal 100-200kg/ha", "notes": "Traditional Ca + P source in AP"},
                {"name": "Wood ash 500kg/ha", "notes": "K, Ca, micronutrients"},
            ],
            "when_to_apply": "Gypsum SPECIFICALLY at pegging stage.",
            "resistance_management": "Not applicable.",
            "safety": "Do not mix ZnSO4 with phosphate products.",
            "expected_recovery": "Foliar results visible 5-7 days.",
        }},
        "cultural_practices": [
            "Soil test every season",
            "Lime if pH < 6.0",
            "Gypsum 500kg/ha at pegging EVERY season",
            "Avoid waterlogging",
        ],
    },

    "Groundnut___rust": {
        "pathogen_type": "fungal", "pathogen": "Puccinia arachidis",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "rust",
        "treatments": {"fungicide": {
            "product": "Mancozeb 75WP + Hexaconazole 5SC tank mix",
            "dosage": "Mancozeb: 2g/L + Hexaconazole: 2ml/L",
            "frequency": "Every 10-14 days — do not delay first spray",
            "organic_alt": "Wettable sulfur 3g/L + Copper oxychloride 3g/L",
            "chemical_options": [
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 10 days from first pustule"},
                {"name": "Hexaconazole 5SC", "dosage": "2ml/L", "frequency": "Every 14 days"},
                {"name": "Tebuconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [{"name": "Wettable sulfur 80WP", "dosage": "3g/L", "frequency": "Every 7-10 days"}],
            "traditional_remedies": [{"name": "Turmeric + slaked lime spray on leaf undersides", "notes": "Traditional AP practice"}],
            "when_to_apply": "Scout weekly from 45 DAS. First pustule = spray immediately.",
            "resistance_management": "Alternate M3 with FRAC 3.",
            "safety": "Hexaconazole PHI 14 days.",
            "expected_recovery": "Pustules dry out 5-7 days after DMI spray.",
        }},
        "cultural_practices": ["Scout undersides of leaves from 45 DAS weekly", "Sow on recommended date", "Adequate K fertilisation", "Eliminate volunteer groundnut"],
    },

    # ════════════ MANGO ═══════════════════════════════════════════════════════

    "Mango___Anthracnose": {
        "pathogen_type": "fungal", "pathogen": "Colletotrichum gloeosporioides",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Carbendazim 50WP or Copper Oxychloride 50WP",
            "dosage": "Carbendazim: 1g/L | Copper: 3g/L",
            "frequency": "3 sprays: panicle, fruit set, 3-4 weeks after fruit set",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Carbendazim 50WP", "dosage": "1g/L", "frequency": "3 critical sprays"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Same timing"},
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 15 days"},
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "Every 14-21 days (max 3)"},
            ],
            "organic_options": [
                {"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "3 sprays"},
                {"name": "Trichoderma viride spray", "dosage": "10g/L", "frequency": "3 sprays"},
            ],
            "traditional_remedies": [{"name": "Hot water post-harvest dip 52°C/5min", "notes": "Reduces storage loss 60-70%"}],
            "when_to_apply": "Spray 1 at panicle 5-10cm; spray 2 at pea-size fruit; spray 3 at 3-4 weeks.",
            "resistance_management": "Carbendazim resistance documented — rotate with Propiconazole.",
            "safety": "Carbendazim PHI 28 days.",
            "expected_recovery": "Preventive sprays protect crop; infected fruit does not recover.",
        }},
        "cultural_practices": ["Prune after harvest", "Remove mummified fruit", "Open canopy", "Hot water dip for export fruit"],
    },

    "Mango___Bacterial_Canker": {
        "pathogen_type": "bacterial", "pathogen": "Xanthomonas campestris pv. mangiferaeindicae",
        "valid_actions": ["bactericide", "monitor"], "weather_class": "bacterial_spot",
        "treatments": {"bactericide": {
            "product": "Copper Oxychloride 50WP or Copper Hydroxide 50WP",
            "dosage": "3g/L", "frequency": "Every 21 days during monsoon — 3-4 sprays/season",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 21 days"},
                {"name": "Copper Hydroxide 77WP", "dosage": "3g/L", "frequency": "Every 21 days"},
                {"name": "Streptomycin sulfate 17WP", "dosage": "0.5g/L", "frequency": "When copper fails (max 3)"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 21 days"}],
            "traditional_remedies": [{"name": "Turmeric + lime paste on canker lesions", "notes": "Traditional orchard practice"}],
            "when_to_apply": "Before monsoon onset. ALWAYS after pruning.",
            "resistance_management": "Switch to streptomycin if copper fails.",
            "safety": "Fungicide is INEFFECTIVE.",
            "expected_recovery": "No cure — prune cankered branches.",
            "notes": "BACTERIAL disease — fungicide has ZERO effect.",
        }},
        "cultural_practices": ["Prune cankered branches 15-20cm below symptoms", "Disinfect tools between cuts", "No operations during/after rain"],
    },

    "Mango___Cutting_Weevil": {
        "pathogen_type": "pest", "pathogen": "Deporaus marginatus",
        "valid_actions": ["monitor", "soil_fix"], "weather_class": "pest",
        "treatments": {"soil_fix": {
            "product": "Chlorpyrifos 20EC or Carbaryl 50WP",
            "dosage": "Chlorpyrifos: 2ml/L | Carbaryl: 2g/L",
            "frequency": "At new flush — 2 sprays 10-14 days apart",
            "organic_alt": "Neem oil 0.5% + NSKE 5%",
            "chemical_options": [
                {"name": "Chlorpyrifos 20EC", "dosage": "2ml/L", "frequency": "At flush; repeat 10-14 days"},
                {"name": "Carbaryl 50WP", "dosage": "2g/L", "frequency": "At flush; repeat 14 days"},
                {"name": "Imidacloprid 17.8SL", "dosage": "0.5ml/L", "frequency": "Once per flush — NOT within 3 months of harvest"},
            ],
            "organic_options": [{"name": "Neem oil 0.5%", "dosage": "5ml/L", "frequency": "Weekly during flush"}],
            "traditional_remedies": [{"name": "Daily collection of fallen rolled leaves", "notes": "Breaks population cycle"}],
            "when_to_apply": "Monitor during flush. >10% leaves damaged = spray immediately.",
            "resistance_management": "Rotate organophosphate and carbamate.",
            "safety": "Chlorpyrifos PHI 14 days.",
            "expected_recovery": "Adults killed 24-48 hours.",
        }},
        "cultural_practices": ["Daily collection of rolled leaf sections", "Deep cultivation around base", "White lime wash on trunk"],
    },

    "Mango___Die_Back": {
        "pathogen_type": "fungal (trunk disease)", "pathogen": "Lasiodiplodia theobromae",
        "valid_actions": ["soil_fix", "fungicide", "monitor"], "weather_class": "trunk_disease",
        "treatments": {"fungicide": {
            "product": "Carbendazim 50WP paste on wounds + Copper Oxychloride spray",
            "dosage": "Paste: thick paste; Spray: 3g/L",
            "frequency": "Paste immediately after every cut; Spray every 21 days",
            "organic_alt": "Bordeaux paste + Trichoderma spray",
            "chemical_options": [
                {"name": "Carbendazim 50WP paste", "dosage": "Thick paste within 10 min of cut", "frequency": "Every cut"},
                {"name": "Copper Oxychloride 50WP spray", "dosage": "3g/L", "frequency": "Every 21 days"},
                {"name": "Thiophanate-methyl 70WP paste", "dosage": "Thick paste", "frequency": "Each cut"},
            ],
            "organic_options": [{"name": "Bordeaux paste", "dosage": "Thick paste within 10 minutes", "frequency": "Every cut"}],
            "traditional_remedies": [{"name": "Turmeric + lime + mustard oil wound paste", "notes": "Traditional orchard practice"}],
            "when_to_apply": "Prune ONLY in dry weather. Seal within 10 minutes.",
            "resistance_management": "Rotate Carbendazim with Thiophanate-methyl.",
            "safety": "Carbendazim PHI 28 days.",
            "expected_recovery": "No cure for infected wood — prune 15cm below symptoms.",
        }},
        "cultural_practices": ["Prune ONLY in dry weather", "Wound paste WITHIN 10 MINUTES", "Burn pruned material", "Balanced tree nutrition"],
    },

    "Mango___Gall_Midge": {
        "pathogen_type": "pest", "pathogen": "Procontarinia matteiana",
        "valid_actions": ["monitor", "soil_fix"], "weather_class": "pest",
        "treatments": {"soil_fix": {
            "product": "Imidacloprid 17.8SL soil drench or Chlorpyrifos + Cypermethrin foliar",
            "dosage": "Imidacloprid: 1ml/L drench | Chlorpyrifos+Cypermethrin: 2ml/L",
            "frequency": "At flush emergence — 1-2 applications",
            "organic_alt": "Neem oil 0.5% + yellow sticky traps",
            "chemical_options": [
                {"name": "Imidacloprid 17.8SL soil drench", "dosage": "1ml/L", "frequency": "Once before flush"},
                {"name": "Chlorpyrifos + Cypermethrin", "dosage": "2ml/L", "frequency": "At flush; repeat 10-14 days"},
                {"name": "Dimethoate 30EC", "dosage": "2ml/L", "frequency": "Every 7-10 days"},
            ],
            "organic_options": [{"name": "Neem oil 0.5%", "dosage": "5ml/L", "frequency": "Weekly during flush"}],
            "traditional_remedies": [{"name": "Deep cultivation + lime dust", "notes": "Exposes pupae to sun and predators"}],
            "when_to_apply": "Monitor soil post-monsoon. Begin sprays when adults trapped.",
            "resistance_management": "Rotate neonicotinoid → organophosphate → pyrethroid.",
            "safety": "Imidacloprid PHI 60 days. DO NOT spray during flowering.",
            "expected_recovery": "New flush after spray remains undamaged.",
        }},
        "cultural_practices": ["Deep cultivation after harvest", "Collect infested leaves daily", "Yellow sticky traps before flush"],
    },

    "Mango___Healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment — preventive copper before monsoon", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Bordeaux spray before monsoon"}},
        "cultural_practices": ["Prune after harvest", "Copper spray before monsoon", "Monitor for Anthracnose and Bacterial Canker"],
    },

    "Mango___Powdery_Mildew": {
        "pathogen_type": "fungal", "pathogen": "Oidium mangiferae",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Wettable Sulfur 80WP or Hexaconazole 5SC",
            "dosage": "Sulfur: 3g/L | Hexaconazole: 2ml/L",
            "frequency": "3 sprays: panicle emergence, full bloom, pea-size fruit",
            "organic_alt": "Wettable sulfur 3g/L",
            "chemical_options": [
                {"name": "Wettable Sulfur 80WP", "dosage": "3g/L", "frequency": "3 sprays — DO NOT above 38°C"},
                {"name": "Hexaconazole 5SC", "dosage": "2ml/L", "frequency": "Same 3-spray timing"},
                {"name": "Dinocap 48EC", "dosage": "1ml/L", "frequency": "Every 14-21 days"},
                {"name": "Myclobutanil 10WP", "dosage": "1g/L", "frequency": "Every 14 days (max 3)"},
            ],
            "organic_options": [{"name": "Wettable sulfur 80WP", "dosage": "3g/L", "frequency": "Every 10-14 days during flowering"}],
            "traditional_remedies": [{"name": "Sulfur dust at panicle emergence", "notes": "Traditional low-cost alternative"}],
            "when_to_apply": "MOST CRITICAL: panicle emergence to petal fall.",
            "resistance_management": "Alternate FRAC 3 with FRAC M2 (Sulfur).",
            "safety": "DO NOT spray sulfur above 38°C.",
            "expected_recovery": "Existing colonies die 5-7 days. Unmanaged: 20-80% crop loss.",
        }},
        "cultural_practices": ["Monitor panicles from September/November", "Spray AT PANICLE EMERGENCE", "Prune October-November", "Avoid late nitrogen"],
    },

    "Mango___Sooty_Mould": {
        "pathogen_type": "fungal", "pathogen": "Capnodium mangiferae (secondary on honeydew)",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "CONTROL INSECTS FIRST — then starch 1% spray to dislodge mould",
            "dosage": "Insecticide varies; Starch: 10g/L",
            "frequency": "2 insecticide sprays 14 days apart",
            "organic_alt": "Neem oil 0.5% for insects + soap wash",
            "chemical_options": [
                {"name": "Imidacloprid 17.8SL", "dosage": "0.5ml/L", "frequency": "2 sprays 14 days apart"},
                {"name": "Dimethoate + Chlorpyrifos", "dosage": "1ml/L + 1ml/L", "frequency": "2 sprays"},
                {"name": "Starch spray 1%", "dosage": "10g/L", "frequency": "Once after insect control"},
            ],
            "organic_options": [{"name": "Neem oil 0.5%", "dosage": "5ml/L", "frequency": "Weekly"}],
            "traditional_remedies": [{"name": "Release Cryptolaemus montrouzieri beetles", "notes": "Most effective biological control"}],
            "when_to_apply": "Control insects FIRST — mould disappears naturally without honeydew.",
            "resistance_management": "Rotate neonicotinoid with organophosphate.",
            "safety": "Imidacloprid HIGH bee toxicity — DO NOT during flowering.",
            "expected_recovery": "Mould weathers off 2-4 weeks after insect control.",
            "notes": "Sooty mould does NOT infect plant tissue — grows only on insect honeydew.",
        }},
        "cultural_practices": ["Identify and control causative insect", "Release Cryptolaemus beetles", "Prune for airflow", "Remove ant colonies"],
    },

    "Orange___Haunglongbing_(Citrus_greening)": {
        "pathogen_type": "bacterial", "pathogen": "Candidatus Liberibacter asiaticus (psyllid vector)",
        "valid_actions": ["monitor"], "weather_class": "bacterial_spot",
        "treatments": {"monitor": {
            "product": "NO CURE — Prevention + vector control + remove infected trees",
            "dosage": "Imidacloprid 0.5ml/L for psyllid",
            "frequency": "Every 21-28 days during flush",
            "organic_alt": "Kaolin clay 5% + Tamarixia radiata release + remove infected trees",
            "chemical_options": [
                {"name": "Imidacloprid 17.8SL", "dosage": "0.5ml/L", "frequency": "Each flush"},
                {"name": "Thiamethoxam 25WG", "dosage": "0.25g/L", "frequency": "Every 21 days"},
                {"name": "Spirotetramat 15SC", "dosage": "0.75ml/L", "frequency": "When nymphs present"},
            ],
            "organic_options": [
                {"name": "Remove and destroy ALL infected trees immediately", "notes": "SINGLE MOST IMPORTANT action"},
                {"name": "Kaolin clay 5%", "dosage": "50g/L", "frequency": "Every 7 days"},
            ],
            "traditional_remedies": [{"name": "ZnSO4 + MnSO4 foliar monthly", "notes": "Manages deficiency symptoms; does not cure"}],
            "when_to_apply": "No treatment cures HLB.",
            "resistance_management": "Rotate Imidacloprid → Thiamethoxam → Spirotetramat.",
            "safety": "Tree removal may be MANDATORY under state programs.",
            "expected_recovery": "NONE. Infected trees decline and die within 5-10 years.",
            "notes": "World's most devastating citrus disease. No commercial cure exists.",
        }},
        "cultural_practices": ["Use ONLY certified HLB-free nursery plants", "Remove and destroy infected trees", "Systemic insecticide at every flush", "Report to district horticulture department"],
    },

    "Peach___Bacterial_spot": {
        "pathogen_type": "bacterial", "pathogen": "Xanthomonas arboricola pv. pruni",
        "valid_actions": ["bactericide", "monitor"], "weather_class": "bacterial_spot",
        "treatments": {"bactericide": {
            "product": "Copper Hydroxide 50WP or Oxytetracycline 17WP",
            "dosage": "Copper: 3g/L | Oxytetracycline: 200ppm",
            "frequency": "Pink bud, petal fall, +2wk, +4wk",
            "organic_alt": "Bordeaux mixture 1% + dormant lime sulfur",
            "chemical_options": [
                {"name": "Copper Hydroxide 50WP", "dosage": "3g/L", "frequency": "4 sprays"},
                {"name": "Oxytetracycline 17WP", "dosage": "200ppm", "frequency": "Every 10-14 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14-21 days"}],
            "traditional_remedies": [{"name": "Dormant lime sulfur spray", "notes": "Kills overwintering bacteria in bark"}],
            "when_to_apply": "Begin at pink bud.",
            "resistance_management": "Switch to oxytetracycline if copper fails.",
            "safety": "Fungicide is INEFFECTIVE.",
            "expected_recovery": "Existing spots do not heal.",
        }},
        "cultural_practices": ["Open-vase canopy pruning", "Remove infected twigs", "Resistant varieties: Redhaven, Contender", "Drip irrigation"],
    },

    "Peach___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "bacterial_spot",
        "treatments": {"monitor": {"product": "No treatment — preventive copper", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Dormant lime sulfur"}},
        "cultural_practices": ["Dormant lime sulfur spray", "Monitor weekly for bacterial spot", "Annual pruning"],
    },

    "Pepper,_bell___Bacterial_spot": {
        "pathogen_type": "bacterial", "pathogen": "Xanthomonas campestris pv. vesicatoria",
        "valid_actions": ["bactericide", "irrigation", "monitor"], "weather_class": "bacterial_spot",
        "treatments": {"bactericide": {
            "product": "Copper Hydroxide + Mancozeb tank mix",
            "dosage": "Copper: 3g/L + Mancozeb: 2g/L",
            "frequency": "Every 7-10 days warm/wet",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Copper Hydroxide + Mancozeb", "dosage": "3g/L + 2g/L", "frequency": "Every 7-10 days"},
                {"name": "Copper Oxychloride + Mancozeb", "dosage": "2g/L + 2g/L", "frequency": "Every 7-10 days"},
                {"name": "Kasugamycin + Copper", "dosage": "3g/L", "frequency": "Every 10-14 days (max 3)"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 10-14 days"}],
            "traditional_remedies": [{"name": "Cow urine + garlic spray", "notes": "Traditional Karnataka practice"}],
            "when_to_apply": "Before predicted rain. Never work in wet field.",
            "resistance_management": "Always tank mix copper with Mancozeb.",
            "safety": "CRITICAL: Fungicide is COMPLETELY INEFFECTIVE.",
            "expected_recovery": "Existing spots do not heal.",
            "notes": "Bacterial — FUNGICIDE HAS ZERO EFFECT.",
        }},
        "cultural_practices": ["Drip irrigation ONLY", "Disease-free transplants", "Never work in wet field", "Crop rotation 2 years"],
    },

    "Pepper,_bell___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "bacterial_spot",
        "treatments": {"monitor": {"product": "No treatment — preventive copper", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Preventive copper before rain"}},
        "cultural_practices": ["Drip irrigation", "Scout weekly", "Adequate Ca nutrition"],
    },

    "Potato___Early_blight": {
        "pathogen_type": "fungal", "pathogen": "Alternaria solani",
        "valid_actions": ["fungicide", "soil_fix", "irrigation", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Chlorothalonil 75WP or Mancozeb 75WP",
            "dosage": "2g/L", "frequency": "Every 7-10 days from first lesion",
            "organic_alt": "Copper oxychloride 3g/L",
            "chemical_options": [
                {"name": "Chlorothalonil 75WP", "dosage": "2g/L", "frequency": "Every 7-10 days"},
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 7-10 days"},
                {"name": "Azoxystrobin + Difenoconazole", "dosage": "0.75ml/L + 0.3ml/L", "frequency": "Every 14 days (max 3)"},
                {"name": "Iprodione 50WP", "dosage": "1.5g/L", "frequency": "Every 14 days (max 2)"},
            ],
            "organic_options": [{"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 10-14 days"}],
            "traditional_remedies": [{"name": "Garlic extract spray", "notes": "Traditional Himalayan potato practice"}],
            "when_to_apply": "Scout from 3 weeks after emergence. First lesion = spray.",
            "resistance_management": "Alternate M5 with M3.",
            "safety": "Chlorothalonil IARC Group 2B — full PPE.",
            "expected_recovery": "Remove lower infected leaves.",
        }},
        "cultural_practices": ["Crop rotation: potato → maize → wheat", "Certified seed tubers", "Hilling at 3-4 weeks", "Drip irrigation"],
    },

    "Potato___Late_blight": {
        "pathogen_type": "oomycete (fungal-like)", "pathogen": "Phytophthora infestans",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "late_blight_oomycete",
        "treatments": {"fungicide": {
            "product": "Metalaxyl-M 8% + Mancozeb 64% WP — GOLD STANDARD",
            "dosage": "2.5g/L", "frequency": "Every 5-7 days in cool humid — DO NOT DELAY",
            "organic_alt": "Copper Hydroxide + Mancozeb (limited efficacy)",
            "chemical_options": [
                {"name": "Metalaxyl-M + Mancozeb", "dosage": "2.5g/L", "frequency": "Every 7 days; 5 days severe"},
                {"name": "Cymoxanil + Mancozeb", "dosage": "2.5g/L", "frequency": "Every 7 days"},
                {"name": "Dimethomorph + Mancozeb", "dosage": "1g/L + 2g/L", "frequency": "Every 7 days"},
                {"name": "Propamocarb 72.2SL", "dosage": "1.5ml/L", "frequency": "Every 7-10 days"},
            ],
            "organic_options": [{"name": "Copper Hydroxide + Mancozeb tank mix", "dosage": "3g/L + 2g/L", "frequency": "Every 5-7 days"}],
            "traditional_remedies": [{"name": "IMMEDIATE plant removal", "notes": "MOST CRITICAL action — one plant infects 10 neighbours within 3-5 days"}],
            "when_to_apply": "EMERGENCY — apply within 24 hours of any lesion.",
            "resistance_management": "MAJOR metalaxyl resistance in India. NEVER use alone.",
            "safety": "Delay is not an option.",
            "expected_recovery": "Cannot recover. Haulm destruction at >75% infected.",
            "notes": "HIGHEST PRIORITY disease in potato.",
        }},
        "cultural_practices": ["Monitor daily weather", "Certified disease-free seed tubers", "REMOVE infected plants IMMEDIATELY", "Hilling minimum 15cm"],
    },

    "Potato___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "late_blight_oomycete",
        "treatments": {"monitor": {"product": "No treatment — begin preventive programme", "dosage": "N/A", "frequency": "DAILY in cool/wet weather", "organic_alt": "Preventive Bordeaux at first cold snap"}},
        "cultural_practices": ["Monitor daily weather forecasts", "Begin preventive sprays BEFORE disease appears", "Certified disease-free seed"],
    },

    "Raspberry___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment needed", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Preventive copper at bud swell"}},
        "cultural_practices": ["Remove old canes after fruiting", "Open canopy for airflow", "Monitor for Botrytis, Cane Blight"],
    },

    "Soybean___Southern_blight": {
        "pathogen_type": "fungal", "pathogen": "Sclerotium rolfsii",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Carbendazim 50WP soil drench or Tebuconazole 25EC",
            "dosage": "Carbendazim: 1g/L drench | Tebuconazole: 1ml/L",
            "frequency": "At first symptom — repeat every 14 days x2-3",
            "organic_alt": "Trichoderma harzianum 10g/plant",
            "chemical_options": [
                {"name": "Carbendazim 50WP soil drench", "dosage": "1g/L — 200ml/plant", "frequency": "Repeat 14 days"},
                {"name": "Tebuconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days x2-3"},
                {"name": "PCNB 2.5G soil", "dosage": "50g/plant", "frequency": "Once at sowing"},
            ],
            "organic_options": [{"name": "Trichoderma harzianum 10g/plant", "frequency": "At sowing + 45 DAS"}],
            "traditional_remedies": [{"name": "Deep summer ploughing", "notes": "MOST IMPORTANT — kills 70-80% overwintering inoculum"}],
            "when_to_apply": "Act IMMEDIATELY at first wilting.",
            "resistance_management": "Alternate Carbendazim with Tebuconazole.",
            "safety": "Carbendazim PHI 14 days.",
            "expected_recovery": "Girdled plants will die.",
        }},
        "cultural_practices": ["Deep summer ploughing — most effective practice", "Crop rotation 2-3 years", "Large FYM amounts", "Avoid waterlogging"],
    },

    "Soybean___Sudden_Death_Syndrone": {
        "pathogen_type": "fungal", "pathogen": "Fusarium virguliforme",
        "valid_actions": ["soil_fix", "fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"soil_fix": {
            "product": "Fluopyram seed treatment OR Metalaxyl + Thiram seed treatment",
            "dosage": "Fluopyram: 1.5ml/kg | Metalaxyl+Thiram: 3g/kg",
            "frequency": "ONCE at sowing — NO foliar cure",
            "organic_alt": "Trichoderma harzianum 4g/kg seed",
            "chemical_options": [
                {"name": "Fluopyram 480FS seed treatment", "dosage": "1.5ml/kg", "frequency": "Once"},
                {"name": "Metalaxyl + Thiram seed treatment", "dosage": "3g/kg", "frequency": "Once"},
            ],
            "organic_options": [{"name": "Trichoderma harzianum seed treatment", "dosage": "4g/kg", "frequency": "Once"}],
            "traditional_remedies": [{"name": "Deep tillage + residue management", "notes": "Buries residue where Fusarium survives"}],
            "when_to_apply": "ALL management must be at or before sowing.",
            "resistance_management": "Not applicable for seed treatments.",
            "safety": "Do not eat treated seed.",
            "expected_recovery": "No recovery once symptoms show — root damage already severe.",
            "notes": "SDS root infection happens early — foliar symptoms appear much later. NO foliar treatment works.",
        }},
        "cultural_practices": ["Improve soil drainage", "Avoid cold soil planting", "SDS-tolerant varieties", "Crop rotation"],
    },

    "Soybean___Yellow_Mosaic": {
        "pathogen_type": "viral", "pathogen": "Mungbean Yellow Mosaic Virus (whitefly vector)",
        "valid_actions": ["monitor"], "weather_class": "viral",
        "treatments": {"monitor": {
            "product": "NO CURE — Whitefly control + resistant varieties + rogue plants",
            "dosage": "Imidacloprid seed: 5g/kg | Thiamethoxam foliar: 0.25g/L",
            "frequency": "Seed once; foliar every 14-21 days; rogue daily first 6 weeks",
            "organic_alt": "Yellow sticky traps + neem oil + reflective mulch",
            "chemical_options": [
                {"name": "Imidacloprid 70WG seed treatment", "dosage": "5g/kg", "frequency": "Once — MOST IMPORTANT"},
                {"name": "Thiamethoxam 25WG foliar", "dosage": "0.25g/L", "frequency": "Every 21 days"},
                {"name": "Spiromesifen 22.9SC", "dosage": "1ml/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [{"name": "Yellow sticky traps", "dosage": "15-20/ha", "frequency": "Before planting"}],
            "traditional_remedies": [{"name": "Daily roguing", "notes": "Each infected plant is virus factory"}],
            "when_to_apply": "Prevention ONLY — control whiteflies BEFORE virus appears.",
            "resistance_management": "Rotate Imidacloprid → Thiamethoxam → Spiromesifen.",
            "safety": "Foliar neonicotinoids toxic to bees.",
            "expected_recovery": "NONE — remove and destroy infected plants.",
            "notes": "Most damaging soybean disease in India. Resistant varieties JS-335, SL-295, NRC-37 most important decision.",
        }},
        "cultural_practices": ["YMV-resistant varieties FIRST priority", "Sow on recommended date", "Imidacloprid seed treatment every season", "Rogue infected plants daily"],
    },

    "Soybean___bacterial_blight": {
        "pathogen_type": "bacterial", "pathogen": "Pseudomonas savastanoi pv. glycinea",
        "valid_actions": ["bactericide", "monitor"], "weather_class": "bacterial_spot",
        "treatments": {"bactericide": {
            "product": "Copper Oxychloride 50WP",
            "dosage": "3g/L", "frequency": "At first symptom — repeat every 10-14 days",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 10-14 days"},
                {"name": "Copper Hydroxide 50WP", "dosage": "3g/L", "frequency": "Every 10-14 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14 days"}],
            "traditional_remedies": [{"name": "Avoid field operations when wet", "notes": "Primary spread prevention"}],
            "when_to_apply": "Most critical after cool rainy weather.",
            "resistance_management": "Switch to kasugamycin if copper fails.",
            "safety": "Fungicide is COMPLETELY INEFFECTIVE.",
            "expected_recovery": "Existing spots do not heal.",
            "notes": "Bacterial — fungicide has ZERO effect.",
        }},
        "cultural_practices": ["Certified disease-free seed", "No overhead irrigation when wet", "Crop rotation"],
    },

    "Soybean___ferrugen": {
        "pathogen_type": "fungal", "pathogen": "Phakopsora pachyrhizi (Asian Soybean Rust)",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "rust",
        "treatments": {"fungicide": {
            "product": "Azoxystrobin + Propiconazole tank mix",
            "dosage": "1ml/L + 1ml/L", "frequency": "At R1 — critical first spray",
            "organic_alt": "Wettable sulfur 3g/L",
            "chemical_options": [
                {"name": "Azoxystrobin + Propiconazole", "dosage": "1ml/L + 1ml/L", "frequency": "At R1; repeat R3, R5"},
                {"name": "Fluxapyroxad 200SC", "dosage": "1ml/L", "frequency": "At R1"},
                {"name": "Trifloxystrobin + Tebuconazole", "dosage": "0.5g/L", "frequency": "At R1"},
            ],
            "organic_options": [{"name": "Wettable sulfur 80WP", "dosage": "3g/L", "frequency": "Every 10 days from flowering"}],
            "traditional_remedies": [{"name": "Cow urine + turmeric spray on leaf undersides", "notes": "Traditional Indian organic practice"}],
            "when_to_apply": "Scout from V6. First pustule = spray immediately.",
            "resistance_management": "QoI resistance documented in Brazil — rotate FRAC groups.",
            "safety": "PHI 7-14 days.",
            "expected_recovery": "Pustules stop sporulating 48-72 hours.",
        }},
        "cultural_practices": ["Plant early", "Rust-tolerant varieties", "Scout weekly from R1"],
    },

    "Soybean___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "rust",
        "treatments": {"monitor": {"product": "No treatment — preventive scouting", "dosage": "N/A", "frequency": "Weekly from R1", "organic_alt": "Preventive neem oil at R1"}},
        "cultural_practices": ["Scout weekly from V6", "Imidacloprid seed treatment if YMV risk", "Balanced K fertilisation"],
    },

    "Soybean___powdery_mildew": {
        "pathogen_type": "fungal", "pathogen": "Microsphaera diffusa",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Wettable Sulfur 80WP or Tebuconazole 25EC",
            "dosage": "Sulfur: 3g/L | Tebuconazole: 1ml/L",
            "frequency": "At first symptom — repeat every 10-14 days",
            "organic_alt": "Wettable sulfur 3g/L",
            "chemical_options": [
                {"name": "Wettable Sulfur 80WP", "dosage": "3g/L", "frequency": "Every 10 days"},
                {"name": "Tebuconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days (max 2)"},
            ],
            "organic_options": [{"name": "Wettable sulfur 80WP", "dosage": "3g/L", "frequency": "Every 7-10 days"}],
            "traditional_remedies": [{"name": "Baking soda spray", "notes": "Some efficacy at early stages"}],
            "when_to_apply": "First white patches on upper leaf surface.",
            "resistance_management": "Low resistance risk to sulfur.",
            "safety": "Sulfur: do NOT within 14 days of oil sprays.",
            "expected_recovery": "Colonies die 5-7 days. Often appears late season.",
        }},
        "cultural_practices": ["Improve canopy airflow", "Avoid excess nitrogen", "Scout from R3"],
    },

    "Squash___Powdery_mildew": {
        "pathogen_type": "fungal", "pathogen": "Podosphaera xanthii",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Wettable Sulfur 80WP or Myclobutanil 10WP",
            "dosage": "Sulfur: 3g/L | Myclobutanil: 1g/L",
            "frequency": "Every 7-10 days — spreads very fast on cucurbits",
            "organic_alt": "Wettable sulfur 3g/L",
            "chemical_options": [
                {"name": "Myclobutanil 10WP", "dosage": "1g/L", "frequency": "Every 10-14 days (max 4)"},
                {"name": "Wettable Sulfur 80WP", "dosage": "3g/L", "frequency": "Every 7-10 days"},
                {"name": "Tebuconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days (max 3)"},
            ],
            "organic_options": [{"name": "Full-fat milk 40%", "dosage": "400ml + 600ml water weekly", "notes": "Scientifically validated"}],
            "traditional_remedies": [{"name": "Baking soda + soap spray", "notes": "Raises leaf surface pH"}],
            "when_to_apply": "Act immediately at first white patches.",
            "resistance_management": "HIGH resistance — rotate FRAC 3 → FRAC 11 → M2.",
            "safety": "Sulfur: not within 14 days of oil sprays.",
            "expected_recovery": "Colonies die 5-7 days after fungicide.",
        }},
        "cultural_practices": ["Adequate plant spacing", "Remove infected leaves early", "Avoid overhead evening watering"],
    },

    "Strawberry___Leaf_scorch": {
        "pathogen_type": "fungal", "pathogen": "Diplocarpon earlianum",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Captan 50WP or Myclobutanil 10WP",
            "dosage": "Captan: 2g/L | Myclobutanil: 1g/L",
            "frequency": "Every 10-14 days from new growth through fruiting",
            "organic_alt": "Copper oxychloride 3g/L",
            "chemical_options": [
                {"name": "Captan 50WP", "dosage": "2g/L", "frequency": "Every 10-14 days"},
                {"name": "Myclobutanil 10WP", "dosage": "1g/L", "frequency": "Every 14 days (max 4)"},
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "Every 14-21 days (max 4)"},
            ],
            "organic_options": [{"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 14 days"}],
            "traditional_remedies": [{"name": "Post-harvest leaf litter cleanup", "notes": "MOST IMPORTANT — removes overwintering inoculum"}],
            "when_to_apply": "Preventive from new growth.",
            "resistance_management": "Rotate M4 → FRAC 3 → FRAC 11.",
            "safety": "Captan PHI 3 days.",
            "expected_recovery": "Lesions dry 7-10 days after fungicide.",
        }},
        "cultural_practices": ["Remove ALL old leaves after harvest", "Drip irrigation", "30cm spacing"],
    },

    "Strawberry___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment needed", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Preventive Captan at new growth"}},
        "cultural_practices": ["Post-harvest renovation", "Monitor for Botrytis, Leaf Scorch, Powdery Mildew", "Drip irrigation"],
    },

    "Sugarcane___Healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment needed", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Monthly preventive spray"}},
        "cultural_practices": ["Certified disease-free sets EVERY season", "Monitor monthly for Red Rot, Rust, Smut", "Ensure adequate drainage"],
    },

    "Sugarcane___Mosaic": {
        "pathogen_type": "viral", "pathogen": "Sugarcane Mosaic Virus (aphid vector)",
        "valid_actions": ["monitor"], "weather_class": "viral",
        "treatments": {"monitor": {
            "product": "NO CURE — Aphid vector control + rogue plants",
            "dosage": "Imidacloprid 0.5ml/L",
            "frequency": "Aphid control weekly first 3 months",
            "organic_alt": "Yellow sticky traps + neem oil",
            "chemical_options": [
                {"name": "Imidacloprid 70WG sett treatment", "dosage": "5g/kg", "frequency": "Once before planting"},
                {"name": "Thiamethoxam 25WG foliar", "dosage": "0.25g/L", "frequency": "Every 21 days"},
            ],
            "organic_options": [{"name": "Yellow sticky traps", "dosage": "15-20/ha", "frequency": "From planting"}],
            "traditional_remedies": [{"name": "Rogue infected plants + lime drench", "notes": "Prevents regrowth as SCMV reservoir"}],
            "when_to_apply": "Aphid control most critical first 3 months.",
            "resistance_management": "Rotate Imidacloprid → Thiamethoxam.",
            "safety": "Not a human pathogen.",
            "expected_recovery": "NO recovery from viral infection.",
        }},
        "cultural_practices": ["Certified virus-tested setts", "Rogue infected plants immediately", "Control aphids continuously"],
    },

    "Sugarcane___RedRot": {
        "pathogen_type": "fungal", "pathogen": "Colletotrichum falcatum",
        "valid_actions": ["fungicide", "soil_fix", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Carbendazim 50WP sett treatment — ONLY effective prevention",
            "dosage": "1g/L soak 15-20 minutes",
            "frequency": "ONCE before planting",
            "organic_alt": "Hot water sett treatment 50°C x 1 hour",
            "chemical_options": [
                {"name": "Carbendazim 50WP sett treatment", "dosage": "1g/L soak", "frequency": "Once"},
                {"name": "Propiconazole 25EC sett treatment", "dosage": "1ml/L soak", "frequency": "Once"},
            ],
            "organic_options": [{"name": "Hot water sett treatment 50°C x 1hr", "notes": "PROVEN — ICAR recommended"}],
            "traditional_remedies": [{"name": "Ash-charcoal sett dip", "notes": "Traditional UP practice"}],
            "when_to_apply": "Sett treatment BEFORE PLANTING is ONLY effective timing.",
            "resistance_management": "Rotate Carbendazim with Propiconazole.",
            "safety": "Wear gloves and mask.",
            "expected_recovery": "Infected stalks cannot recover — remove and burn.",
            "notes": "MOST ECONOMICALLY DAMAGING sugarcane disease in India.",
        }},
        "cultural_practices": ["Certified disease-free setts EVERY SEASON", "Hot water treatment gold standard", "Remove and burn infected stalks"],
    },

    "Sugarcane___Rust": {
        "pathogen_type": "fungal", "pathogen": "Puccinia melanocephala",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "rust",
        "treatments": {"fungicide": {
            "product": "Propiconazole 25EC or Trifloxystrobin + Propiconazole",
            "dosage": "Propiconazole: 1ml/L", "frequency": "1-2 sprays at first pustule",
            "organic_alt": "Wettable sulfur 3g/L",
            "chemical_options": [
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "At first pustule"},
                {"name": "Trifloxystrobin + Propiconazole", "dosage": "0.5g/L", "frequency": "Once — long residual"},
            ],
            "organic_options": [{"name": "Wettable sulfur 80WP", "dosage": "3g/L", "frequency": "Every 10 days"}],
            "traditional_remedies": [{"name": "Resistant variety selection", "notes": "Co-86032, Co-0238 good tolerance"}],
            "when_to_apply": "Scout August-November.",
            "resistance_management": "Alternate Propiconazole with dual-mode product.",
            "safety": "PHI 14 days.",
            "expected_recovery": "Pustules stop sporulating 48-72 hours.",
        }},
        "cultural_practices": ["Plant resistant varieties", "Monitor August-November weekly", "Avoid excess nitrogen"],
    },

    "Sugarcane___Yellow": {
        "pathogen_type": "viral", "pathogen": "SCYLV or Mg/S deficiency — DIAGNOSE FIRST",
        "valid_actions": ["monitor", "soil_fix"], "weather_class": "viral",
        "treatments": {"soil_fix": {
            "product": "Diagnose first: viral = vector control; nutritional = MgSO4 foliar",
            "dosage": "MgSO4 5g/L | Imidacloprid 0.5ml/L for aphid",
            "frequency": "Foliar 3 sprays 15-day intervals",
            "organic_alt": "Dolomite lime 200kg/ha",
            "chemical_options": [{"name": "MgSO4 foliar 0.5%", "dosage": "5g/L", "frequency": "3 sprays — if Mg deficiency confirmed"}],
            "organic_options": [{"name": "Dolomite lime 200kg/ha", "frequency": "Once per season"}],
            "traditional_remedies": [{"name": "SOIL TEST FIRST", "notes": "Most important step before treating any yellowing"}],
            "when_to_apply": "Diagnose before treating.",
            "resistance_management": "Not applicable.",
            "safety": "Over-application of MgSO4 can acidify soil.",
            "expected_recovery": "Mg deficiency: improvement in 10-14 days.",
        }},
        "cultural_practices": ["Soil test before treating yellowing", "For SCYLV: virus-free setts + vector control", "For Mg: dolomite lime"],
    },

    "Tea___Anthracnose": {
        "pathogen_type": "fungal", "pathogen": "Colletotrichum camelliae",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Carbendazim 50WP or Copper Oxychloride 50WP",
            "dosage": "Carbendazim: 1g/L | Copper: 3g/L",
            "frequency": "Every 14 days during monsoon",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Carbendazim 50WP", "dosage": "1g/L", "frequency": "Every 14 days (max 3)"},
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 14 days"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14-21 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14 days"}],
            "traditional_remedies": [{"name": "Bordeaux paste on pruning cuts within 30 minutes", "notes": "Critical traditional practice"}],
            "when_to_apply": "Preventive before monsoon (May-June).",
            "resistance_management": "Rotate Carbendazim → Copper → Propiconazole.",
            "safety": "Carbendazim PHI 7 days.",
            "expected_recovery": "Infected shoots dry up 14 days.",
        }},
        "cultural_practices": ["Prune infected shoots; seal with Bordeaux paste", "30-50% shade density", "Adequate K nutrition"],
    },

    "Tea___algal_leaf": {
        "pathogen_type": "algal", "pathogen": "Cephaleuros parasiticus",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Copper Oxychloride 50WP — copper toxic to photosynthetic algae",
            "dosage": "3g/L", "frequency": "2-3 sprays 21-day intervals",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [{"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "2-3 sprays"}],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 21 days"}],
            "traditional_remedies": [{"name": "Improve drainage and airflow", "notes": "Reduces algal leaf 50-60% without spraying"}],
            "when_to_apply": "During monsoon when orange-red patches appear.",
            "resistance_management": "Not applicable — algae no chemical resistance.",
            "safety": "Copper PHI 14 days.",
            "expected_recovery": "Patches dry off 2-3 weeks.",
        }},
        "cultural_practices": ["Improve field drainage — MOST IMPORTANT", "Thin shade trees", "Apply lime around plants"],
    },

    "Tea___bird_eye_spot": {
        "pathogen_type": "fungal", "pathogen": "Cercospora theae",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Copper Oxychloride 50WP or Mancozeb 75WP",
            "dosage": "Copper: 3g/L | Mancozeb: 2g/L",
            "frequency": "Every 14-21 days",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 14-21 days"},
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 21 days"}],
            "traditional_remedies": [{"name": "K sulfate topdress 50kg/ha", "notes": "K-deficient tea shows more spotting"}],
            "when_to_apply": "Preventive during monsoon.",
            "resistance_management": "Rotate copper with Mancozeb.",
            "safety": "Copper PHI 14 days.",
            "expected_recovery": "Spots stop spreading within 7-10 days.",
        }},
        "cultural_practices": ["Remove infected leaves during plucking", "Improve canopy airflow", "Adequate K and P nutrition"],
    },

    "Tea___brown_blight": {
        "pathogen_type": "fungal", "pathogen": "Colletotrichum camelliae / Pestalotiopsis theae",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Carbendazim 50WP or Copper Oxychloride 50WP",
            "dosage": "Carbendazim: 1g/L | Copper: 3g/L",
            "frequency": "Every 14 days during monsoon",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Carbendazim 50WP", "dosage": "1g/L", "frequency": "Every 14 days (max 3)"},
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 14-21 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14 days"}],
            "traditional_remedies": [{"name": "Pruning + Bordeaux paste", "notes": "Removes inoculum"}],
            "when_to_apply": "Begin at monsoon onset.",
            "resistance_management": "Rotate Carbendazim with copper.",
            "safety": "Carbendazim PHI 7 days.",
            "expected_recovery": "Infected shoots dry out.",
        }},
        "cultural_practices": ["Prune infected shoots; seal wounds", "30-50% shade management", "Good field drainage"],
    },

    "Tea___gray_light": {
        "pathogen_type": "fungal", "pathogen": "Pestalotiopsis theae",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Mancozeb 75WP or Copper Oxychloride 50WP",
            "dosage": "Mancozeb: 2.5g/L | Copper: 3g/L",
            "frequency": "Every 14 days during humid conditions",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Mancozeb 75WP", "dosage": "2.5g/L", "frequency": "Every 14 days"},
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14-21 days"}],
            "traditional_remedies": [{"name": "Hard pruning of infected stems", "notes": "Pruning faster than spraying alone"}],
            "when_to_apply": "Scout after monsoon onset.",
            "resistance_management": "Alternate Mancozeb with copper.",
            "safety": "Mancozeb PHI 7 days.",
            "expected_recovery": "Hard prune + 2-3 sprays for clean re-growth.",
        }},
        "cultural_practices": ["Hard prune infected areas", "Bordeaux paste on wounds", "Improve shade and drainage"],
    },

    "Tea___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {"product": "No treatment — preventive copper before monsoon", "dosage": "N/A", "frequency": "Weekly", "organic_alt": "Preventive Bordeaux at monsoon"}},
        "cultural_practices": ["Preventive Bordeaux at monsoon onset", "Monitor weekly for diseases", "Balanced NPK programme"],
    },

    "Tea___red_leaf_spot": {
        "pathogen_type": "fungal", "pathogen": "Phyllosticta theaefolia",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Mancozeb 75WP or Copper Oxychloride 50WP",
            "dosage": "Mancozeb: 2.5g/L | Copper: 3g/L",
            "frequency": "Every 14 days during monsoon",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Mancozeb 75WP", "dosage": "2.5g/L", "frequency": "Every 14 days"},
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14 days"}],
            "traditional_remedies": [{"name": "Improved drainage", "notes": "Consistently worse in wet sections"}],
            "when_to_apply": "Before monsoon and continue.",
            "resistance_management": "Rotate Mancozeb with copper.",
            "safety": "Mancozeb PHI 7 days.",
            "expected_recovery": "Spots remain but stop spreading.",
        }},
        "cultural_practices": ["Improve drainage", "Remove infected leaves during plucking", "Balanced P nutrition"],
    },

    "Tea___white_spot": {
        "pathogen_type": "fungal", "pathogen": "Cercosporella theae",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Copper Oxychloride 50WP",
            "dosage": "3g/L", "frequency": "Every 14-21 days",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 14-21 days"},
                {"name": "Mancozeb 75WP", "dosage": "2.5g/L", "frequency": "Every 14 days"},
            ],
            "organic_options": [{"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14-21 days"}],
            "traditional_remedies": [{"name": "Prune and lime dress", "notes": "Traditional practice"}],
            "when_to_apply": "Preventive at start of rainy season.",
            "resistance_management": "Alternate copper with Mancozeb.",
            "safety": "Copper PHI 14 days.",
            "expected_recovery": "Spots remain but stop spreading.",
        }},
        "cultural_practices": ["Remove infected leaves", "Preventive copper before monsoon", "Balanced K nutrition"],
    },


    # ════════════ TOMATO ══════════════════════════════════════════════════════

    "Tomato___Bacterial_spot": {
        "pathogen_type": "bacterial", "pathogen": "Xanthomonas campestris pv. vesicatoria / X. perforans",
        "valid_actions": ["bactericide", "irrigation", "monitor"], "weather_class": "bacterial_spot",
        "treatments": {"bactericide": {
            "product": "Copper Hydroxide 50WP + Mancozeb 75WP tank mix (ALWAYS tank mix — reduces resistance)",
            "dosage": "Copper: 3g/L + Mancozeb: 2g/L",
            "frequency": "Every 7 days in warm/wet; 14 days moderate",
            "organic_alt": "Bordeaux mixture 1%",
            "chemical_options": [
                {"name": "Copper Hydroxide 50WP + Mancozeb 75WP", "dosage": "3g/L + 2g/L", "frequency": "Every 7-10 days", "type": "Standard resistance-management tank mix — ICAR-IIVR recommended"},
                {"name": "Copper Oxychloride 50WP + Mancozeb", "dosage": "2g/L + 2g/L", "frequency": "Every 7-10 days", "type": "Alternative copper — more phytotoxic above 35°C"},
                {"name": "Kasugamycin 3L", "dosage": "2ml/L", "frequency": "Every 10-14 days (max 3)", "type": "Antibiotic — for copper-resistant strains"},
                {"name": "Streptomycin Sulfate 17WP + Copper", "dosage": "0.5g/L + 2g/L", "frequency": "Every 10 days (max 3)", "type": "Older antibiotic — check state approval"},
            ],
            "organic_options": [
                {"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L fresh", "frequency": "Every 10-14 days"},
                {"name": "Pseudomonas chlororaphis bio-bactericide", "dosage": "10g/L", "frequency": "Every 14 days"},
            ],
            "traditional_remedies": [
                {"name": "Turmeric + copper sulfate spray", "method": "30g turmeric + 2g CuSO4/1L; strain; spray", "notes": "Curcumin antibacterial against Xanthomonas + copper bactericidal — traditional Karnataka vegetable farming"},
                {"name": "Cow urine 1:10 + turmeric spray", "method": "100ml cow urine + 30g turmeric/1L; strain; spray weekly", "notes": "Traditional organic practice widely used in Maharashtra organic tomato"},
            ],
            "when_to_apply": "Apply BEFORE predicted rain. Morning application. Do NOT work in field when plants are wet.",
            "resistance_management": "Copper resistance WIDESPREAD in India. ALWAYS tank mix with Mancozeb. If copper failing — Kasugamycin.",
            "safety": "CRITICAL: Fungicide is COMPLETELY INEFFECTIVE. Copper PHI 0-3 days. Kasugamycin PHI 7 days.",
            "expected_recovery": "Existing spots do not heal. New growth clean after 2-3 sprays.",
            "notes": "BACTERIAL — FUNGICIDE HAS ZERO EFFECT.",
        }},
        "cultural_practices": [
            "Drip irrigation ONLY — overhead irrigation is the primary disease spread mechanism in Indian tomato",
            "Certified disease-free seed; copper oxychloride 2g/kg seed treatment",
            "Never work in field when wet — hands spread bacteria",
            "Crop rotation: 2 years from solanaceous crops",
            "Stake plants for better air movement and faster drying",
        ],
    },

    "Tomato___Early_blight": {
        "pathogen_type": "fungal", "pathogen": "Alternaria solani",
        "valid_actions": ["fungicide", "soil_fix", "irrigation", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Chlorothalonil 75WP or Mancozeb 75WP",
            "dosage": "2g/L", "frequency": "Every 7-10 days from first target-shaped lesion",
            "organic_alt": "Copper oxychloride 3g/L or Bordeaux 1%",
            "chemical_options": [
                {"name": "Chlorothalonil 75WP", "dosage": "2g/L", "frequency": "Every 7-10 days", "type": "Protective multi-site — ICAR-IIVR; multi-site reduces resistance"},
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 7-10 days", "type": "Protective contact"},
                {"name": "Azoxystrobin 23SC + Difenoconazole 25EC", "dosage": "0.75ml/L + 0.3ml/L", "frequency": "Every 14 days (max 3)", "type": "Dual-mode systemic premium — processing tomatoes"},
                {"name": "Difenoconazole 25EC", "dosage": "0.5ml/L", "frequency": "Every 14 days (max 3)", "type": "Premium DMI — excellent curative activity on Alternaria"},
                {"name": "Iprodione 50WP", "dosage": "1.5g/L", "frequency": "Every 14 days (max 2)", "type": "SDHI — specific Alternaria activity; rotate with M3"},
            ],
            "organic_options": [
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 10-14 days"},
                {"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14 days — stop 3 weeks before harvest"},
                {"name": "NSKE 5%", "dosage": "50g/L overnight; strain; spray weekly"},
            ],
            "traditional_remedies": [
                {"name": "Turmeric powder spray", "method": "30g turmeric/1L; boil 10 min; cool; strain; dilute 1:5; spray", "notes": "Curcumin antifungal against Alternaria — traditional Tamil Nadu/Kerala organic vegetable"},
                {"name": "Panchagavya 3% monthly", "method": "Ferment 7 days; dilute 3%; spray monthly"},
            ],
            "when_to_apply": "Scout from 3 weeks after transplanting. First lesion = spray immediately. Threshold: 5% leaves. Early morning application only.",
            "resistance_management": "Alternate FRAC M5 (Chlorothalonil) with FRAC M3 (Mancozeb). Add FRAC 11 or FRAC 3 max 2-3 times per crop. Avoid repeated SDHI (FRAC 7) — resistance builds quickly.",
            "safety": "Chlorothalonil IARC Group 2B — respirator and gloves mandatory. PHI 7 days. Mancozeb PHI 7 days. Azoxystrobin PHI 0 days.",
            "expected_recovery": "Remove lower infected leaves — inoculum sources. Upper canopy protected with 2-3 timely sprays.",
        }},
        "cultural_practices": [
            "Paddy straw or silver mulch around plant base — prevents soil splash initiation of lower leaf infection",
            "Stake plants 45-60cm off ground — improves air circulation",
            "Drip or furrow irrigation ONLY — overhead creates leaf wetness triggering epidemics",
            "Remove lower infected leaves as soon as disease appears",
            "Crop rotation: 2-year minimum from solanaceous crops",
        ],
    },

    "Tomato___Late_blight": {
        "pathogen_type": "oomycete (fungal-like)", "pathogen": "Phytophthora infestans",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "late_blight_oomycete",
        "treatments": {"fungicide": {
            "product": "Metalaxyl-M 8% + Mancozeb 64% WP — GOLD STANDARD",
            "dosage": "2.5g/L", "frequency": "Every 5-7 days in cool (10-20°C) humid — DO NOT DELAY",
            "organic_alt": "Copper Hydroxide 3g/L + Mancozeb 2g/L tank mix (limited efficacy)",
            "chemical_options": [
                {"name": "Metalaxyl-M 8% + Mancozeb 64% WP", "dosage": "2.5g/L", "frequency": "Every 7 days; 5 days severe", "type": "Phenylamide + protective GOLD STANDARD"},
                {"name": "Cymoxanil 8% + Mancozeb 64% WP", "dosage": "2.5g/L", "frequency": "Every 7 days", "type": "Translaminar + protective — when metalaxyl resistance"},
                {"name": "Dimethomorph 50WP + Mancozeb", "dosage": "1g/L + 2g/L", "frequency": "Every 7 days", "type": "FRAC 40 — rotation product"},
                {"name": "Propamocarb 72.2SL", "dosage": "1.5ml/L", "frequency": "Every 7-10 days", "type": "Systemic — excellent fruit protection"},
                {"name": "Ametoctradin + Dimethomorph", "dosage": "2ml/L", "frequency": "Every 7-10 days", "type": "Novel dual-mode CAA — no cross-resistance with metalaxyl"},
            ],
            "organic_options": [
                {"name": "Copper Hydroxide 50WP + Mancozeb 75WP", "dosage": "3g/L + 2g/L", "frequency": "Every 5-7 days"},
                {"name": "Bordeaux 1.5%", "dosage": "15g CuSO4 + 15g lime/L", "frequency": "Every 5-7 days severe"},
            ],
            "traditional_remedies": [
                {"name": "IMMEDIATE plant removal", "method": "First sign: bag plant + 30cm soil; remove from field; burn; lime the area", "notes": "MOST CRITICAL action — one plant infects 10 neighbours within 3-5 days; traditional UP/HP farmers practice daily scouting + same-day removal"},
                {"name": "Hilling to protect tubers/base", "method": "Add 10cm soil around stem when disease appears", "notes": "Traditional protection of stem base from spore wash"},
                {"name": "Jeevamrutha soil drench monthly", "method": "Fermented bio-input 10% dilution monthly", "notes": "Promotes beneficial soil biology; used in organic tomato in Himachal Pradesh"},
            ],
            "when_to_apply": "EMERGENCY — apply within 24 hours of first lesion or high-risk forecast. Late blight can destroy 100% foliage in 5-7 days.",
            "resistance_management": "MAJOR metalaxyl resistance in India. NEVER use alone. Rotate: FRAC 4+M3 → FRAC 27+M3 → FRAC 40+M3. Limit metalaxyl family to 4 sprays per crop.",
            "safety": "Delay is not an option. Metalaxyl-M PHI 7 days. Full PPE — airborne sporangia.",
            "expected_recovery": "Infected tissue cannot recover. Haulm destruction when >75% infected — protects fruit from further infection.",
            "notes": "HIGHEST PRIORITY tomato disease — especially in Indian hills (HP, UK, J&K), Pune plateau, Ooty. Emergency treatment required.",
        }},
        "cultural_practices": [
            "Monitor daily weather — explodes at 10-20°C + leaf wetness >10 hours",
            "Certified disease-free transplants",
            "60cm plant spacing — better airflow slows spread",
            "REMOVE infected plants IMMEDIATELY on first detection",
            "Stake all plants — keeps foliage off ground",
            "Destroy solanaceous weeds around field — alternative P. infestans hosts",
        ],
    },

    "Tomato___Leaf_Mold": {
        "pathogen_type": "fungal", "pathogen": "Passalora fulva (Cladosporium fulvum)",
        "valid_actions": ["fungicide", "irrigation", "monitor"], "weather_class": "leaf_mold",
        "treatments": {"fungicide": {
            "product": "Chlorothalonil 75WP or Mancozeb 75WP — spray specifically on leaf UNDERSIDES",
            "dosage": "2g/L", "frequency": "Every 7-10 days — critical in polyhouse conditions",
            "organic_alt": "Copper oxychloride 3g/L on leaf undersides",
            "chemical_options": [
                {"name": "Chlorothalonil 75WP", "dosage": "2g/L", "frequency": "Every 7-10 days", "type": "Protective — apply on leaf undersides where C. fulvum sporulates"},
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 7-10 days", "type": "Protective — tank mix with Chlorothalonil"},
                {"name": "Myclobutanil 10WP", "dosage": "1g/L", "frequency": "Every 14 days", "type": "DMI systemic curative — when established"},
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "Every 14-21 days", "type": "QoI systemic — broad-spectrum for polyhouse multiple diseases"},
            ],
            "organic_options": [
                {"name": "Copper Oxychloride 50WP — on leaf undersides", "dosage": "3g/L", "frequency": "Every 10-14 days"},
                {"name": "Potassium bicarbonate 0.5%", "dosage": "5g/L", "frequency": "Every 7-10 days"},
            ],
            "traditional_remedies": [
                {"name": "Increase ventilation FIRST", "method": "Open all polyhouse vents; install shade net sides; reduce plant density — Leaf Mold CANNOT sporulate below 75% RH", "notes": "MOST IMPORTANT action — ventilation management alone can eliminate Leaf Mold in polyhouses"},
                {"name": "Full-fat milk 40% spray", "method": "400ml milk + 600ml water; spray weekly on leaves", "notes": "Scientifically validated — milk proteins create antifungal compounds under UV; practical for small polyhouses"},
            ],
            "when_to_apply": "Spray on leaf undersides specifically — C. fulvum sporulates on lower leaf surface only.",
            "resistance_management": "Alternate Chlorothalonil (M5) → Mancozeb (M3) → DMI (FRAC 3). Max 2 consecutive systemics.",
            "safety": "Chlorothalonil PHI 7 days. Full PPE in polyhouse — enclosed space increases exposure.",
            "expected_recovery": "Existing mold stops sporulating 5-7 days. New leaves clean after 2-3 sprays. Key: reduce polyhouse humidity — fungicide alone insufficient.",
        }},
        "cultural_practices": [
            "MOST IMPORTANT: Reduce polyhouse humidity below 75% — Leaf Mold CANNOT sporulate below this level",
            "Increase plant spacing 45-50cm between plants",
            "Remove and destroy infected leaves immediately",
            "Drip irrigation only — water in morning",
            "Prune lower leaves early for base air circulation",
        ],
    },

    "Tomato___Septoria_leaf_spot": {
        "pathogen_type": "fungal", "pathogen": "Septoria lycopersici",
        "valid_actions": ["fungicide", "irrigation", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Chlorothalonil 75WP or Mancozeb 75WP",
            "dosage": "2g/L", "frequency": "Every 7-10 days from first tiny white spots with dark borders",
            "organic_alt": "Copper oxychloride 3g/L or Bordeaux 1%",
            "chemical_options": [
                {"name": "Chlorothalonil 75WP", "dosage": "2g/L", "frequency": "Every 7-10 days", "type": "Standard — same spray programme as Early Blight"},
                {"name": "Mancozeb 75WP", "dosage": "2g/L", "frequency": "Every 7-10 days", "type": "Equally effective on Septoria and Early Blight — one programme for both"},
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "Every 14 days (max 3)", "type": "QoI — controls Septoria + Early Blight + Late Blight simultaneously"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days", "type": "DMI curative — when Septoria well-established"},
            ],
            "organic_options": [
                {"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 10-14 days"},
                {"name": "Bordeaux mixture 1%", "dosage": "10g CuSO4 + 10g lime/L", "frequency": "Every 14 days"},
            ],
            "traditional_remedies": [
                {"name": "Mulching + de-leafing combination", "method": "Apply paddy straw or silver mulch around plant base; remove lower infected leaves simultaneously", "notes": "Mulch blocks soil splash (Septoria primary source); de-leafing removes inoculum — combination reduces severity 60-70% without spray; traditional practice in Karnataka and Maharashtra vegetable farms"},
            ],
            "when_to_apply": "First tiny (1-3mm) circular spots with white centers and dark borders on oldest leaves = spray immediately. Disease progresses bottom to top.",
            "resistance_management": "Alternate Chlorothalonil (M5) with Mancozeb (M3) every 2-3 sprays. Add systemic max 2-3 sprays per crop.",
            "safety": "Chlorothalonil PHI 7 days. Mancozeb PHI 7 days. Azoxystrobin PHI 0 days.",
            "expected_recovery": "Remove lower spotted leaves — inoculum sources. Upper canopy protected by timely sprays.",
        }},
        "cultural_practices": [
            "Mulch around base — Septoria spores splash from soil to lower leaves",
            "Remove lower infected leaves as soon as spotted",
            "Drip irrigation only — overhead triggers Septoria epidemics",
            "Crop rotation: 2-year minimum from solanaceous",
            "Stake plants for air movement",
        ],
    },

    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "pathogen_type": "pest", "pathogen": "Tetranychus urticae (Two-spotted Spider Mite)",
        "valid_actions": ["irrigation", "monitor"], "weather_class": "pest",
        "treatments": {"irrigation": {
            "product": "Abamectin 1.8EC or Spiromesifen 22.9SC",
            "dosage": "Abamectin: 0.5ml/L | Spiromesifen: 1ml/L",
            "frequency": "At first detection; repeat after 7-10 days — must do 2 applications to cover egg hatch",
            "organic_alt": "Neem oil 0.5% + insecticidal soap; daily strong water spray on leaf undersides",
            "chemical_options": [
                {"name": "Abamectin 1.8EC", "dosage": "0.5ml/L", "frequency": "Every 7-10 days x2", "type": "Macrolide miticide — translaminar; apply to leaf undersides"},
                {"name": "Spiromesifen 22.9SC", "dosage": "1ml/L", "frequency": "Every 7-10 days x2", "type": "Tetronic acid — excellent on eggs and nymphs"},
                {"name": "Hexythiazox 5.45EC", "dosage": "1ml/L", "frequency": "Once — long residual", "type": "METI inhibitor — ovicide + larvicide"},
                {"name": "Bifenazate 22.6SC", "dosage": "1ml/L", "frequency": "Every 10-14 days (max 2)", "type": "Hydrazine — fast knockdown all stages; no cross-resistance"},
                {"name": "Fenpyroximate 5SC", "dosage": "1ml/L", "frequency": "Every 10-14 days", "type": "METI inhibitor — broad-spectrum all life stages"},
            ],
            "organic_options": [
                {"name": "Neem oil 0.5% + insecticidal soap", "dosage": "5ml neem oil + 5ml soap/L", "frequency": "Every 5-7 days x3-4"},
                {"name": "Phytoseiulus persimilis predatory mites", "dosage": "50 predators/sq metre — release in evening", "frequency": "Once — predators reproduce; excellent in polyhouses"},
                {"name": "Strong water spray force on leaf undersides", "dosage": "Jet setting — forceful spray", "frequency": "Every 2-3 days during mite outbreak"},
            ],
            "traditional_remedies": [
                {"name": "Garlic + onion + chilli extract", "method": "100g garlic + 100g onion + 20g chilli/1L; strain; dilute 1:5; spray leaf undersides", "notes": "Traditional repellent — allicin + quercetin + capsaicin disrupt mite feeding; used in IPM in Kerala and Tamil Nadu organic farming"},
                {"name": "Tobacco decoction", "method": "40g tobacco leaves boiled in 1L for 30 min; cool; strain; dilute 1:4; spray leaf undersides", "notes": "Natural nicotine miticide — traditional practice; DO NOT spray within 3 weeks of harvest; wash hands thoroughly"},
                {"name": "Daily water misting on leaf undersides", "method": "Mist with water spray on leaf undersides daily during hot/dry weather", "notes": "Mites THRIVE above 35°C, low humidity — daily misting creates hostile conditions; traditional Karnataka/Maharashtra farmer first response"},
            ],
            "when_to_apply": "Scout from V3 — check UNDERSIDES of lower leaves for tiny moving dots, webbing, yellow stippling. Chemical threshold: 5-10 mites/leaf or visible webbing. Apply miticides on leaf undersides.",
            "resistance_management": "Spider mites have EXTREME resistance evolution. Rotate: FRAC 21A (Fenpyroximate/Bifenazate) → Macrolide (Abamectin) → Tetronic acid (Spiromesifen) → 21A. NEVER same class twice consecutively.",
            "safety": "Apply morning or evening only — heat reduces efficacy. Abamectin PHI 7 days. Spiromesifen PHI 1 day. Extremely toxic to bees — never apply during bloom.",
            "expected_recovery": "First spray kills 80-90% adults/nymphs. Second spray kills hatching eggs. Population collapses 14-21 days. Release Phytoseiulus as follow-up to prevent re-infestation.",
        }},
        "cultural_practices": [
            "Remove heavily infested leaves — reduces mite population and eggs",
            "Increase irrigation during hot/dry weather — mites peak in hot, dry, dusty conditions",
            "Release Phytoseiulus persimilis in polyhouses — excellent long-term biological control",
            "Avoid broad-spectrum insecticides that kill natural predators — mites explode when natural enemies eliminated",
            "Monitor at least twice weekly from V6 — 2-week window from detection to economic loss is very short",
        ],
    },

    "Tomato___Target_Spot": {
        "pathogen_type": "fungal", "pathogen": "Corynespora cassiicola",
        "valid_actions": ["fungicide", "monitor"], "weather_class": "fungal_blight",
        "treatments": {"fungicide": {
            "product": "Chlorothalonil 75WP or Azoxystrobin 23SC",
            "dosage": "Chlorothalonil: 2g/L | Azoxystrobin: 1ml/L",
            "frequency": "Every 7-10 days from first large concentric ring lesions",
            "organic_alt": "Copper oxychloride 3g/L",
            "chemical_options": [
                {"name": "Chlorothalonil 75WP", "dosage": "2g/L", "frequency": "Every 7-10 days", "type": "Protective — integrates with early blight programme"},
                {"name": "Azoxystrobin 23SC", "dosage": "1ml/L", "frequency": "Every 14 days (max 3)", "type": "QoI systemic — excellent Target Spot + Early Blight simultaneously"},
                {"name": "Propiconazole 25EC", "dosage": "1ml/L", "frequency": "Every 14 days", "type": "DMI curative on Corynespora"},
                {"name": "Boscalid", "dosage": "0.5g/L", "frequency": "Every 14-21 days (max 2)", "type": "SDHI premium — excellent Corynespora activity; long residual"},
            ],
            "organic_options": [{"name": "Copper Oxychloride 50WP", "dosage": "3g/L", "frequency": "Every 10-14 days"}],
            "traditional_remedies": [{"name": "Crop rotation + debris removal", "method": "Remove all tomato debris after harvest; deep plough; rotate to non-solanaceous", "notes": "C. cassiicola survives in soil debris — debris removal + rotation most effective long-term management"}],
            "when_to_apply": "Target Spot lesions: larger (1-2cm) than Septoria, distinct concentric rings. Begin at first lesion on lower leaves.",
            "resistance_management": "Rotate Chlorothalonil (M5) → Azoxystrobin (FRAC 11) → DMI (FRAC 3). SDHI max 2/crop.",
            "safety": "Azoxystrobin PHI 0 days. Chlorothalonil PHI 7 days. Propiconazole PHI 7 days.",
            "expected_recovery": "Lesions do not disappear. Fungicide stops new infection. Upper canopy protected with consistent 7-10 day programme.",
        }},
        "cultural_practices": [
            "Remove and destroy plant debris after harvest",
            "Crop rotation: 2-year break from tomato/cucurbit",
            "Remove infected lower leaves as soon as lesions appear",
            "Stake plants and prune lower leaves for air circulation",
            "Drip or furrow irrigation preferred",
        ],
    },

    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "pathogen_type": "viral", "pathogen": "Tomato Yellow Leaf Curl Virus (TYLCV) — silverleaf whitefly Bemisia tabaci biotype B",
        "valid_actions": ["monitor"], "weather_class": "viral",
        "treatments": {"monitor": {
            "product": "NO CURE — Whitefly vector control + TYLCV-resistant varieties + rogue infected plants",
            "dosage": "Imidacloprid 0.5ml/L or Thiamethoxam 0.25g/L for whitefly",
            "frequency": "Nursery drench once; foliar every 14-21 days; rogue daily first 6 weeks",
            "organic_alt": "Silver reflective mulch + yellow sticky traps + neem oil 0.5% + remove infected plants",
            "chemical_options": [
                {"name": "Imidacloprid 70WG nursery drench", "dosage": "5g/L — drench nursery trays 2-3 days before transplanting", "frequency": "Once", "type": "MOST IMPORTANT — protects transplants 3-4 weeks during critical establishment"},
                {"name": "Thiamethoxam 25WG foliar", "dosage": "0.25g/L", "frequency": "Every 14-21 days after nursery protection expires"},
                {"name": "Spirotetramat 15SC", "dosage": "0.75ml/L", "frequency": "Every 14-21 days when nymphs present", "type": "Phloem-mobile — reaches nymphs on leaf undersides"},
                {"name": "Pyriproxyfen 10EC (IGR)", "dosage": "1ml/L", "frequency": "Every 14-21 days", "type": "Disrupts whitefly reproduction — breaks life cycle"},
            ],
            "organic_options": [
                {"name": "Silver reflective mulch before transplanting", "notes": "PROVEN — reduces TYLCV incidence 40-60% in Indian trials"},
                {"name": "Yellow sticky traps 15-20/ha", "frequency": "Install before transplanting"},
                {"name": "Neem oil 0.5%", "dosage": "5ml/L + soap", "frequency": "Every 7-10 days"},
            ],
            "traditional_remedies": [
                {"name": "Maize border rows (3-4 rows)", "method": "Plant around entire field perimeter before tomato transplanting", "notes": "Traditional barrier cropping — reduces whitefly immigration; used by traditional farmers in Maharashtra and Karnataka"},
                {"name": "Daily roguing as family task", "method": "Walk through field each morning; uproot yellow-curled plants; bag and remove", "notes": "Traditional IPM wisdom — each infected plant is virus reservoir; practiced in Karnataka and Tamil Nadu commercial tomato"},
            ],
            "when_to_apply": "Apply nursery neonicotinoid drench BEFORE transplanting — most critical timing. Begin sticky trap monitoring before transplanting.",
            "resistance_management": "B-biotype whitefly HIGH resistance risk. Rotate: Imidacloprid → Thiamethoxam → Spirotetramat → Pyriproxyfen.",
            "safety": "Neonicotinoid seed treatment toxic to birds. Foliar neonicotinoids extremely toxic to bees — DO NOT apply during bloom.",
            "expected_recovery": "NONE for infected plants — remove and destroy immediately.",
            "notes": "TYLCV = single most damaging tomato disease in India below 1000m. 70-100% crop failure in epidemic years. Use TYLCV-resistant varieties (TY-1 gene): Arka Rakshak, Naveen, commercial F1 hybrids.",
        }},
        "cultural_practices": [
            "FIRST PRIORITY: TYLCV-resistant variety with TY-1 gene — Arka Rakshak, Naveen, most modern commercial F1 hybrids",
            "Imidacloprid nursery drench 2-3 days before transplanting",
            "Silver reflective mulch before transplanting",
            "Rogue infected plants DAILY for first 6 weeks",
            "Avoid planting near cotton, brinjal, other solanaceous crops — shared whitefly populations",
        ],
    },

    "Tomato___Tomato_mosaic_virus": {
        "pathogen_type": "viral", "pathogen": "Tomato Mosaic Virus (ToMV) / Tobacco Mosaic Virus — CONTACT-TRANSMITTED + seed-borne",
        "valid_actions": ["monitor"], "weather_class": "viral",
        "treatments": {"monitor": {
            "product": "NO CURE — Contact transmission prevention + seed treatment + rogue plants",
            "dosage": "No chemical treatment for viral infection",
            "frequency": "Prevention: constant sanitation. Roguing: daily in first 6 weeks",
            "organic_alt": "ALL management non-chemical: sanitation, resistant variety, roguing",
            "chemical_options": [
                {"name": "Copper Sulfate tool dip", "dosage": "2g/L — dip all tools 30 seconds between EVERY plant", "frequency": "Every plant cut", "type": "Tool disinfection — ToMV spreads through sap-contaminated tools"},
                {"name": "Phosphate buffer spray (KHPO4 + Na2HPO4)", "dosage": "2g/L each monopotassium + disodium phosphate", "frequency": "Weekly preventive spray on healthy plants", "type": "SAR inducer — not a cure; preventive resistance induction"},
            ],
            "organic_options": [
                {"name": "Skim milk hand-washing before every plant contact", "notes": "MOST IMPORTANT — milk protein denatures ToMV on contact; practiced in commercial greenhouse tomato"},
                {"name": "Milk spray 2%", "dosage": "20ml/L on leaves weekly", "frequency": "Weekly preventive — milk proteins competitively exclude TMV particles"},
                {"name": "Potassium silicate 0.1% spray", "dosage": "1g/L weekly", "notes": "Silicon strengthens cell walls reducing mechanical virus entry; OMRI-listed"},
            ],
            "traditional_remedies": [
                {"name": "NO SMOKING rule in tomato field", "method": "STRICTLY prohibit all tobacco near tomato plants — tobacco use by workers infects tomato within minutes of contact", "notes": "ESSENTIAL RULE — Tobacco Mosaic Virus from tobacco products infects tomato immediately; wash hands TWICE with soap; traditional commercial tomato wisdom worldwide"},
                {"name": "One pruning knife per plant", "method": "Dedicate one sterilised knife per plant during pruning; soak in 10% bleach solution between plants", "notes": "Prevents sap transfer between plants — standard commercial tomato practice"},
            ],
            "when_to_apply": "All management is preventive — no treatment once a plant is infected. Prevention begins at seed source.",
            "resistance_management": "Variety selection: TM-2a gene provides complete ToMV resistance — use resistant varieties.",
            "safety": "ToMV is NOT a human pathogen — tomatoes from infected plants are safe to eat.",
            "expected_recovery": "NONE — remove infected plants immediately. Prevent spread through strict sanitation.",
            "notes": "ToMV can survive on dried plant material, in soil, and on tools for MONTHS. Once in a greenhouse — persists for years without sanitation. Resistance gene TM-2a in modern varieties provides complete resistance.",
        }},
        "cultural_practices": [
            "ToMV-resistant variety with TM-2a gene — ask seed company for virus resistance table; available in most modern commercial F1 hybrids",
            "Seed treatment: 10% trisodium phosphate (TSP) soak 15 minutes; wash thoroughly",
            "Wash hands with soap + milk before every entry into field — hand-washing station at field boundary",
            "ABSOLUTELY NO tobacco use near tomato field — TMV from tobacco infects within minutes",
            "Disinfect all pruning tools between EVERY plant — 10% bleach or 70% alcohol",
        ],
    },

    "Tomato___healthy": {
        "pathogen_type": "none", "valid_actions": ["monitor"], "weather_class": "fungal_blight",
        "treatments": {"monitor": {
            "product": "No treatment — begin preventive programme",
            "dosage": "N/A", "frequency": "Weekly inspection", "organic_alt": "Preventive copper before expected rain",
            "organic_options": [
                {"name": "Chlorothalonil 2g/L preventive spray", "dosage": "2g/L", "frequency": "Every 14 days from 3 weeks after transplanting"},
                {"name": "Neem oil 0.5% preventive", "dosage": "5ml/L", "frequency": "Weekly as general preventive"},
            ],
        }},
        "cultural_practices": [
            "Begin preventive fungicide programme 3 weeks after transplanting — do not wait for disease",
            "Scout weekly: leaf undersides for spider mites; lower leaves for early blight/septoria; stem base for Fusarium/Pythium",
            "Monitor for whitefly DAILY from transplanting — TYLCV management begins before first whitefly is seen",
            "Maintain drip irrigation + mulching from planting",
            "Stake all plants for better air movement",
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS — used by pipeline.py and recommendation_ml.py
# ══════════════════════════════════════════════════════════════════════════════

def parse_disease_label(raw_label: str) -> dict:
    """Parse a raw model label like 'Tomato___Bacterial_spot' into components."""
    if not raw_label:
        return {"crop": None, "disease_name": "Unknown", "raw_label": raw_label, "is_healthy": False}
    if "___" in raw_label:
        crop, disease = raw_label.split("___", 1)
    else:
        crop, disease = raw_label, "Unknown"
    crop = crop.replace("_", " ").replace(",", "").strip()
    disease_name = disease.replace("_", " ").strip()
    is_healthy = "healthy" in disease.lower()
    return {"crop": crop, "disease_name": disease_name, "raw_label": raw_label, "is_healthy": is_healthy}


def get_pathogen_info(disease_class: str) -> dict:
    """Return pathogen_type and pathogen name for a disease class."""
    entry = DISEASE_DB.get(disease_class, {})
    return {
        "pathogen_type": entry.get("pathogen_type", "unknown"),
        "pathogen": entry.get("pathogen", "Unknown pathogen"),
    }


def get_valid_actions(disease_class: str) -> list:
    """Return the biologically valid action set for a disease class."""
    entry = DISEASE_DB.get(disease_class, {})
    return entry.get("valid_actions", ALL_ACTIONS)


def get_weather_class(disease_class: str) -> str:
    entry = DISEASE_DB.get(disease_class, {})
    return entry.get("weather_class", "fungal_blight")


def get_treatment_detail(disease_class: str, action: str) -> dict:
    """Return the treatment detail dict for a disease+action combo. Empty if not found."""
    entry = DISEASE_DB.get(disease_class, {})
    return entry.get("treatments", {}).get(action, {})


def get_cultural_practices(disease_class: str) -> list:
    entry = DISEASE_DB.get(disease_class, {})
    return entry.get("cultural_practices", [])


def get_full_treatment_plan(disease_class: str = None, crop_type: str = None) -> dict:
    """
    Returns a complete treatment plan dict with chemical_options, organic_options,
    traditional_remedies, cultural_practices etc. for the frontend to render.
    Falls back to crop-level info if disease_class not found, then to generic.
    """
    entry = DISEASE_DB.get(disease_class, {}) if disease_class else {}

    if not entry and crop_type:
        entry = get_crop_fallback(crop_type)

    chemical_options = []
    organic_options = []
    traditional_remedies = []
    primary_action = None

    treatments = entry.get("treatments", {})
    for action, detail in treatments.items():
        if not primary_action:
            primary_action = action
        for opt in detail.get("chemical_options", []):
            chemical_options.append({**opt, "category": "Chemical", "action": action})
        for opt in detail.get("organic_options", []):
            organic_options.append({**opt, "category": "Organic", "action": action})
        for opt in detail.get("traditional_remedies", []):
            traditional_remedies.append({**opt, "category": "Traditional", "action": action})

    return {
        "chemical_options": chemical_options,
        "organic_options": organic_options,
        "traditional_remedies": traditional_remedies,
        "cultural_practices": entry.get("cultural_practices", []),
        "pathogen": entry.get("pathogen", ""),
        "pathogen_type": entry.get("pathogen_type", "unknown"),
        "primary_action": primary_action,
        "notes": entry.get("notes", ""),
    }


def get_best_treatment(disease_class: str, chosen_action: str) -> dict:
    """Always returns a meaningful treatment dict, falling back through actions."""
    if not disease_class:
        return {}
    td = get_treatment_detail(disease_class, chosen_action)
    if td:
        td = dict(td); td["action_used"] = chosen_action
        return td
    entry = DISEASE_DB.get(disease_class, {})
    for fallback_action in entry.get("valid_actions", []):
        td = get_treatment_detail(disease_class, fallback_action)
        if td:
            td = dict(td); td["action_used"] = fallback_action
            td["note"] = f"Showing '{fallback_action}' treatment — most relevant for this disease"
            return td
    return {}


def is_crop_in_model(crop_type: str) -> bool:
    """Returns True if the trained 77-class CNN can classify this crop."""
    if not crop_type:
        return False
    key = crop_type.strip().lower()
    key = CROP_NAME_ALIASES.get(key, key)
    MODEL_CROPS = {
        "apple", "banana", "blueberry", "cherry", "citrus", "coffee",
        "corn", "maize", "grape", "groundnut", "mango", "orange",
        "peach", "pepper", "potato", "raspberry", "soybean", "squash",
        "strawberry", "sugarcane", "tea", "tomato",
    }
    return key in MODEL_CROPS


# ══════════════════════════════════════════════════════════════════════════════
# CROP_FALLBACK_DB — used when crop is selected but model cannot identify it
# (e.g. Rice, Wheat, Cotton, Chilli, Brinjal, Onion — not in 77-class model)
# ══════════════════════════════════════════════════════════════════════════════

CROP_FALLBACK_DB = {
    "rice": {
        "common_diseases": ["Blast", "Brown Spot", "Sheath Blight", "Bacterial Leaf Blight"],
        "dominant_pathogen_type": "fungal",
        "valid_actions": ["fungicide", "irrigation", "soil_fix", "monitor"],
        "treatments": {"fungicide": {
            "product": "Tricyclazole (Blast) or Hexaconazole (Sheath Blight)",
            "dosage": "Tricyclazole: 0.6g/L | Hexaconazole: 2ml/L",
            "frequency": "At first sign — repeat every 10-14 days if humid",
            "organic_alt": "Pseudomonas fluorescens bio-agent spray",
        }},
        "cultural_practices": [
            "Use certified disease-free seed and resistant varieties",
            "Maintain spacing for airflow — avoid excess nitrogen",
            "Drain fields periodically to reduce canopy humidity",
        ],
    },
    "wheat": {
        "common_diseases": ["Stem Rust", "Leaf Rust", "Yellow Rust", "Loose Smut", "Powdery Mildew"],
        "dominant_pathogen_type": "fungal",
        "valid_actions": ["fungicide", "soil_fix", "monitor"],
        "treatments": {"fungicide": {
            "product": "Propiconazole (Rust) or Tebuconazole (Smut/Mildew)",
            "dosage": "Propiconazole: 1ml/L | Tebuconazole: 1.5ml/L",
            "frequency": "At tillering-boot stage — 1-2 sprays at 14-day intervals",
            "organic_alt": "Sulfur dust 20-25kg/ha",
        }},
        "cultural_practices": [
            "Use rust-resistant varieties: HD-2967, PBW-343",
            "Sow at recommended time — avoid late sowing",
            "Balanced fertilisation — avoid excess nitrogen",
        ],
    },
    "cotton": {
        "common_diseases": ["Fusarium Wilt", "Alternaria Blight", "Leaf Curl Virus", "Bacterial Blight"],
        "dominant_pathogen_type": "fungal",
        "valid_actions": ["fungicide", "bactericide", "soil_fix", "ph_correction", "monitor"],
        "treatments": {
            "fungicide": {"product": "Carbendazim (Wilt) or Mancozeb (Blight)", "dosage": "Carbendazim: 1g/L | Mancozeb: 2.5g/L", "frequency": "Every 10-14 days", "organic_alt": "Trichoderma viride soil drench"},
            "bactericide": {"product": "Copper Oxychloride (Bacterial Blight)", "dosage": "3g/L", "frequency": "Every 10 days", "organic_alt": "Bordeaux mixture 1%"},
        },
        "cultural_practices": ["Plant certified whitefly-free seeds", "Rogue Leaf Curl-infected plants", "Deep summer ploughing for Fusarium"],
    },
    "sugarcane": {
        "common_diseases": ["Red Rot", "Smut", "Wilt", "Grassy Shoot Disease"],
        "dominant_pathogen_type": "fungal",
        "valid_actions": ["fungicide", "irrigation", "soil_fix", "monitor"],
        "treatments": {"fungicide": {"product": "Carbendazim sett treatment", "dosage": "1g/L", "frequency": "Soak setts before planting", "organic_alt": "Hot water sett treatment 50°C/1hr"}},
        "cultural_practices": ["Disease-free seed setts from certified nurseries", "Hot water treatment of setts", "Maintain drainage"],
    },
    "soybean": {
        "common_diseases": ["Soybean Rust", "Charcoal Rot", "Stem Canker", "Frogeye Leaf Spot"],
        "dominant_pathogen_type": "fungal",
        "valid_actions": ["fungicide", "soil_fix", "monitor"],
        "treatments": {"fungicide": {"product": "Azoxystrobin + Chlorothalonil", "dosage": "2ml/L", "frequency": "At R1 flowering, repeat 14 days", "organic_alt": "Neem-based products"}},
        "cultural_practices": ["Use rust-resistant varieties", "Crop rotation with non-host", "Avoid excessive plant density"],
    },
    "groundnut": {
        "common_diseases": ["Early Leaf Spot", "Late Leaf Spot", "Rust", "Collar Rot"],
        "dominant_pathogen_type": "fungal",
        "valid_actions": ["fungicide", "soil_fix", "monitor"],
        "treatments": {"fungicide": {"product": "Chlorothalonil or Mancozeb", "dosage": "2g/L", "frequency": "Every 10-14 days from 30 DAS", "organic_alt": "Copper fungicide 3g/L"}},
        "cultural_practices": ["Seed treatment before sowing", "No evening irrigation", "Harvest promptly at maturity"],
    },
    "chilli": {
        "common_diseases": ["Anthracnose", "Powdery Mildew", "Bacterial Wilt", "Leaf Curl Virus"],
        "dominant_pathogen_type": "fungal",
        "valid_actions": ["fungicide", "bactericide", "irrigation", "monitor"],
        "treatments": {
            "fungicide": {"product": "Mancozeb (Anthracnose) or Sulphur (Powdery Mildew)", "dosage": "2.5g/L | 3g/L", "frequency": "Every 10 days", "organic_alt": "Neem oil 5ml/L"},
            "bactericide": {"product": "Copper Oxychloride (Bacterial Wilt)", "dosage": "3g/L", "frequency": "At first symptoms", "organic_alt": "Pseudomonas fluorescens drench"},
        },
        "cultural_practices": ["Virus-free transplants", "Control thrips/whiteflies", "Avoid waterlogging"],
    },
    "onion": {
        "common_diseases": ["Purple Blotch", "Stemphylium Blight", "Downy Mildew", "Basal Rot"],
        "dominant_pathogen_type": "fungal",
        "valid_actions": ["fungicide", "irrigation", "monitor"],
        "treatments": {"fungicide": {"product": "Iprodione or Metalaxyl", "dosage": "2ml/L | 2g/L", "frequency": "Every 7-10 days humid weather", "organic_alt": "Bordeaux mixture 1%"}},
        "cultural_practices": ["Certified disease-free sets", "Drip irrigation only", "Rotate with non-allium crops"],
    },
    "brinjal": {
        "common_diseases": ["Little Leaf", "Phomopsis Blight", "Bacterial Wilt", "Fruit Borer"],
        "dominant_pathogen_type": "fungal",
        "valid_actions": ["fungicide", "bactericide", "monitor"],
        "treatments": {
            "fungicide": {"product": "Copper Oxychloride or Mancozeb", "dosage": "3g/L", "frequency": "At first symptom", "organic_alt": "Neem cake soil incorporation"},
            "bactericide": {"product": "Copper Hydroxide (Bacterial Wilt)", "dosage": "3g/L", "frequency": "At wilt sign", "organic_alt": "Trichoderma harzianum drench"},
        },
        "cultural_practices": ["Uproot Little Leaf-infected plants", "Remove Bacterial Wilt plants with soil", "Avoid replanting in infected soil"],
    },
    "maize": {
        "common_diseases": ["Turcicum Blight", "Common Rust", "Gray Leaf Spot", "Maize Streak Virus"],
        "dominant_pathogen_type": "fungal",
        "valid_actions": ["fungicide", "soil_fix", "monitor"],
        "treatments": {"fungicide": {"product": "Azoxystrobin or Propiconazole", "dosage": "1ml/L", "frequency": "At first lesion, repeat 14 days", "organic_alt": "Crop rotation"}},
        "cultural_practices": ["Hybrid blight-resistant varieties", "Crop rotation", "Destroy infected residue"],
    },
}

UNKNOWN_CROP_FALLBACK = {
    "common_diseases": ["Fungal blight", "Bacterial spot", "Rust", "Powdery mildew"],
    "dominant_pathogen_type": "unknown",
    "valid_actions": ["fungicide", "bactericide", "soil_fix", "irrigation", "monitor"],
    "treatments": {
        "fungicide": {"product": "Mancozeb 75WP or Copper Oxychloride 50WP", "dosage": "Mancozeb: 2g/L | Copper: 3g/L", "frequency": "Every 7-10 days", "organic_alt": "Bordeaux mixture 1%"},
        "bactericide": {"product": "Copper Hydroxide 77WP", "dosage": "3g/L", "frequency": "Every 7-10 days", "organic_alt": "Bordeaux mixture 1%"},
    },
    "cultural_practices": [
        "Select your crop type on the Scan page for disease-specific recommendations",
        "Remove and destroy infected leaves immediately",
        "Improve air circulation by pruning",
        "Avoid overhead irrigation",
    ],
}


def get_crop_fallback(crop_type: str) -> dict:
    """Returns crop-level fallback knowledge when specific disease class is unknown."""
    if not crop_type:
        return UNKNOWN_CROP_FALLBACK
    key = crop_type.strip().lower()
    key = CROP_NAME_ALIASES.get(key, key)
    return CROP_FALLBACK_DB.get(key, UNKNOWN_CROP_FALLBACK)


def get_crop_valid_actions(crop_type: str) -> list:
    fallback = get_crop_fallback(crop_type)
    actions = fallback.get("valid_actions", ALL_ACTIONS)
    if "monitor" not in actions:
        actions = actions + ["monitor"]
    return actions


def get_crop_treatment(crop_type: str, action: str) -> dict:
    fallback = get_crop_fallback(crop_type)
    return fallback.get("treatments", {}).get(action, {})


def get_crop_cultural_practices(crop_type: str) -> list:
    return get_crop_fallback(crop_type).get("cultural_practices", [])

def ensure_configs_exist(base_dir: str = None) -> None:
    import json, os
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    configs = {
        "actions_config.json": {
            action: {"type": ACTION_TYPE.get(action, "Chemical"),
                     "cost_inr": ACTION_COST_INR.get(action, 200),
                     "display_name": TREATMENT_DISPLAY_NAME.get(action, action)}
            for action in ALL_ACTIONS
        },
        "crop_diseases.json": {
            k: v.get("valid_actions", ["monitor"])
            for k, v in DISEASE_DB.items()
        },
        "disease_weather.json": {
            k: v.get("weather_class", "fungal_blight")
            for k, v in DISEASE_DB.items()
        },
    }
    for filename, data in configs.items():
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(data, f, indent=2)