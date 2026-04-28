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
import threading
import numpy as np
import pandas as pd
from collections import Counter
from sklearn.preprocessing import normalize

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "spicerack_model.joblib")

CSV_PATH = os.path.join(BASE, "data", "full_recipes_with_restrictions.csv")

_model     = None
_recipe_df = None
_lower_titles = None
TOP_CLUSTERS = 5

_load_lock = threading.Lock()

def load():
    global _model, _recipe_df, _lower_titles
    
    with _load_lock:
        if _model is None and os.path.exists(MODEL_PATH):
            _model = joblib.load(MODEL_PATH)
            print(f"[recommender] loaded — {_model['n_recipes']:,} recipes, "
                  f"{_model['n_clusters']} clusters, "
                  f"silhouette {_model.get('silhouette','?')}")
        
        if _recipe_df is None and os.path.exists(CSV_PATH):
            _recipe_df = pd.read_csv(CSV_PATH)
            _recipe_df["title"] = _recipe_df["title"].astype(str).str.strip()
            _recipe_df.set_index("title", inplace=True)
            
            _lower_titles = _recipe_df.index.astype(str).str.lower().values
            print(f"[recommender] recipe data — {len(_recipe_df):,} rows")
            
    return _model


def search_recipes(query: str, max_results: int = 50) -> pd.DataFrame:
    """Fast title search using the precomputed lowercase index array."""
    load()
    if _recipe_df is None or _lower_titles is None:
        return pd.DataFrame()
        
    lower_q = query.lower()
    mask = pd.Series(_lower_titles).str.contains(lower_q, regex=False).fillna(False).values
    
    return _recipe_df.iloc[mask].head(max_results).copy()


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


def get_recipe_meta(title: str) -> dict:
    """Helper to fetch course and diets from the new CSV."""
    load()
    meta = {"course": "Unknown", "diets": []}
    if _recipe_df is None:
        return meta

    clean_title = title.strip()
    if clean_title not in _recipe_df.index:
        return meta
        
    row = _recipe_df.loc[clean_title]
    
    # only uses first title occurance in the dataframe
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]

    meta["course"] = str(row.get("course_category", "Unknown"))

    # Map your CSV columns to the frontend filter names
    diet_cols = {
        "vegetarian": "is_vegetarian", "vegan": "is_vegan",
        "dairy-free": "is_dairy_free", "gluten-free": "is_gluten_free",
        "keto": "is_keto", "paleo": "is_paleo",
        "halal": "is_halal", "kosher": "is_kosher", "hindu": "is_hindu_friendly"
    }
    for diet_name, col in diet_cols.items():
        if col in row and row[col] in [True, "True", "true", 1, "1"]:
            meta["diets"].append(diet_name)

    return meta


def recommend(user_spices: list, top_n: int = 12) -> list:
    model = load()
    print(type(model))
    if model is None or not user_spices:
        return []

    pantry_set  = set(user_spices)
    cluster_arr = np.array(model["cluster_labels"])

    u                = _user_vector(user_spices, model)
    nearest_clusters = _nearest_clusters(user_spices, model)

    # mask covering all nearest clusters
    cluster_mask = np.zeros(len(cluster_arr), dtype=bool)
    for cid in nearest_clusters:
        cluster_mask |= (cluster_arr == cid)

    scores = model["recipe_matrix"] @ u
    scores[~cluster_mask] = 0

    if len(scores) > top_n:
        # Partitions only the top_n elements, avoiding a full matrix sort
        idx = np.argpartition(scores, -top_n)[-top_n:]
        top_idx = idx[np.argsort(scores[idx])][::-1]
    else:
        top_idx = np.argsort(scores)[::-1]
        
    results = []

    for i in top_idx:
        if scores[i] <= 0 or len(results) == top_n:
            break
        sp      = set(model["recipe_spices"][i])
        cid     = int(cluster_arr[i])
        profile = ", ".join(model["cluster_top_spices"].get(cid, [])[:3])
        title   = model["recipe_titles"][i]
        meta = get_recipe_meta(title)

        results.append({
            "title":      title,
            "score":      round(float(scores[i]), 3),
            "profile":    profile,
            "matched":    sorted(pantry_set & sp),
            "missing":    sorted(sp - pantry_set),
            "all_spices": list(sp),
            "saved":      False,
            "course":     meta["course"],
            "diets":      meta["diets"]
        })

    return results


def get_recipe_details(title: str) -> dict | None:
    load()
    if _recipe_df is None:
        return None

    clean_title = title.strip()
    if clean_title not in _recipe_df.index:
        return None
        
    row = _recipe_df.loc[clean_title]
    
    # only uses first title occurance in the dataframe
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]

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
