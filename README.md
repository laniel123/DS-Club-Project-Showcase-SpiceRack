# 🌶 SpiceRack
**DS Club Project — Spring 2026**

Tell us what spices you have, we tell you what you can cook.

---

## What it does

SpiceRack is a recipe recommendation system that takes the spices in your pantry and finds recipes you can make. It learns which spices are rare and distinctive (saffron, galangal) vs common and uninformative (salt, pepper), so recommendations are driven by what makes your pantry unique — not by the fact that you own salt.

- **Recommends recipes** based on your spice pantry using a trained K-Means + SVD model
- **Hearts recipes** to save them to your personal collection
- **Suggests spices to buy** that would unlock the most new recipes
- **Scans barcodes** on spice jars to add spices automatically
- **Validates spice input** — only accepts known canonical spices from a 179-spice vocabulary
- **Modal popups** with full ingredients, directions, and a photo from Unsplash

---

## Project structure

```
SpiceRack/
├── SpiceRack-website-main/     ← Flask website
│   ├── app.py                  ← routes, user key, spice validation
│   ├── recommender.py          ← model inference, multi-cluster search
│   ├── unsplash.py             ← photo API helper
│   ├── barcode_scanner.py      ← barcode scan via pyzbar + Open Food Facts
│   ├── spice_data_v2.py        ← 179 canonical spices, aliases, flavor profiles
│   ├── spicerack_model.joblib  ← trained model (NOT in git — generate locally)
│   ├── data/
│   │   ├── cluster_data.csv    ← full dataset with clusters (NOT in git — generate locally)
│   │   ├── user_spices.db      ← user pantry (SQLite)
│   │   └── saved_recipes.db    ← user saved recipes (SQLite)
│   ├── static/
│   │   ├── style.css
│   │   └── script.js
│   └── templates/
│       └── index.html
│
├── main.ipynb                  ← model training notebook
└── spice_data_v2.py            ← shared spice vocabulary
```

---

## Model

The model is trained in `main.ipynb` on the [RecipeNLG dataset](https://recipenlg.cs.put.poznan.pl/) (~2.2M recipes).

### Training pipeline

1. **Load** — read `full_dataset.csv`, parse NER column to extract canonical spice names
2. **Filter** — keep only recipes with 2+ spices (removes noise)
3. **Cluster** — `MiniBatchKMeans` with 100 clusters discovers natural flavor groups from spice co-occurrence patterns. Oversized clusters (>50k recipes) are split into sub-clusters. Silhouette score: **0.667**
4. **TF-IDF + IDF boost** — downweights common spices (salt: ~0.0001) and upweights rare ones (saffron: high relative weight). IDF weights are squared to make rare spices dominant
5. **SVD** — compresses 179 binary spice dimensions to 100 dense dimensions via `TruncatedSVD`. After L2 normalization, cosine similarity = dot product
6. **Save** — `joblib.dump` saves the full model to `spicerack_model.joblib`

### Model keys saved

```python
{
    "kmeans",            # MiniBatchKMeans — cluster assignment
    "svd",               # TruncatedSVD — dimensionality reduction
    "mlb",               # MultiLabelBinarizer — spice vocabulary
    "tfidf",             # TfidfTransformer — spice frequency weighting
    "idf_boost",         # squared IDF weights — rare spice dominance
    "recipe_matrix",     # (n_recipes, 100) L2-normalized recipe vectors
    "recipe_titles",     # list of recipe titles
    "recipe_spices",     # list of spice lists per recipe
    "cluster_labels",    # cluster ID per recipe
    "cluster_top_spices",# top spices per cluster for display
    "n_clusters",        # total cluster count
    "n_recipes",         # 2,231,142
    "silhouette",        # 0.6694
}
```

### How recommendations work

```
user pantry → mlb.transform() → tfidf.transform() → idf_boost → svd.transform() → normalize
                                                                         ↓
                                                           find top 5 nearest clusters
                                                                         ↓
                                                           scores = recipe_matrix @ user_vec
                                                                         ↓
                                                                    rank → top 12
```

Small pantries (1-2 spices) search up to 9 nearest clusters to avoid missing relevant recipes.

---

## Setup

### 1. Generate the model

Open `main.ipynb` and run all cells in order. You need the RecipeNLG dataset (`full_dataset.csv`) in the project root. Download it from [Kaggle](https://www.kaggle.com/datasets/saloni1712/recipenlg).

The notebook will save `spicerack_model.joblib` to the project root.

### 2. Generate the full recipe CSV

After running the clustering cell in the notebook, run:

```python
df_cluster.to_csv("SpiceRack-website-main/data/cluster_data.csv", index=False)
```

This saves all 2.2M recipes with their cluster assignments for the modal to use.

### 3. Install dependencies

```bash
pip install flask scikit-learn scipy joblib numpy pandas requests
pip install pyzbar opencv-python   # for barcode scanner
brew install zbar                  # Mac only, for barcode scanner
```

### 4. Run the website

```bash
cd SpiceRack-website-main
python3 app.py
```

Open localhost

---

## Files NOT in git

These files are too large for GitHub and must be generated locally:

| File | Size | How to generate |
|------|------|-----------------|
| `spicerack_model.joblib` | ~974 MB | Run `main.ipynb` |
| `data/cluster_data.csv` | ~1-2 GB | Run `df_cluster.to_csv(...)` in notebook |
| `full_dataset.csv` | ~2.2M rows | Download from Kaggle |

---

## Tech stack

- **Python 3.11**
- **scikit-learn** — MiniBatchKMeans, TruncatedSVD, TfidfTransformer, MultiLabelBinarizer
- **Flask** — web server
- **SQLite** — user spices and saved recipes
- **joblib** — model serialization
- **pandas / numpy** — data processing
- **Unsplash API** — recipe photos
- **pyzbar + OpenCV** — barcode scanning (in development)
- **Open Food Facts API** — barcode product lookup

---

## Team

SpiceRack: Daniel Larson, Elijah Ret, Arya Moghadam, Ethan Rao, Luke Maldonado, Austin Pak, Emanuel Rodriguez  — Spring 2026