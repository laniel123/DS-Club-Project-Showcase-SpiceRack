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
CSV_PATH   = os.path.join(BASE, "data", "full_recipes_with_restrictions.csv")

DIET_COLS = [
    'is_vegetarian', 'is_vegan', 'is_dairy_free', 'is_gluten_free',
    'is_keto', 'is_paleo', 'is_halal', 'is_kosher', 'is_hindu_friendly',
]

_model     = None
_recipe_df = None
TOP_CLUSTERS = 5

# Precomputed at load() time — never rebuilt per request
_diet_masks    = {}   # col -> np.ndarray[bool] aligned to model["recipe_titles"]
_course_arr    = None # np.ndarray[str] aligned to model["recipe_titles"]
_norm_titles   = None # pd.Series of lowercase model titles (1.27 M)
_lower_titles  = None # np.ndarray of lowercase df['title'] for /api/search (2.2 M)
_recipe_lookup = None # dict: stripped title -> df row for get_recipe_details
_suggest_cache = {}   # frozenset(pantry) -> suggest result


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
    for kw in _DESSERT_KEYWORDS:
        if kw in t:
            return "Dessert & Sweets"
    for kw in _MAINS_KEYWORDS:
        if kw in t or kw in words:
            return "Mains & Sides"
    return "Other/Miscellaneous"


def _precompute(model, df):
    """Build all per-request caches once after model + CSV are loaded."""
    global _diet_masks, _course_arr, _norm_titles, _lower_titles, _recipe_lookup

    # Normalised lowercase model titles — reused by every filter operation
    _norm_titles = pd.Series([
        t.strip().lower() if isinstance(t, str) else ''
        for t in model['recipe_titles']
    ])

    # Single groupby over all dietary + course columns (one pass through 2.2 M rows)
    title_lower = df['title'].str.strip().str.lower()
    agg_spec = {c: 'min' for c in DIET_COLS if c in df.columns}
    agg_spec['course_category'] = 'first'
    grouped = df.groupby(title_lower).agg(agg_spec)

    # Dietary masks: numpy bool array aligned to model["recipe_titles"]
    for col in DIET_COLS:
        if col in grouped.columns:
            lookup = grouped[col].to_dict()
            _diet_masks[col] = (
                _norm_titles.map(lookup)
                .fillna(False)
                .astype(bool)
                .values
            )

    # Course array: string per model recipe
    course_lookup = grouped['course_category'].to_dict()
    _course_arr = _norm_titles.map(course_lookup).fillna('').values

    # Lowercase titles array for fast /api/search
    _lower_titles = df['title'].str.lower().fillna('').values

    # Title → row dict for O(1) get_recipe_details (keep first occurrence per title)
    dedup = df.drop_duplicates(subset='title', keep='first')
    _recipe_lookup = dict(zip(dedup['title'].str.strip(), dedup.itertuples(index=False)))

    print("[recommender] precomputation done")


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
        if "course_category" not in _recipe_df.columns or _recipe_df["course_category"].isna().all():
            print("[recommender] classifying course categories from titles…")
            _recipe_df["course_category"] = _recipe_df["title"].apply(_classify_course)
            print("[recommender] course classification done")
        if _model is not None:
            _precompute(_model, _recipe_df)

    return _model


def _user_vector(pantry: list, model) -> np.ndarray:
    """pantry → binary → idf_boost (manual) → svd → normalize"""
    user_bin     = np.asarray(model["mlb"].transform([set(pantry)]))
    user_boosted = normalize(user_bin * model["idf_boost"], norm="l2")
    u            = model["svd"].transform(user_boosted)[0]
    norm         = np.linalg.norm(u)
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

    # Build filter mask from precomputed arrays — no per-request groupby
    filter_mask = None
    if (filters and len(filters) > 0) or (courses and len(courses) > 0):
        if _norm_titles is None:
            return []
        filter_mask = np.ones(len(model["recipe_titles"]), dtype=bool)

        for f in (filters or []):
            if f in _diet_masks:
                filter_mask &= _diet_masks[f]

        if courses and len(courses) > 0 and _course_arr is not None:
            filter_mask &= np.isin(np.asarray(_course_arr, dtype=str), courses)

        if not filter_mask.any():
            return []

    u = _user_vector(user_spices, model)
    nearest_clusters = _nearest_clusters(user_spices, model)

    cluster_arr  = np.array(model["cluster_labels"])
    cluster_mask = np.zeros(len(cluster_arr), dtype=bool)
    for cid in nearest_clusters:
        cluster_mask |= (cluster_arr == cid)

    scores = model["recipe_matrix"] @ u
    scores[~cluster_mask] = 0
    if filter_mask is not None:
        scores[~filter_mask] = 0

    top_idx = np.argsort(scores)[::-1]
    results = []
    for i in top_idx:
        if scores[i] <= 0 or len(results) == top_n:
            break
        recipe_title = model["recipe_titles"][i]
        sp  = set(model["recipe_spices"][i])
        cid = int(cluster_arr[i])
        profile = ", ".join(model["cluster_top_spices"].get(cid, [])[:3])
        results.append({
            "title":     recipe_title,
            "score":     round(float(scores[i]), 3),
            "profile":   profile,
            "matched":   sorted(pantry_set & sp),
            "missing":   sorted(sp - pantry_set),
            "all_spices": list(sp),
            "saved":     False,
        })
    return results


def get_recipe_details(title: str) -> dict | None:
    load()
    if _recipe_lookup is None:
        return None
    row = _recipe_lookup.get(title.strip())
    if row is None:
        return None
    try:
        ings = ast.literal_eval(str(row.ingredients))
        if not isinstance(ings, list):
            ings = str(row.ingredients).split(",")
    except Exception:
        ings = str(row.ingredients).split(",")
    try:
        dirs = ast.literal_eval(str(row.directions))
        if not isinstance(dirs, list):
            dirs = str(row.directions).split(",")
    except Exception:
        dirs = str(row.directions).split(",")
    return {
        "ingredients": [i.strip() for i in ings if str(i).strip()],
        "directions":  [d.strip() for d in dirs if str(d).strip()],
    }


def search_recipes(query: str, max_results: int = 50) -> pd.DataFrame:
    """Fast title search using the precomputed lowercase title array."""
    load()
    if _recipe_df is None or _lower_titles is None:
        return pd.DataFrame()
    lower_q = query.lower()
    mask = pd.Series(_lower_titles).str.contains(lower_q, regex=False, na=False).values
    return _recipe_df[mask].head(max_results)


def suggest_spices(user_spices: list, top_n: int = 5) -> list:
    model = load()
    if model is None:
        return []
    key = frozenset(user_spices)
    if key in _suggest_cache:
        return _suggest_cache[key]
    pantry_set = set(user_spices)
    unlock = Counter()
    for sp_list in model["recipe_spices"]:
        missing = set(sp_list) - pantry_set
        if len(missing) == 1:
            unlock[next(iter(missing))] += 1
    result = unlock.most_common(top_n)
    _suggest_cache[key] = result
    return result
