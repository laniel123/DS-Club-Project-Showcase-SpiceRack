import os
import sys
import sqlite3

# make sure the project folder is always on the path
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from flask import Flask, request, redirect, render_template, jsonify, flash
from spice_data_v2 import CANONICAL_SPICES, ALIASES
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
    conn = sqlite3.connect(SPICES_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS spices (id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
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


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    spices      = get_spices()
    spice_names = [s["name"] for s in spices]
    mid         = len(spices) // 2 + (len(spices) % 2)

    recipes     = recommender.recommend(spice_names)
    suggestions = recommender.suggest_spices(spice_names)
    print(recipes)
    print(suggestions)

    saved_titles = get_saved_titles()
    for r in recipes:
        r["saved"] = r["title"] in saved_titles

    return render_template("index.html",
        left_spices=spices[:mid],
        right_spices=spices[mid:],
        recipes=recipes,
        suggestions=suggestions,
        saved_recipes=get_saved(),
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

    image_url = unsplash.get_photo_url(title)
    return jsonify({
        "ingredients": details["ingredients"],
        "directions":  details["directions"],
        "image":       image_url,
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


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
