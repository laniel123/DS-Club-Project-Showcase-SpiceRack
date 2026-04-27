"""
recommender.py
Built for model keys:
kmeans, svd, mlb, tfidf, idf_boost, recipe_matrix,
recipe_titles, recipe_spices, cluster_labels, cluster_top_spices,
n_clusters, n_recipes, silhouette
"""

import os
import ast
import joblib
import numpy as np
import pandas as pd
from collections import Counter
from sklearn.preprocessing import normalize

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "spicerack_model.joblib")

#CSV_PATH = "/Users/daniellarson/Desktop/SpiceRack/cluster_data.csv"
CSV_PATH = os.path.join(BASE, "data", "full_recipes_with_restrictions.csv")

_model     = None
_recipe_df = None
TOP_CLUSTERS = 5   # search top N nearest clusters per query


_DESSERT_KEYWORDS = {
    "cake", "cookie", "cookies", "pie", "tart", "brownie", "brownies",
    "pudding", "custard", "mousse", "cheesecake", "cupcake", "cupcakes",
    "muffin", "muffins", "donut", "donuts", "doughnut", "fudge", "candy",
    "truffle", "truffles", "macaroon", "macarons", "eclair", "cream puff",
    "ice cream", "sorbet", "gelato", "parfait", "cobbler", "crisp",
    "shortbread", "biscotti", "tiramisu", "baklava", "crepe", "crepes",
    "waffle", "waffles", "pancake", "pancakes", "sweet roll", "cinnamon roll",
    "dessert", "sweet", "sweets", "chocolate", "candy bar", "lollipop",
    "meringue", "praline", "caramel", "butterscotch", "toffee", "nougat",
    "brittle", "bark", "fudge", "popsicle", "smoothie bowl", "fruit salad",
}

_MAINS_KEYWORDS = {
    "chicken", "beef", "pork", "lamb", "turkey", "salmon", "tuna", "shrimp",
    "pasta", "spaghetti", "lasagna", "fettuccine", "penne", "rigatoni",
    "rice", "risotto", "pilaf", "fried rice", "stir fry", "stir-fry",
    "soup", "stew", "chili", "chilli", "curry", "casserole", "roast",
    "burger", "sandwich", "wrap", "taco", "burrito", "enchilada", "quesadilla",
    "pizza", "quiche", "frittata", "omelette", "omelet", "steak", "meatball",
    "meatloaf", "pot pie", "pot roast", "brisket", "ribs", "wings",
    "salad", "grain bowl", "bowl", "bake", "baked", "grilled", "roasted",
    "braised", "sauteed", "sautéed", "pan-fried", "deep-fried", "poached",
    "side dish", "stuffing", "dressing", "mashed", "potatoes", "coleslaw",
    "noodle", "noodles", "ramen", "udon", "soba", "pho", "gumbo", "jambalaya",
    "paella", "biryani", "tagine", "moussaka", "shakshuka", "fajita",
    "fish", "seafood", "crab", "lobster", "scallop", "clam", "mussel",
}


def _classify_course(title) -> str:
    if not isinstance(title, str):
        return "Other/Miscellaneous"
    t = title.lower()
    words = set(t.replace("-", " ").split())
    # Check two-word phrases too
    for kw in _DESSERT_KEYWORDS:
        if kw in t:
            return "Dessert & Sweets"
    for kw in _MAINS_KEYWORDS:
        if kw in t or kw in words:
            return "Mains & Sides"
    return "Other/Miscellaneous"


def load():
    global _model, _recipe_df
    if _model is None and os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
        print(f"[recommender] loaded — {_model['n_recipes']:,} recipes, "
              f"{_model['n_clusters']} clusters, "
              f"silhouette {_model.get('silhouette','?')}")
    if _recipe_df is None and os.path.exists(CSV_PATH):
        _recipe_df = pd.read_csv(CSV_PATH)
        print(f"[recommender] recipe data — {len(_recipe_df):,} rows")
        if _recipe_df["course_category"].isna().all():
            print("[recommender] classifying course categories from titles…")
            _recipe_df["course_category"] = _recipe_df["title"].apply(_classify_course)
            print("[recommender] course classification done")
    return _model


def _user_vector(pantry: list, model) -> np.ndarray:
    """pantry → binary → idf_boost (manual) → svd → normalize"""
    
    # 1. Create the binary array
    user_bin = np.asarray(model["mlb"].transform([set(pantry)]))
    
    # 2. BYPASS the broken tfidf object!
    # Multiply the binary array by the raw idf_boost weights directly
    user_boosted = user_bin * model["idf_boost"]
    
    # 3. Normalize the weighted array
    user_boosted = normalize(user_boosted, norm="l2")
    
    # 4. Compress with SVD
    u    = model["svd"].transform(user_boosted)[0]
    norm = np.linalg.norm(u)
    
    return u / norm if norm > 0 else u


def _nearest_clusters(pantry: list, model) -> list:
    """Return top N nearest cluster IDs. Search more clusters for small pantries."""
    user_bin  = np.asarray(model["mlb"].transform([set(pantry)]))
    distances = model["kmeans"].transform(user_bin)[0]

    n = TOP_CLUSTERS
    if len(pantry) <= 2:
        n = min(n + 4, model["n_clusters"])
    elif len(pantry) <= 4:
        n = min(n + 2, model["n_clusters"])

    return np.argsort(distances)[:n].tolist()


def recommend(user_spices: list, filters=None, courses=None, top_n=20) -> list:
    """Recommend recipes using ML model scoring with dietary/course filters."""
    model = load()
    if model is None or not user_spices:
        return []

    pantry_set = set(user_spices)

    # Build set of allowed titles from CSV if filters/courses specified
    allowed_titles = None
    if (filters and len(filters) > 0) or (courses and len(courses) > 0):
        if _recipe_df is not None:
            df = _recipe_df.copy()

            # Apply dietary filters
            if filters and len(filters) > 0:
                for f in filters:
                    if f in df.columns:
                        df = df[df[f] == True]

            # Apply course filters
            if courses and len(courses) > 0:
                df = df[df['course_category'].isin(courses)]

            if not df.empty:
                # Normalize titles for matching (strip, lowercase)
                allowed_titles = set(df['title'].str.strip().str.lower().unique())
            else:
                return []  # No recipes match filters
        else:
            return []

    # Get the user's vector using the ML model
    u = _user_vector(user_spices, model)
    nearest_clusters = _nearest_clusters(user_spices, model)

    # Get cluster array
    cluster_arr = np.array(model["cluster_labels"])

    # Create mask for nearest clusters
    cluster_mask = np.zeros(len(cluster_arr), dtype=bool)
    for cid in nearest_clusters:
        cluster_mask |= (cluster_arr == cid)

    # Score all recipes using the model
    scores = model["recipe_matrix"] @ u
    scores[~cluster_mask] = 0

    # Get top indices
    top_idx = np.argsort(scores)[::-1]
    results = []

    for i in top_idx:
        if scores[i] <= 0 or len(results) == top_n:
            break

        recipe_title = model["recipe_titles"][i]

        # If filters applied, only include recipes that match
        if allowed_titles is not None:
            # Normalize model title for comparison
            normalized_title = recipe_title.strip().lower()
            if normalized_title not in allowed_titles:
                continue

        sp = set(model["recipe_spices"][i])
        cid = int(cluster_arr[i])
        profile = ", ".join(model["cluster_top_spices"].get(cid, [])[:3])

        results.append({
            "title": recipe_title,
            "score": round(float(scores[i]), 3),
            "profile": profile,
            "matched": sorted(pantry_set & sp),
            "missing": sorted(sp - pantry_set),
            "all_spices": list(sp),
            "saved": False,
        })

    return results


def get_recipe_details(title: str) -> dict | None:
    load()
    if _recipe_df is None:
        return None
    match = _recipe_df[_recipe_df["title"].str.strip() == title.strip()]
    if match.empty:
        return None
    row = match.iloc[0]
    try:
        ings = ast.literal_eval(str(row["ingredients"]))
        if not isinstance(ings, list):
            ings = str(row["ingredients"]).split(",")
    except Exception:
        ings = str(row["ingredients"]).split(",")
    try:
        dirs = ast.literal_eval(str(row["directions"]))
        if not isinstance(dirs, list):
            dirs = str(row["directions"]).split(",")
    except Exception:
        dirs = str(row["directions"]).split(",")
    return {
        "ingredients": [i.strip() for i in ings if str(i).strip()],
        "directions":  [d.strip() for d in dirs if str(d).strip()],
    }


def suggest_spices(user_spices: list, top_n: int = 5) -> list:
    model = load()
    if model is None:
        return []
    pantry_set = set(user_spices)
    unlock     = Counter()
    for sp_list in model["recipe_spices"]:
        missing = set(sp_list) - pantry_set
        if len(missing) == 1:
            unlock[next(iter(missing))] += 1
    return unlock.most_common(top_n)
