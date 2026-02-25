# spice_data.py
# ─────────────────────────────────────────────────────────────────────────────
# Central data store for Spicerack.
# Contains: spice vocabulary, aliases, flavor profiles, and culinary regions.
# Import in your notebook with:
#   from spice_data import SPICES, ALIASES, CANONICAL_SPICES, FLAVOR_PROFILES, REGION_PROFILES
# ─────────────────────────────────────────────────────────────────────────────


# ── Full Spice Vocabulary ─────────────────────────────────────────────────────
# Users can only select from this list (enforced by validate_spices())

SPICES = [

    # ── Salt & Pepper ──────────────────────────────────────────────────────────
    "salt",
    "sea salt",
    "kosher salt",
    "fleur de sel",
    "himalayan pink salt",
    "black salt",
    "smoked salt",
    "black pepper",
    "white pepper",
    "pink peppercorn",
    "green peppercorn",
    "sichuan pepper",
    "long pepper",
    "grains of paradise",

    # ── Alliums ────────────────────────────────────────────────────────────────
    "garlic",
    "garlic powder",
    "garlic flakes",
    "roasted garlic powder",
    "onion powder",
    "onion flakes",
    "dried onion",
    "shallot powder",
    "chive",
    "dried chive",
    "leek powder",

    # ── Chiles & Heat ──────────────────────────────────────────────────────────
    "chili powder",
    "cayenne",
    "crushed red pepper",
    "chipotle powder",
    "ancho chili powder",
    "guajillo powder",
    "pasilla powder",
    "mulato chili powder",
    "habanero powder",
    "ghost pepper powder",
    "aleppo pepper",
    "urfa biber",
    "gochugaru",
    "paprika",
    "smoked paprika",
    "sweet paprika",
    "hot paprika",
    "piment d'espelette",
    "tajin",

    # ── Warm / Baking Spices ───────────────────────────────────────────────────
    "cinnamon",
    "cassia cinnamon",
    "ceylon cinnamon",
    "nutmeg",
    "mace",
    "cloves",
    "allspice",
    "cardamom",
    "black cardamom",
    "ginger",
    "ground ginger",
    "dried ginger",
    "galangal",
    "star anise",
    "anise",
    "anise seed",
    "vanilla",
    "vanilla powder",

    # ── Earthy & Smoky ─────────────────────────────────────────────────────────
    "cumin",
    "caraway",
    "nigella seed",
    "black cumin",
    "turmeric",
    "smoked turmeric",
    "fenugreek",
    "fenugreek seed",
    "asafoetida",
    "hing",
    "annatto",
    "achiote",
    "sumac",
    "amchur",
    "dried mango powder",
    "tamarind powder",
    "kokum powder",

    # ── Mediterranean Herbs ────────────────────────────────────────────────────
    "oregano",
    "greek oregano",
    "mexican oregano",
    "basil",
    "dried basil",
    "thyme",
    "lemon thyme",
    "rosemary",
    "sage",
    "marjoram",
    "bay leaf",
    "bay leaves",
    "savory",
    "summer savory",
    "winter savory",
    "lavender",
    "herbes de provence",
    "italian seasoning",

    # ── Fresh-Dry Herbs ────────────────────────────────────────────────────────
    "parsley",
    "dried parsley",
    "dill",
    "dried dill",
    "dill seed",
    "tarragon",
    "dried tarragon",
    "chervil",
    "dried chervil",
    "celery seed",
    "celery salt",
    "dried cilantro",
    "coriander",
    "coriander seed",

    # ── Mustard & Seed Spices ──────────────────────────────────────────────────
    "mustard",
    "mustard powder",
    "mustard seed",
    "yellow mustard seed",
    "brown mustard seed",
    "black mustard seed",
    "fennel",
    "fennel seed",
    "fennel pollen",
    "poppy seed",
    "sesame seed",
    "black sesame seed",
    "hemp seed",
    "flax seed",

    # ── Blends & Masalas ───────────────────────────────────────────────────────
    "curry powder",
    "madras curry powder",
    "garam masala",
    "chaat masala",
    "panch phoron",
    "ras el hanout",
    "baharat",
    "berbere",
    "harissa powder",
    "za'atar",
    "dukkah",
    "chinese five spice",
    "seven spice",
    "shichimi togarashi",
    "furikake",
    "old bay",
    "cajun seasoning",
    "creole seasoning",
    "jerk seasoning",
    "taco seasoning",
    "poultry seasoning",
    "pumpkin pie spice",
    "apple pie spice",
    "pickling spice",
    "bouquet garni",
    "mixed spice",

    # ── Floral & Exotic ────────────────────────────────────────────────────────
    "saffron",
    "dried rose petals",
    "rose water powder",
    "dried lavender",
    "dried hibiscus",
    "dried chamomile",
    "marigold petal",
    "dried orange peel",
    "dried lemon peel",
    "dried lime peel",
    "kaffir lime leaf",
    "lemongrass powder",
    "makrut lime powder",

    # ── Umami & Savory ─────────────────────────────────────────────────────────
    "msg",
    "nutritional yeast",
    "dried mushroom powder",
    "porcini powder",
    "shiitake powder",
    "truffle salt",
    "miso powder",
    "bonito powder",
    "kombu powder",
    "dried tomato powder",
    "dried bell pepper",

    # ── Acidic & Bright ────────────────────────────────────────────────────────
    "citric acid",
    "cream of tartar",
    "dried lime powder",
    "loomi",
    "black lime",
    "dried pomegranate seed",
    "pomegranate powder",
    "barberry",

    # ── Wood & Smoke ───────────────────────────────────────────────────────────
    "liquid smoke powder",
    "smoked sea salt",
    "hickory smoked salt",
    "applewood smoked salt",

]


# ── Aliases ───────────────────────────────────────────────────────────────────
# Maps variant spellings / common names → canonical spice name in SPICES list

ALIASES = {
    # Pepper variants
    "pepper":                   "black pepper",
    "ground pepper":            "black pepper",
    "cracked pepper":           "black pepper",
    "white peppercorn":         "white pepper",
    "szechuan pepper":          "sichuan pepper",
    "szechwan pepper":          "sichuan pepper",
    "sichuan peppercorn":       "sichuan pepper",

    # Salt variants
    "table salt":               "salt",
    "iodized salt":             "salt",
    "rock salt":                "salt",
    "pink salt":                "himalayan pink salt",
    "himalayan salt":           "himalayan pink salt",
    "kala namak":               "black salt",

    # Garlic / onion
    "garlic powder":            "garlic",
    "garlic salt":              "garlic",
    "granulated garlic":        "garlic",
    "garlic granules":          "garlic",
    "roasted garlic":           "roasted garlic powder",
    "onion salt":               "onion powder",
    "granulated onion":         "onion powder",
    "dried shallot":            "shallot powder",

    # Chiles
    "red pepper flakes":        "crushed red pepper",
    "red chili flakes":         "crushed red pepper",
    "chile flakes":             "crushed red pepper",
    "cayenne pepper":           "cayenne",
    "ground cayenne":           "cayenne",
    "chipotle":                 "chipotle powder",
    "ancho":                    "ancho chili powder",
    "guajillo":                 "guajillo powder",
    "aleppo":                   "aleppo pepper",
    "korean chili flakes":      "gochugaru",
    "korean red pepper":        "gochugaru",
    "smoked paprika":           "paprika",
    "sweet smoked paprika":     "paprika",
    "hot smoked paprika":       "hot paprika",
    "spanish paprika":          "paprika",
    "hungarian paprika":        "paprika",

    # Warm spices
    "ground cinnamon":          "cinnamon",
    "cinnamon stick":           "cinnamon",
    "ground nutmeg":            "nutmeg",
    "whole nutmeg":             "nutmeg",
    "ground cloves":            "cloves",
    "whole cloves":             "cloves",
    "ground allspice":          "allspice",
    "allspice berries":         "allspice",
    "ground cardamom":          "cardamom",
    "cardamom pods":            "cardamom",
    "green cardamom":           "cardamom",
    "ground ginger":            "ginger",
    "dried ginger":             "ginger",
    "fresh ginger powder":      "ginger",
    "ground galangal":          "galangal",
    "star anise pod":           "star anise",
    "ground star anise":        "star anise",
    "aniseed":                  "anise seed",
    "anise powder":             "anise",
    "vanilla bean powder":      "vanilla powder",
    "vanilla extract powder":   "vanilla powder",

    # Earthy / smoky
    "ground cumin":             "cumin",
    "cumin seed":               "cumin",
    "ground caraway":           "caraway",
    "caraway seed":             "caraway",
    "black seed":               "nigella seed",
    "kalonji":                  "nigella seed",
    "onion seed":               "nigella seed",
    "ground turmeric":          "turmeric",
    "turmeric root powder":     "turmeric",
    "ground fenugreek":         "fenugreek",
    "methi":                    "fenugreek",
    "methi powder":             "fenugreek",
    "asafetida":                "asafoetida",
    "hing powder":              "hing",
    "ground annatto":           "annatto",
    "achiote powder":           "achiote",
    "dried mango powder":       "amchur",
    "mango powder":             "amchur",
    "ground sumac":             "sumac",
    "ground tamarind":          "tamarind powder",

    # Mediterranean herbs
    "dried oregano":            "oregano",
    "wild oregano":             "greek oregano",
    "dried basil":              "basil",
    "dried thyme":              "thyme",
    "dried rosemary":           "rosemary",
    "dried sage":               "sage",
    "dried marjoram":           "marjoram",
    "bay leaves":               "bay leaf",
    "laurel leaf":              "bay leaf",
    "dried savory":             "savory",
    "herbs de provence":        "herbes de provence",

    # Fresh / dry herbs
    "flat leaf parsley":        "parsley",
    "curly parsley":            "parsley",
    "dried parsley flakes":     "parsley",
    "dill weed":                "dill",
    "dried dill weed":          "dill",
    "dried tarragon":           "tarragon",
    "celery powder":            "celery seed",
    "ground coriander":         "coriander",
    "coriander powder":         "coriander",
    "dhania":                   "coriander",

    # Mustard / seeds
    "dry mustard":              "mustard powder",
    "english mustard powder":   "mustard powder",
    "ground mustard":           "mustard powder",
    "mustard seed powder":      "mustard powder",
    "ground fennel":            "fennel",
    "fennel powder":            "fennel",
    "ground fennel seed":       "fennel seed",
    "white sesame":             "sesame seed",
    "toasted sesame":           "sesame seed",

    # Blends
    "curry":                    "curry powder",
    "indian curry powder":      "curry powder",
    "garam":                    "garam masala",
    "ras-el-hanout":            "ras el hanout",
    "five spice":               "chinese five spice",
    "chinese five-spice":       "chinese five spice",
    "7 spice":                  "seven spice",
    "mixed herbs":              "italian seasoning",
    "pumpkin spice":            "pumpkin pie spice",

    # Floral / exotic
    "saffron threads":          "saffron",
    "rose petals":              "dried rose petals",
    "orange peel":              "dried orange peel",
    "lemon peel":               "dried lemon peel",
    "lime leaf":                "kaffir lime leaf",
    "makrut lime leaf":         "kaffir lime leaf",
    "lemongrass":               "lemongrass powder",

    # Umami
    "mushroom powder":          "dried mushroom powder",
    "porcini":                  "porcini powder",
    "shiitake":                 "shiitake powder",
    "tomato powder":            "dried tomato powder",

    # Acid / bright
    "black dried lime":         "black lime",
    "dried lime":               "loomi",
    "omani lime":               "loomi",
    "persian lime powder":      "dried lime powder",
    "pomegranate molasses powder": "pomegranate powder",
    "zereshk":                  "barberry",
}


# ── Canonical Spice Set ───────────────────────────────────────────────────────
# All unique canonical names after alias resolution

CANONICAL_SPICES = sorted(set(ALIASES.get(s, s) for s in SPICES))


# ── Flavor Profiles ───────────────────────────────────────────────────────────
# Each profile groups spices by shared flavor character.
# Coverage score = how many of these spices the user has / total in profile.

FLAVOR_PROFILES = {

    "Smoky & Savory": {
        "paprika", "smoked paprika", "chipotle powder", "ancho chili powder",
        "smoked salt", "smoked sea salt", "hickory smoked salt", "applewood smoked salt",
        "cumin", "garlic", "black pepper", "onion powder",
        "liquid smoke powder", "porcini powder", "dried mushroom powder",
    },

    "Bold & Spicy": {
        "cayenne", "crushed red pepper", "chili powder", "habanero powder",
        "ghost pepper powder", "gochugaru", "aleppo pepper", "urfa biber",
        "chipotle powder", "ancho chili powder", "guajillo powder", "pasilla powder",
        "hot paprika", "sichuan pepper", "long pepper", "grains of paradise",
        "harissa powder", "piment d'espelette",
    },

    "Warm & Sweet": {
        "cinnamon", "cassia cinnamon", "ceylon cinnamon",
        "nutmeg", "mace", "cloves", "allspice",
        "cardamom", "ginger", "star anise", "anise", "anise seed",
        "vanilla", "vanilla powder", "black cardamom",
        "pumpkin pie spice", "apple pie spice", "mixed spice",
    },

    "Herby & Mediterranean": {
        "oregano", "greek oregano", "basil", "thyme", "lemon thyme",
        "rosemary", "sage", "marjoram", "bay leaf", "savory",
        "summer savory", "winter savory", "lavender", "dried lavender",
        "herbes de provence", "italian seasoning", "bouquet garni",
        "tarragon", "chervil", "parsley", "dried parsley",
    },

    "Fresh & Grassy": {
        "dill", "dill seed", "tarragon", "chervil", "parsley",
        "dried cilantro", "coriander", "celery seed", "celery salt",
        "dried chive", "chive", "lemongrass powder", "kaffir lime leaf",
        "fennel", "fennel seed", "fennel pollen",
    },

    "Bright & Tangy": {
        "sumac", "amchur", "dried mango powder", "tamarind powder",
        "loomi", "black lime", "dried lime powder", "citric acid",
        "pomegranate powder", "barberry", "kokum powder",
        "dried orange peel", "dried lemon peel", "dried lime peel",
    },

    "South Asian & Aromatic": {
        "curry powder", "madras curry powder", "garam masala", "chaat masala",
        "panch phoron", "turmeric", "coriander", "cumin", "ginger",
        "cardamom", "black cardamom", "fenugreek", "fenugreek seed",
        "asafoetida", "hing", "mustard seed", "black mustard seed",
        "nigella seed", "black cumin", "amchur", "tamarind powder",
    },

    "Middle Eastern & North African": {
        "ras el hanout", "baharat", "seven spice", "za'atar", "dukkah",
        "sumac", "cumin", "coriander", "cinnamon", "allspice",
        "cardamom", "turmeric", "saffron", "aleppo pepper", "urfa biber",
        "dried rose petals", "loomi", "black lime", "barberry",
        "berbere", "fenugreek",
    },

    "East Asian & Pacific": {
        "chinese five spice", "shichimi togarashi", "furikake",
        "sichuan pepper", "star anise", "ginger", "galangal",
        "black sesame seed", "sesame seed", "gochugaru",
        "lemongrass powder", "kaffir lime leaf", "makrut lime powder",
        "bonito powder", "kombu powder", "miso powder",
        "dried mushroom powder", "shiitake powder",
    },

    "Caribbean & Latin": {
        "jerk seasoning", "allspice", "scotch bonnet powder",
        "cumin", "oregano", "mexican oregano", "achiote", "annatto",
        "coriander", "garlic", "onion powder", "thyme",
        "habanero powder", "guajillo powder", "ancho chili powder",
        "chipotle powder", "tajin", "chaat masala",
    },

    "American BBQ & Southern": {
        "smoked paprika", "chipotle powder", "chili powder", "cayenne",
        "garlic", "onion powder", "black pepper", "cumin",
        "mustard powder", "celery seed", "old bay", "cajun seasoning",
        "creole seasoning", "hickory smoked salt", "applewood smoked salt",
    },

    "French & European": {
        "herbes de provence", "tarragon", "thyme", "rosemary", "marjoram",
        "bay leaf", "parsley", "chervil", "lavender", "dried lavender",
        "savory", "bouquet garni", "celery seed", "white pepper",
        "piment d'espelette", "fleur de sel",
    },

    "Floral & Perfumed": {
        "saffron", "dried rose petals", "dried lavender", "dried hibiscus",
        "dried chamomile", "marigold petal", "cardamom", "vanilla",
        "vanilla powder", "rose water powder",
    },

    "Umami & Savory Depth": {
        "msg", "nutritional yeast", "dried mushroom powder", "porcini powder",
        "shiitake powder", "truffle salt", "miso powder", "bonito powder",
        "kombu powder", "dried tomato powder", "dried bell pepper",
        "smoked salt", "smoked sea salt",
    },

    "Seed & Nutty": {
        "sesame seed", "black sesame seed", "poppy seed", "fennel seed",
        "mustard seed", "yellow mustard seed", "brown mustard seed",
        "black mustard seed", "caraway", "nigella seed", "hemp seed",
        "flax seed", "coriander seed", "dill seed", "celery seed",
        "dukkah", "furikake",
    },

}


# ── Culinary Regions ──────────────────────────────────────────────────────────
# Maps each region to the flavor profiles most associated with it.
# Used to tag recipes and group recommendations by cuisine.

REGION_PROFILES = {

    "Mexican / Tex-Mex": [
        "Bold & Spicy",
        "Smoky & Savory",
        "Caribbean & Latin",
    ],

    "Italian / Mediterranean": [
        "Herby & Mediterranean",
        "Bright & Tangy",
        "Fresh & Grassy",
    ],

    "Middle Eastern": [
        "Middle Eastern & North African",
        "Warm & Sweet",
        "Bright & Tangy",
        "Floral & Perfumed",
    ],

    "North African": [
        "Middle Eastern & North African",
        "Bold & Spicy",
        "Warm & Sweet",
        "Bright & Tangy",
    ],

    "South Asian / Indian": [
        "South Asian & Aromatic",
        "Bold & Spicy",
        "Bright & Tangy",
        "Warm & Sweet",
    ],

    "East Asian": [
        "East Asian & Pacific",
        "Umami & Savory Depth",
        "Seed & Nutty",
    ],

    "Southeast Asian": [
        "East Asian & Pacific",
        "Bold & Spicy",
        "Fresh & Grassy",
        "Bright & Tangy",
    ],

    "Caribbean": [
        "Caribbean & Latin",
        "Bold & Spicy",
        "Warm & Sweet",
    ],

    "American BBQ / Southern": [
        "American BBQ & Southern",
        "Smoky & Savory",
        "Bold & Spicy",
    ],

    "French / European": [
        "French & European",
        "Herby & Mediterranean",
        "Umami & Savory Depth",
    ],

    "Greek": [
        "Herby & Mediterranean",
        "Bright & Tangy",
        "Middle Eastern & North African",
    ],

    "Ethiopian / East African": [
        "Middle Eastern & North African",
        "Bold & Spicy",
        "Warm & Sweet",
    ],

    "Japanese": [
        "East Asian & Pacific",
        "Umami & Savory Depth",
        "Seed & Nutty",
        "Fresh & Grassy",
    ],

    "Korean": [
        "East Asian & Pacific",
        "Bold & Spicy",
        "Umami & Savory Depth",
    ],

    "Baking & Desserts": [
        "Warm & Sweet",
        "Floral & Perfumed",
        "Seed & Nutty",
    ],

    "Pickling & Preserving": [
        "Seed & Nutty",
        "Bright & Tangy",
        "Fresh & Grassy",
    ],

}


# ── Summary ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Total spices in vocabulary : {len(SPICES)}")
    print(f"Total aliases              : {len(ALIASES)}")
    print(f"Total canonical spices     : {len(CANONICAL_SPICES)}")
    print(f"Total flavor profiles      : {len(FLAVOR_PROFILES)}")
    print(f"Total culinary regions     : {len(REGION_PROFILES)}")
    print()
    print("Flavor Profiles:")
    for name, spices in FLAVOR_PROFILES.items():
        print(f"  {name:35s} ({len(spices)} spices)")
    print()
    print("Culinary Regions:")
    for region, profiles in REGION_PROFILES.items():
        print(f"  {region:35s} → {profiles}")
