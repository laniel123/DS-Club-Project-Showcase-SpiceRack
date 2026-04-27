import os
import sys
import sqlite3
import ast

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from flask import Flask, request, redirect, render_template, jsonify, flash
from spice_data_v2 import CANONICAL_SPICES, ALIASES
import recommender
import unsplash

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


def init_db():
    conn = sqlite3.connect(SPICES_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS spices (id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
    conn.commit()
    conn.close()
    conn = sqlite3.connect(SAVED_DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS saved_recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT UNIQUE, profile TEXT, matched TEXT
    )""")
    conn.commit()
    conn.close()

init_db()


def get_spices():
    conn = sqlite3.connect(SPICES_DB)
    rows = conn.execute("SELECT id, name FROM spices ORDER BY name").fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1]} for r in rows]

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


@app.route("/")
def index():
    # 1. Capture checkbox preferences and course filters from URL
    selected_prefs = request.args.getlist("pref")
    selected_courses = request.args.getlist("course_pref")

    spices = get_spices()
    spice_names = [s["name"] for s in spices]

    # 2. Get recommendations based on spices AND filters
    recipes = recommender.recommend(
        spice_names,
        filters=selected_prefs,
        courses=selected_courses
    ) or []

    # 3. Get suggestions and saved data for UI logic
    suggestions = recommender.suggest_spices(spice_names)
    saved_titles = get_saved_titles()

    # 4. Mark saved status for Recommended recipes
    for r in recipes:
        r["saved"] = r["title"] in saved_titles
        r["image"] = unsplash.get_photo_url(r["title"], r.get("all_spices", []))
        # profile and matched already come correctly from recommender

    # 5. Fetch images for Saved recipes
    saved_recipes = get_saved()
    for sr in saved_recipes:
        sr["image"] = unsplash.get_photo_url(sr["title"])

    # Split spices for the two-column pantry view
    mid = len(spices) // 2 + (len(spices) % 2)

    return render_template("index.html",
        left_spices=spices[:mid],
        right_spices=spices[mid:],
        recipes=recipes,
        suggestions=suggestions,
        saved_recipes=saved_recipes
    )


@app.route("/add_spices", methods=["POST"])
def add_spices():
    data     = request.form.get("user_spice_add", "")
    accepted, rejected = [], []
    conn = sqlite3.connect(SPICES_DB)
    for entry in data.split(","):
        raw = entry.strip().lower().strip("\r\n")
        if not raw: continue
        canon = ALIASES.get(raw, raw)
        if canon in CANONICAL_SPICES:
            conn.execute("INSERT OR IGNORE INTO spices (name) VALUES (?)", (canon,))
            accepted.append(canon)
        else:
            rejected.append(raw)
    conn.commit()
    conn.close()
    if accepted: flash(f"✓ Added: {', '.join(accepted)}", "success")
    if rejected: flash(f"✗ Not recognized: {', '.join(rejected)}", "error")
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


@app.route("/save_recipe", methods=["POST"])
def save_recipe():
    d = request.get_json(force=True)
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
        c = conn.cursor()
        c.execute("SELECT ingredients, directions, image_url FROM recipes WHERE title = ?", (title,))
        result = c.fetchone()
        conn.close()
        if result:
            return jsonify({"ingredients": result[0].split(","),
                            "directions":  result[1].split(","),
                            "image":       result[2]})
        return jsonify({"error": "Recipe not found"}), 404

    image_url = unsplash.get_photo_url(title, details.get("spices", []))
    return jsonify({
        "ingredients": details["ingredients"],
        "directions":  details["directions"],
        "image":       image_url,
    })


@app.route("/api/search")
def search_database():
    try:
        query      = request.args.get("q", "").strip().lower()
        if not query: return jsonify([])
        df         = recommender._recipe_df
        if df is None: return jsonify([])
        user_spices = {s["name"].lower() for s in get_spices()}
        saved_titles = get_saved_titles()
        matches = df[df['title'].str.contains(query, case=False, na=False)].head(50)
        results = []
        for _, row in matches.iterrows():
            try:
                recipe_spices = ast.literal_eval(str(row['spices']))
                matched = [s for s in recipe_spices if s.lower() in user_spices]
            except:
                matched = []
            results.append({
                "title":   row['title'],
                "profile": "Global Database",
                "saved":   row['title'] in saved_titles,
                "matched": matched,
                "image":   unsplash._cache.get(row['title'], ""),
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/random_recipe")
def get_random_global_recipe():
    try:
        df = recommender._recipe_df
        if df is None: return jsonify({"error": "Data not loaded"}), 500
        row = df.sample(n=1).iloc[0]
        return jsonify({"title": row['title'], "success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/scan_barcode", methods=["POST"])
def scan_barcode():
    if barcode_scanner is None:
        return jsonify({"success": False, "message": "Scanner unavailable."})
    if "barcode_image" not in request.files:
        return jsonify({"success": False, "message": "No image received."})
    result = barcode_scanner.scan_image(request.files["barcode_image"].read())
    if result["success"] and result["name"]:
        conn = sqlite3.connect(SPICES_DB)
        conn.execute("INSERT OR IGNORE INTO spices (name) VALUES (?)", (result["name"],))
        conn.commit()
        conn.close()
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)