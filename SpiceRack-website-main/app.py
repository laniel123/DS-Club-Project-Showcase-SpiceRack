import os
import sys
import sqlite3

# make sure the project folder is always on the path
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from flask import Flask, request, redirect, render_template, jsonify, flash
from spice_data_v2 import CANONICAL_SPICES, ALIASES
import concurrent.futures
import recommender
import unsplash

# barcode scanner is optional — fails gracefully if deps not installed
barcode_scanner = None
try:
    import barcode_scanner as _bs
    barcode_scanner = _bs
except Exception:
    pass

app = Flask(__name__)
app.secret_key = "spicerack-secret-2026"

SPICES_DB = os.path.join(BASE, "data", "user_spices.db")
SAVED_DB  = os.path.join(BASE, "data", "saved_recipes.db")
ALL_DB    = os.path.join(BASE, "data", "all_recipes.db")


# ── init ──────────────────────────────────────────────────────────────────────

def init_db():
    #new column for the saving of spices
    conn = sqlite3.connect(SPICES_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS spices (id INTEGER PRIMARY KEY, name TEXT UNIQUE, is_favorite INTEGER DEFAULT 0)")
    
    #updates existing spice db.
    try:
        conn.execute("ALTER TABLE spices ADD COLUMN is_favorite INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column already exists
    conn.commit()
    conn.close()

    conn = sqlite3.connect(SAVED_DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS saved_recipes (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        title   TEXT UNIQUE,
        profile TEXT,
        matched TEXT
    )""")
    conn.commit()
    conn.close()

init_db()


# ── helpers ───────────────────────────────────────────────────────────────────

def get_spices():
    conn = sqlite3.connect(SPICES_DB)
    rows = conn.execute("SELECT id, name, is_favorite FROM spices ORDER BY name").fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "is_favorite": bool(r[2])} for r in rows]

def get_saved():
    conn = sqlite3.connect(SAVED_DB)
    rows = conn.execute("SELECT title, profile, matched FROM saved_recipes ORDER BY title").fetchall()
    conn.close()
    return [{"title": r[0], "profile": r[1], "matched": r[2].split(",") if r[2] else []} for r in rows]

def get_saved_titles():
    conn = sqlite3.connect(SAVED_DB)
    titles = {r[0] for r in conn.execute("SELECT title FROM saved_recipes").fetchall()}
    conn.close()
    return titles

def fetch_card_image(title, fallback_spices=None):
    if title in unsplash._cache:
        val = unsplash._cache[title]
        return "" if val == "NOT_FOUND" else val

    if fallback_spices is None:
        fallback_spices = []
    
    details = recommender.get_recipe_details(title)

    if details is None:
        try:
            conn = sqlite3.connect(ALL_DB)
            c = conn.cursor()
            c.execute("SELECT image_url FROM recipes WHERE title = ?", (title,))
            result = c.fetchone()
            conn.close()
            return result[0] if result and result[0] else ""
        except Exception:
            return ""

    try:
        return unsplash.get_photo_url(title, fallback_spices)
    except TypeError:
        try:
            return unsplash.get_photo_url(title)
        except Exception:
            return ""
    except Exception as e:
        print(f"Unsplash API error: {e}")
        return ""

# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    spices      = get_spices()
    spice_names = [s["name"] for s in spices]

    favorite_spices = [s for s in spices if s["is_favorite"]]
    remaining_spices = [s for s in spices if not s["is_favorite"]]

    MAX_RECIPES = 20
    
    raw_recipes = recommender.recommend(spice_names, top_n=MAX_RECIPES)
    suggestions = recommender.suggest_spices(spice_names)
    saved_titles = get_saved_titles()
    PLACEHOLDER_IMG = "https://placehold.co/600x400/E8DDD2/B96B34?font=lato&text=No+Image+Found"

    def process_recipe(r):
        fetched_img = fetch_card_image(r["title"], r.get("all_spices", []))
        r["image"] = fetched_img if fetched_img else PLACEHOLDER_IMG
        r["saved"] = r["title"] in saved_titles
        return r

    # Process all 20 recommended recipes simultaneously 
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        recipes = list(executor.map(process_recipe, raw_recipes))

    raw_saved = get_saved()[:MAX_RECIPES] 
    
    def process_saved(sr):
        fetched_img = fetch_card_image(sr["title"])
        sr["image"] = fetched_img if fetched_img else PLACEHOLDER_IMG
        meta = recommender.get_recipe_meta(sr["title"])
        sr["course"] = meta["course"]
        sr["diets"]  = meta["diets"]
        return sr

    # Process all 20 saved recipes simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        saved_recipes = list(executor.map(process_saved, raw_saved))

    return render_template("index.html",
        favorite_spices=favorite_spices,
        remaining_spices=remaining_spices,
        recipes=recipes,
        suggestions=suggestions,
        saved_recipes=saved_recipes,
    )


@app.route("/add_spices", methods=["POST"])
def add_spices():
    data     = request.form.get("user_spice_add", "")
    accepted = []
    rejected = []

    conn = sqlite3.connect(SPICES_DB)
    for entry in data.split(","):
        raw = entry.strip().lower().strip("\r\n")
        if not raw:
            continue
        canon = ALIASES.get(raw, raw)
        if canon in CANONICAL_SPICES:
            conn.execute("INSERT OR IGNORE INTO spices (name) VALUES (?)", (canon,))
            accepted.append(canon)
        else:
            rejected.append(raw)
    conn.commit()
    conn.close()

    if accepted:
        flash(f"✓ Added: {', '.join(accepted)}", "success")
    if rejected:
        flash(f"✗ Not recognized: {', '.join(rejected)}", "error")

    return redirect("/")


@app.route("/remove_spice", methods=["POST"])
def remove_spice():
    spice_id = request.form.get("spice_id", "").strip()
    if spice_id:
        conn = sqlite3.connect(SPICES_DB)
        conn.execute("DELETE FROM spices WHERE id = ?", (spice_id,))
        conn.commit()
        conn.close()
    return redirect("/")


@app.route("/toggle_spice_favorite", methods=["POST"])
def toggle_spice_favorite():
    data = request.get_json(force=True)
    spice_id = data.get("spice_id")
    if spice_id:
        conn = sqlite3.connect(SPICES_DB)
        conn.execute("UPDATE spices SET is_favorite = 1 - is_favorite WHERE id = ?", (spice_id,))
        conn.commit()
        conn.close()
    return jsonify({"status": "toggled"})


@app.route("/save_recipe", methods=["POST"])
def save_recipe():
    d = request.get_json(force=True)
    print(f"[save] {d.get('title')}")
    conn = sqlite3.connect(SAVED_DB)
    conn.execute(
        "INSERT OR IGNORE INTO saved_recipes (title, profile, matched) VALUES (?,?,?)",
        (d.get("title", ""), d.get("profile", ""), ",".join(d.get("matched", [])))
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})


@app.route("/unsave_recipe", methods=["POST"])
def unsave_recipe():
    d = request.get_json(force=True)
    conn = sqlite3.connect(SAVED_DB)
    conn.execute("DELETE FROM saved_recipes WHERE title = ?", (d.get("title", ""),))
    conn.commit()
    conn.close()
    return jsonify({"status": "unsaved"})


@app.route("/get_recipe_details/<title>")
def get_recipe_details(title):
    details = recommender.get_recipe_details(title)

    if details is None:
        conn = sqlite3.connect(ALL_DB)
        c    = conn.cursor()
        c.execute("SELECT ingredients, directions, image_url FROM recipes WHERE title = ?", (title,))
        result = c.fetchone()
        conn.close()
        if result:
            return jsonify({
                "ingredients": result[0].split(","),
                "directions":  result[1].split(","),
                "image":       result[2],
            })
        return jsonify({"error": "Recipe not found"}), 404

    # pass spices to improve photo search accuracy
    spices = details.get("spices", [])
    try:
        image_url = unsplash.get_photo_url(title, spices)
    except TypeError:
        try:
            image_url = unsplash.get_photo_url(title)
        except Exception:
            image_url = ""
    except Exception:
        image_url = ""
        
    placeholder_image = "https://placehold.co/600x400/E8DDD2/B96B34?font=lato&text=Sorry,+Can%27t+Display+Image"
        
    return jsonify({
        "ingredients": details["ingredients"],
        "directions":  details["directions"],
        # Ensure the detail tab also uses the placeholder if the Unsplash API is maxed out
        "image":       image_url if image_url else placeholder_image,
    })


@app.route("/scan_barcode", methods=["POST"])
def scan_barcode():
    if barcode_scanner is None:
        return jsonify({
            "success": False,
            "name": None,
            "message": "Barcode scanner not available. Run: pip install pyzbar opencv-python && brew install zbar"
        })
    if "barcode_image" not in request.files:
        return jsonify({"success": False, "name": None, "message": "No image received."})

    result = barcode_scanner.scan_image(request.files["barcode_image"].read())

    if result["success"] and result["name"]:
        conn = sqlite3.connect(SPICES_DB)
        conn.execute("INSERT OR IGNORE INTO spices (name) VALUES (?)", (result["name"],))
        conn.commit()
        conn.close()

    return jsonify(result)


@app.route("/api/search")
def search_database():
    try:
        query = request.args.get("q", "").strip().lower()
        if not query: return jsonify([])

        matches = recommender.search_recipes(query)
        
        if matches.empty: 
            return jsonify([])

        saved_titles = get_saved_titles()
        results = []
        
        for title, row in matches.iterrows():
            results.append({
                "title":   str(title),
                "saved":   str(title) in saved_titles,
                "course":  str(row.get("course_category", "Unknown")),
            })
        return jsonify(results)
    except Exception as e:
        print(f"Search API Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/random_recipe")
def get_random_global_recipe():
    try:
        df = recommender._recipe_df
        if df is None: return jsonify({"error": "Data not loaded"}), 500
        # grab a random index
        random_title = df.sample(n=1).index[0]
        return jsonify({"title": str(random_title), "success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)