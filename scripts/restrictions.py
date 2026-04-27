import pandas as pd
import ast
import re
import os

# ==========================================
# 1. DEFINE ALL KEYWORDS AND COMPILE REGEX (Done once for speed)
# ==========================================

# Vegetarian/Vegan
non_veg_keywords = ['meat', 'chicken', 'beef', 'pork', 'fish', 'shrimp', 'bacon', 'steak', 'tuna', 'salmon', 'lamb',
                    'turkey', 'sausage', 'ham', 'prosciutto', 'veal', 'anchovy', 'scallop', 'crab', 'lobster', 'oyster',
                    'clam', 'squid', 'octopus', 'poultry', 'duck', 'goose', 'venison', 'gelatin', 'lard', 'broth',
                    'bouillon', 'stock']
non_vegan_keywords = non_veg_keywords + ['milk', 'cheese', 'butter', 'yogurt', 'cream', 'whey', 'egg', 'eggs', 'honey',
                                         'mayo', 'mayonnaise', 'ghee', 'casein', 'buttermilk', 'parmesan', 'mozzarella',
                                         'cheddar', 'ricotta', 'brie', 'feta', 'paneer']

# Allergens
allergen_keywords = {
    'Dairy': ['milk', 'cheese', 'butter', 'yogurt', 'cream', 'whey', 'casein', 'ghee', 'buttermilk', 'parmesan',
              'mozzarella', 'cheddar', 'ricotta'],
    'Eggs': ['egg', 'eggs', 'mayo', 'mayonnaise'],
    'Peanuts': ['peanut', 'peanuts'],
    'Tree Nuts': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'macadamia', 'hazelnut', 'pine nut'],
    'Soy': ['soy', 'soybean', 'tofu', 'tempeh', 'edamame', 'miso', 'tamari'],
    'Wheat/Gluten': ['wheat', 'flour', 'bread', 'pasta', 'gluten', 'barley', 'rye', 'seitan', 'bulgur', 'couscous',
                     'panko', 'soy sauce', 'malt', 'farro', 'spelt'],
    'Fish': ['fish', 'salmon', 'tuna', 'cod', 'tilapia', 'halibut', 'trout', 'anchovy', 'sardine'],
    'Shellfish': ['shrimp', 'crab', 'lobster', 'oyster', 'clam', 'scallop', 'mussel', 'prawn'],
    'Sesame': ['sesame', 'tahini']
}

# Diet (Keto/Paleo)
keto_avoid = ['sugar', 'honey', 'maple syrup', 'agave', 'molasses', 'wheat', 'flour', 'bread', 'pasta', 'rice', 'oat',
              'corn', 'quinoa', 'barley', 'rye', 'potato', 'yam', 'sweet potato', 'bean', 'lentil', 'chickpea', 'pea',
              'apple', 'banana', 'orange', 'grape', 'mango', 'pineapple']
paleo_avoid = ['wheat', 'flour', 'bread', 'pasta', 'rice', 'oat', 'corn', 'quinoa', 'barley', 'rye', 'bean', 'lentil',
               'chickpea', 'peanut', 'soy', 'edamame', 'tofu', 'milk', 'cheese', 'butter', 'yogurt', 'cream', 'whey',
               'sugar', 'corn syrup', 'artificial sweetener', 'canola oil', 'vegetable oil', 'soybean oil',
               'peanut oil', 'margarine']

# Religious Groups
pork_keywords = ['pork', 'bacon', 'ham', 'prosciutto', 'lard', 'gelatin', 'pancetta', 'chorizo', 'pepperoni']
alc_keywords = ['wine', 'beer', 'vodka', 'rum', 'whiskey', 'tequila', 'bourbon', 'champagne', 'liquor', 'liqueur',
                'brandy', 'cognac', 'sake', 'mirin', 'ale', 'kahlua', 'amaretto', 'sherry', 'vermouth']
meat_keywords = ['chicken', 'beef', 'lamb', 'turkey', 'duck', 'goose', 'poultry', 'veal', 'venison', 'mutton',
                 'steak'] + pork_keywords
beef_keywords = ['beef', 'steak', 'veal']

# Compile all regex patterns efficiently
veg_pattern = re.compile(r'\b(' + '|'.join(non_veg_keywords) + r')\b')
vegan_pattern = re.compile(r'\b(' + '|'.join(non_vegan_keywords) + r')\b')
allergen_patterns = {k: re.compile(r'\b(' + '|'.join(v) + r')\b') for k, v in allergen_keywords.items()}
keto_pattern = re.compile(r'\b(' + '|'.join(keto_avoid) + r')\b')
paleo_pattern = re.compile(r'\b(' + '|'.join(paleo_avoid) + r')\b')
pork_pattern = re.compile(r'\b(' + '|'.join(pork_keywords) + r')\b')
alc_pattern = re.compile(r'\b(' + '|'.join(alc_keywords) + r')\b')
meat_pattern = re.compile(r'\b(' + '|'.join(meat_keywords) + r')\b')
beef_pattern = re.compile(r'\b(' + '|'.join(beef_keywords) + r')\b')
shellfish_pattern = allergen_patterns['Shellfish']  # Reuse from allergens
dairy_pattern = allergen_patterns['Dairy']  # Reuse from allergens


# ==========================================
# 2. MASTER PROCESSING FUNCTION
# ==========================================
def master_recipe_parser(ingredients_str):
    """Parses ingredients once and applies ALL dietary logics."""
    try:
        if pd.isna(ingredients_str):
            ingredients = []
        elif isinstance(ingredients_str, str) and ingredients_str.startswith('['):
            ingredients = ast.literal_eval(ingredients_str)
        else:
            ingredients = [str(ingredients_str)]
    except:
        ingredients = [str(ingredients_str)]

    ingredients_text = ' '.join([str(i) for i in ingredients]).lower()

    # 1. Veg/Vegan
    is_vegetarian = not bool(veg_pattern.search(ingredients_text))
    is_vegan = is_vegetarian and not bool(vegan_pattern.search(ingredients_text))

    # 2. Allergens & GF/DF
    detected_allergens = [alg for alg, pat in allergen_patterns.items() if pat.search(ingredients_text)]
    allergens_present = ', '.join(detected_allergens) if detected_allergens else 'None'
    is_dairy_free = 'Dairy' not in detected_allergens
    is_gluten_free = 'Wheat/Gluten' not in detected_allergens

    # 3. Keto/Paleo
    is_keto = not bool(keto_pattern.search(ingredients_text))
    is_paleo = not bool(paleo_pattern.search(ingredients_text))

    # 4. Religious
    has_pork = bool(pork_pattern.search(ingredients_text))
    has_alc = bool(alc_pattern.search(ingredients_text))
    has_meat = bool(meat_pattern.search(ingredients_text))
    has_dairy = not is_dairy_free
    has_shellfish = 'Shellfish' in detected_allergens
    has_beef = bool(beef_pattern.search(ingredients_text))

    is_halal = not has_pork and not has_alc
    is_kosher = not has_pork and not has_shellfish and not (has_meat and has_dairy)
    is_hindu_friendly = not has_beef

    return pd.Series({
        'is_vegetarian': is_vegetarian,
        'is_vegan': is_vegan,
        'allergens_present': allergens_present,
        'is_dairy_free': is_dairy_free,
        'is_gluten_free': is_gluten_free,
        'is_keto': is_keto,
        'is_paleo': is_paleo,
        'is_halal': is_halal,
        'is_kosher': is_kosher,
        'is_hindu_friendly': is_hindu_friendly
    })


# ==========================================
# 3. CHUNK PROCESSING ENGINE
# ==========================================
input_file = 'classified_large_recipes_objects.csv'
output_file = 'full_recipes_with_restrictions.csv'
chunk_size = 10000  # Process 10,000 rows at a time (adjust based on your RAM)

# Remove the output file if it already exists to start fresh
if os.path.exists(output_file):
    os.remove(output_file)

print(f"Starting to process {input_file} in chunks of {chunk_size}...")

# Read the file in chunks
chunk_iterator = pd.read_csv(input_file, chunksize=chunk_size)

for i, chunk in enumerate(chunk_iterator):
    print(f"Processing chunk {i + 1}...")

    # Determine the column to parse
    col_to_parse = 'NER' if 'NER' in chunk.columns else 'ingredients_parsed'

    # Apply the master function to the chunk
    # This creates a new dataframe containing only the generated boolean columns
    new_columns = chunk[col_to_parse].apply(master_recipe_parser)

    # Merge the new columns back into the original chunk
    processed_chunk = pd.concat([chunk, new_columns], axis=1)

    # Save the chunk to the output file
    # If it's the first chunk (i==0), write the header. Otherwise, skip the header and append.
    mode = 'w' if i == 0 else 'a'
    write_header = True if i == 0 else False

    processed_chunk.to_csv(output_file, mode=mode, header=write_header, index=False)

print("Processing complete! Check your new file.")