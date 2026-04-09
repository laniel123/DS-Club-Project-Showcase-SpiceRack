"""
Spicerack - Recipe Recommender
DS Club Project - Spring 2026

Tell us what spices you have, we tell you what you can cook.
Also suggests what spice to buy next to unlock the most new recipes.

Usage:
    python main.py
"""

import re
import time
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.decomposition import NMF
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import MultiLabelBinarizer

from spice_data_v2 import SPICES, ALIASES, CANONICAL_SPICES, FLAVOR_PROFILES, REGION_PROFILES

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG - edit these
# ─────────────────────────────────────────────────────────────────────────────

CSV_PATH    = "/Users/daniellarson/Desktop/SpiceRack/cookingdataset/RecipeNLG_dataset.csv"
MODEL_PATH  = "Notebooks/flavor_profile_model.joblib"
SAMPLE_SIZE = None   # set to an int like 50_000 to run faster
N_COMPONENTS = 20    # NMF components - only used when training from scratch
NMF_SAMPLE   = 200_000  # rows used to train NMF (keeps it fast)

# spices you actually have right now
MY_PANTRY = [
    "garlic",
    "cumin",
    "paprika",
    "chili powder",
    "oregano",
    "black pepper",
    "salt",
    "cinnamon",
    "ginger",
]

# spices that MUST show up in every recommended recipe
# leave as [] if you don't care
MUST_USE = [
    "cumin",
    "garlic",
]

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def clean(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z\s']", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def to_canonical(spice: str) -> str:
    n = clean(spice)
    return clean(ALIASES.get(n, n))


def validate_spices(raw_list: list, label: str) -> set:
    valid, bad = set(), []
    for s in raw_list:
        c = to_canonical(s)
        if c in CANONICAL_SPICES:
            valid.add(c)
        else:
            bad.append(s)
    if bad:
        print(f"warning ({label}): didn't recognize these, skipping: {bad}")
    return valid


# sorted longest-first so "smoked paprika" matches before "paprika"
SPICE_PATTERNS = sorted(
    [(sp, clean(sp), re.compile(rf"(^| ){re.escape(clean(sp))}( |$)")) for sp in SPICES],
    key=lambda x: -len(x[0])
)


def get_spices_from_recipe(ingredients) -> set:
    raw  = " ".join(str(x) for x in ingredients) if isinstance(ingredients, list) else str(ingredients)
    text = clean(raw)
    found = set()
    for _, norm, pat in SPICE_PATTERNS:
        if pat.search(" " + text + " "):
            found.add(norm)
    return {to_canonical(sp) for sp in found}


def parse_ingredient_string(x) -> list:
    if isinstance(x, list):
        return [str(i) for i in x]
    if not isinstance(x, str):
        return []
    s = x.strip()
    if s.startswith("[") and s.endswith("]"):
        items = re.findall(r"'([^']*)'|\"([^\"]*)\"", s)
        parsed = [a if a else b for a, b in items]
        return parsed if parsed else [s]
    return [s]

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

print(f"loading {CSV_PATH}...")
df = pd.read_csv(CSV_PATH)

if SAMPLE_SIZE and len(df) > SAMPLE_SIZE:
    df = df.sample(n=SAMPLE_SIZE, random_state=42).reset_index(drop=True)

df["ingredients_parsed"] = df["ingredients"].apply(parse_ingredient_string)
df["spices"]             = df["ingredients_parsed"].apply(get_spices_from_recipe)

mlb = MultiLabelBinarizer(classes=sorted(CANONICAL_SPICES))
X   = np.asarray(mlb.fit_transform(df["spices"]))

print(f"done - {len(df):,} recipes, matrix shape: {X.shape}")
print(f"avg spices per recipe: {X.sum(axis=1).mean():.1f}")

# ─────────────────────────────────────────────────────────────────────────────
# NMF MODEL - load saved model or train from scratch
# ─────────────────────────────────────────────────────────────────────────────

nmf         = None
spice_names = list(mlb.classes_)
H           = None
LEARNED_LABELS = []

if Path(MODEL_PATH).exists():
    saved = joblib.load(MODEL_PATH)
    if saved.get("classes") == spice_names:
        print("loaded saved NMF model")
        nmf = saved["nmf"]
    else:
        print("saved model has different spice classes - retraining...")

if nmf is None:
    print("training NMF model...")
    train_X      = X[:NMF_SAMPLE] if NMF_SAMPLE and NMF_SAMPLE < len(X) else X
    n_samples, n_features = train_X.shape
    n_components = max(1, min(N_COMPONENTS, n_samples, n_features))
    init_method  = "nndsvda" if n_components <= min(n_samples, n_features) else "random"
    t0  = time.time()
    nmf = NMF(n_components=n_components, init=init_method, max_iter=300, random_state=42)
    nmf.fit(train_X)
    joblib.dump({"nmf": nmf, "classes": spice_names}, MODEL_PATH)
    print(f"trained in {time.time()-t0:.1f}s - saved to {MODEL_PATH}")

H = nmf.components_
for row in H:
    top_idx = row.argsort()[-3:][::-1]
    LEARNED_LABELS.append(" / ".join(spice_names[i] for i in top_idx))

print(f"NMF ready - {H.shape[0]} components, {len(spice_names)} spices")

# ─────────────────────────────────────────────────────────────────────────────
# MODEL FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_flavor_profiles(pantry: set, min_coverage: float = 0.3) -> list:
    """Coverage-based flavor profiles from spice_data_v2."""
    results = []
    for profile, spice_set in FLAVOR_PROFILES.items():
        matched  = pantry & spice_set
        coverage = len(matched) / len(spice_set)
        if coverage >= min_coverage:
            results.append((profile, round(coverage, 2), sorted(matched)))
    return sorted(results, key=lambda x: -x[1])


def get_learned_profiles(pantry: set, top_k: int = 5, min_score: float = 0.05) -> list:
    """NMF-based flavor profiles learned from recipe data."""
    if H is None:
        return []
    _H          = H  # local binding so type checker knows it's non-None inside lambdas
    vec         = np.asarray(mlb.transform([pantry]), dtype=float)
    scores      = (vec @ H.T).flatten()
    max_s       = H.sum(axis=1)
    max_s[max_s == 0] = 1
    norm_scores = scores / max_s

    results = []
    for i in norm_scores.argsort()[::-1][:top_k]:
        s = float(norm_scores[i])
        if s < min_score:
            break
        pantry_idx     = [spice_names.index(sp) for sp in pantry if sp in spice_names]
        driving_spices = sorted(pantry_idx, key=lambda j: -_H[i][j])[:5]
        results.append((LEARNED_LABELS[i], round(s, 3), [spice_names[j] for j in driving_spices]))
    return results


def get_regions(profile_names: list) -> list:
    """Maps matched flavor profiles to culinary regions."""
    results = []
    for region, profiles in REGION_PROFILES.items():
        matched = [p for p in profiles if p in profile_names]
        if matched:
            results.append((region, matched))
    return sorted(results, key=lambda x: -len(x[1]))


def recommend(pantry: set, must_use: set, top_k: int = 10, min_match: int = 2) -> pd.DataFrame:
    """Jaccard similarity recommendation with optional must-use filter."""
    user_vec = np.asarray(mlb.transform([pantry]))

    if must_use:
        spice_cols = list(mlb.classes_)
        must_idx   = [spice_cols.index(s) for s in must_use if s in spice_cols]
        must_mask  = X[:, must_idx].min(axis=1).astype(bool) if must_idx else np.ones(len(df), dtype=bool)
    else:
        must_mask = np.ones(len(df), dtype=bool)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sims = 1.0 - pairwise_distances(user_vec, X, metric="jaccard").flatten()

    match_counts = (X & user_vec).sum(axis=1)
    valid = np.where(must_mask & (match_counts >= min_match))[0]

    if len(valid) == 0:
        print("no recipes matched the must-use filter, showing best results without it")
        valid = np.where(match_counts >= min_match)[0]

    ranked = valid[np.lexsort((-match_counts[valid], -sims[valid]))][:top_k]

    out = df.loc[ranked, ["title"]].copy()
    out["similarity"]     = sims[ranked].round(3)
    out["matched_spices"] = df.loc[ranked, "spices"].apply(lambda s: sorted(s & pantry))
    out["num_matched"]    = match_counts[ranked]
    return out.sort_values(["similarity", "num_matched"], ascending=False).reset_index(drop=True)


def tag_region(recipe_spices: set) -> str:
    """Assign a single region label to a recipe based on its spice set."""
    profiles = get_flavor_profiles(recipe_spices, min_coverage=0.2)
    if not profiles:
        return "Other"
    top_profile = profiles[0][0]
    for region, region_profiles in REGION_PROFILES.items():
        if top_profile in region_profiles:
            return region
    return "Other"


def suggest_next_spice(pantry: set, top_k: int = 5, min_match: int = 2, threshold: float = 0.4) -> pd.DataFrame:
    """Rank missing spices by how many new recipes each one would unlock."""
    baseline        = recommend(pantry, must_use=set(), top_k=10_000, min_match=min_match)
    baseline_titles = set(baseline["title"])
    baseline_count  = len(baseline[baseline["similarity"] >= threshold])
    missing         = [s for s in CANONICAL_SPICES if s not in pantry]

    print(f"baseline: {baseline_count} recipes above {threshold} similarity")
    print(f"testing {len(missing)} candidate spices...")

    results = []
    for spice in missing:
        expanded  = pantry | {spice}
        new_recs  = recommend(expanded, must_use=set(), top_k=10_000, min_match=min_match)
        new_count = len(new_recs[new_recs["similarity"] >= threshold])
        new_titles = set(new_recs["title"]) - baseline_titles
        results.append({
            "spice":          spice,
            "newly_unlocked": new_count - baseline_count,
            "examples":       list(new_titles)[:3],
        })

    return pd.DataFrame(results).sort_values("newly_unlocked", ascending=False).head(top_k).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    pantry   = validate_spices(MY_PANTRY, label="pantry")
    must_use = validate_spices(MUST_USE,  label="must-use")

    extras = must_use - pantry
    if extras:
        print(f"added to pantry automatically: {extras}")
        pantry |= extras

    print(f"\npantry:   {sorted(pantry)}")
    print(f"must-use: {sorted(must_use)}")

    # --- flavor profiles (rule-based) ---
    print("\n" + "-" * 55)
    print("flavor profiles (rule-based)")
    print("-" * 55)
    profiles = get_flavor_profiles(pantry)
    if not profiles:
        print("no strong profiles found - try adding more spices")
    else:
        for name, score, matched in profiles:
            bar = "#" * int(score * 10) + "." * (10 - int(score * 10))
            print(f"  [{bar}] {int(score*100)}%  {name}")
            print(f"           spices: {', '.join(matched)}")

    # --- flavor profiles (NMF model) ---
    print("\n" + "-" * 55)
    print("flavor profiles (learned from data)")
    print("-" * 55)
    learned = get_learned_profiles(pantry)
    if not learned:
        print("no strong learned profiles found")
    else:
        for label, score, driving in learned:
            print(f"  [{score:.3f}]  {label}")
            print(f"           driven by: {', '.join(driving)}")

    # --- culinary regions ---
    print("\n" + "-" * 55)
    print("cuisines you can cook")
    print("-" * 55)
    regions = get_regions([p[0] for p in profiles])
    if not regions:
        print("no strong regional match found")
    else:
        for region, matched_profiles in regions:
            print(f"  {region}")
            print(f"    via: {', '.join(matched_profiles)}")

    # --- top recipe recommendations ---
    print("\n" + "-" * 55)
    if must_use:
        print(f"top recipes (must contain: {sorted(must_use)})")
    else:
        print("top recipes")
    print("-" * 55)
    recs = recommend(pantry, must_use, top_k=10, min_match=2)
    print(recs[["title", "similarity", "matched_spices", "num_matched"]].to_string(index=False))

    # --- recipes by region ---
    print("\n" + "-" * 55)
    print("recipes by region")
    print("-" * 55)
    pool = recommend(pantry, must_use, top_k=200, min_match=2)
    pool["region"] = pool["title"].apply(
        lambda t: tag_region(
            df[df["title"] == t]["spices"].iloc[0] if (df["title"] == t).any() else set()
        )
    )
    for region in pool["region"].unique():
        if region == "Other":
            continue
        subset = pool[pool["region"] == region].head(3)
        print(f"\n  {region}")
        for _, row in subset.iterrows():
            print(f"    - {row['title']}  (similarity: {row['similarity']})")

    # --- next spice to buy ---
    print("\n" + "-" * 55)
    print("spices to buy next")
    print("-" * 55)
    next_spice = suggest_next_spice(pantry, top_k=5, min_match=2)
    for _, row in next_spice.iterrows():
        print(f"  {row['spice']:<25} {row['newly_unlocked']:+} new recipes")
        if row["examples"]:
            print(f"  {'':25} e.g. {row['examples'][0]}")
