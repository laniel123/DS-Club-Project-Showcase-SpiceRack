from flask import Flask, request, redirect, render_template, jsonify
import sqlite3
import recommender

app = Flask(__name__)



"""
Run commands in terminal. 

cd SpiceRack-website-main
pip install flask scikit-learn scipy joblib numpy
python3 app.py

"""

# ── spice database ────────────────────────────────────────────────────────────

def init_s_db():
    conn = sqlite3.connect("data/user_spices.db")
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS spices (id INTEGER PRIMARY KEY, name TEXT)')
    conn.commit()
    conn.close()

init_s_db()


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    # get user's spices
    conn_s = sqlite3.connect("data/user_spices.db")
    c_s = conn_s.cursor()
    c_s.execute("SELECT name FROM spices")
    user_spices = [row[0] for row in c_s.fetchall()]
    conn_s.close()

    # split into two columns for existing layout
    mid         = len(user_spices) // 2 + (len(user_spices) % 2)
    left_spice  = user_spices[:mid]
    right_spice = user_spices[mid:]

    # get recommendations from the model
    recipes     = recommender.recommend(user_spices)
    suggestions = recommender.suggest_spices(user_spices)

    return render_template("index.html",
        left_spices=left_spice,
        right_spices=right_spice,
        recipes=recipes,
        suggestions=suggestions,
    )


@app.route("/add_spices", methods=['POST'])
def add_spices():
    data = request.form.get('user_spice_add')
    print(f"DEBUG: Received data from website: {data}")

    spices = []
    for entry in data.split(','): # type: ignore
        if entry.strip():
            spices.append(entry.lower().strip())

    conn = sqlite3.connect("data/user_spices.db")
    c = conn.cursor()
    for spice in spices:
        c.execute("INSERT INTO spices (name) VALUES (?)", (spice,))
    conn.commit()
    conn.close()

    return redirect("/")


@app.route('/get_recipe_details/<title>')
def get_recipe_details(title):
    conn = sqlite3.connect("data/all_recipes.db")
    c = conn.cursor()
    c.execute("SELECT ingredients, directions, image_url FROM recipes WHERE title = ?", (title,))
    result = c.fetchone()
    conn.close()

    if result:
        print(f"DEBUG Image URL for '{title}': '{result[2]}'")
        return jsonify({
            "ingredients": result[0].split(","),
            "directions":  result[1].split(","),
            "image":       result[2]
        })
    return (jsonify({"error": "Recipe not found"}), 404)


if __name__ == "__main__":
    app.run(debug=True)
