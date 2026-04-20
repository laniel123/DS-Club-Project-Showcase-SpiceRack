"""
recommender.py
Scores recipes using the K-Means + SVD model, then filters to only recipes
that exist in all_recipes.db so the modal always has ingredients/directions.
"""

import os
import sqlite3
import joblib
import numpy as np
from scipy.sparse import hstack, csr_matrix
from collections import Counter

MODEL_PATH = os.path.join(os.path.dirname(__file__), "spicerack_model.joblib")
DB_PATH    = os.path.join(os.path.dirname(__file__), "data", "all_recipes.db")
_model     = None


def load():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
        print(f"[recommender] loaded — {_model['n_recipes']:,} recipes, "
              f"{_model['n_clusters']} clusters")
    return _model


def _known_titles():
    """Titles that exist in all_recipes.db — only these can be recommended."""
    conn = sqlite3.connect(DB_PATH)
    titles = {r[0] for r in conn.execute("SELECT title FROM recipes").fetchall()}
    conn.close()
    return titles


def _canon(spice: str, model) -> str | None:
    s = spice.strip().lower()
    c = model["aliases"].get(s, s)
    return c if c in model["canonical_spices"] else None


def _user_vector(pantry: list, ratings: list, model) -> np.ndarray:
    tfidf = model["spice_tfidf"]
    svd   = model["svd"]
    rvecs = model["recipe_matrix"]
    rids  = model["recipe_ids"]

    # pantry → TF-IDF doc → SVD vector
    doc  = " ".join(
        _canon(s, model).replace(" ", "_")
        for s in pantry if _canon(s, model)
    )
    X_sp = tfidf.transform([doc])

    if model.get("use_ingredients") and model.get("ing_tfidf"):
        w     = model.get("ingredient_weight", 0.3)
        empty = csr_matrix((1, model["ing_tfidf"].transform([""]).shape[1]))
        X_u   = hstack([X_sp * (1 - w), empty * w])
    else:
        X_u = X_sp

    u    = svd.transform(X_u)[0]
    norm = np.linalg.norm(u)
    if norm > 0:
        u /= norm

    # blend in taste from ratings >= 4 stars
    liked = []
    for r in ratings:
        if r.get("rating", 0) >= 4 and r.get("recipe_id") in rids:
            idx    = rids.index(r["recipe_id"])
            weight = r["rating"] - 3
            liked.extend([rvecs[idx]] * weight)

    if liked:
        taste = np.mean(liked, axis=0)
        blend = 0.4 * min(len(liked) / 5, 1.0)
        u     = (1 - blend) * u + blend * taste
        norm  = np.linalg.norm(u)
        if norm > 0:
            u /= norm

    return u


def recommend(user_spices: list, ratings: list = [], top_n: int = 12) -> list:
    """
    Returns ranked recipe recommendations.
    Only returns recipes that exist in all_recipes.db.
    Each result: {title, score, category, matched, missing}
    """
    model = load()
    if model is None or not user_spices:
        return []

    known   = _known_titles()
    rids    = model["recipe_ids"]
    rmeta   = model["recipe_meta"]
    kmeans  = model["kmeans"]
    rvecs   = model["recipe_matrix"]
    tfidf   = model["spice_tfidf"]
    svd     = model["svd"]

    pantry_set = set(user_spices)

    # build user vector
    u = _user_vector(user_spices, ratings, model)

    # find nearest cluster
    doc  = " ".join(
        _canon(s, model).replace(" ", "_")
        for s in user_spices if _canon(s, model)
    )
    X_sp = tfidf.transform([doc])
    if model.get("use_ingredients") and model.get("ing_tfidf"):
        w     = model.get("ingredient_weight", 0.3)
        empty = csr_matrix((1, model["ing_tfidf"].transform([""]).shape[1]))
        X_u   = hstack([X_sp * (1 - w), empty * w])
    else:
        X_u = X_sp
    nearest = int(np.argmin(kmeans.transform(svd.transform(X_u).reshape(1, -1))[0]))

    # score all recipes
    scores      = rvecs @ u
    cluster_arr = np.array([rmeta[rid]["flavor_cluster"] for rid in rids])
    scores[cluster_arr != nearest] = 0

    # rank — only keep recipes in all_recipes.db
    top_idx = np.argsort(scores)[::-1]
    results = []

    for i in top_idx:
        if len(results) == top_n:
            break
        rid   = rids[i]
        meta  = rmeta[rid]
        title = meta["title"]

        # skip if not in db (modal wouldn't work)
        if title not in known:
            continue

        # include even if score is 0 — surface all known recipes ranked by similarity
        recipe_spices = set(meta["spices"])
        matched = sorted(pantry_set & recipe_spices)
        missing = sorted(recipe_spices - pantry_set)

        results.append({
            "title":    title,
            "score":    round(float(scores[i]), 3),
            "category": meta.get("flavor_profile", ""),
            "matched":  matched,
            "missing":  missing,
        })

    # if model didn't surface all db recipes, add remaining ones unscored
    surfaced = {r["title"] for r in results}
    for title in known:
        if title not in surfaced:
            # find this title in the model
            for rid in rids:
                if rmeta[rid]["title"] == title:
                    recipe_spices = set(rmeta[rid]["spices"])
                    matched = sorted(pantry_set & recipe_spices)
                    missing = sorted(recipe_spices - pantry_set)
                    results.append({
                        "title":    title,
                        "score":    0.0,
                        "category": rmeta[rid].get("flavor_profile", ""),
                        "matched":  matched,
                        "missing":  missing,
                    })
                    break

    return results


def suggest_spices(user_spices: list, top_n: int = 5) -> list:
    """
    Returns spices to buy next — ones that unlock the most recipes in the db.
    """
    model = load()
    if model is None:
        return []

    known      = _known_titles()
    pantry_set = set(user_spices)
    unlock     = Counter()

    for rid, meta in model["recipe_meta"].items():
        if meta["title"] not in known:
            continue
        missing = set(meta["spices"]) - pantry_set
        if len(missing) == 1:
            unlock[next(iter(missing))] += 1

    return unlock.most_common(top_n)
