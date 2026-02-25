# parse_spices.py
# ─────────────────────────────────────────────────────────────────────────────
# Streams through the full RecipeNLG dataset in chunks, extracts ingredient
# tokens, and generates a ranked report of:
#   1. How well your existing SPICES list is covered
#   2. Common ingredients NOT in your list that look like spices/herbs
#
# HOW TO RUN:
#   1. Place this file in the same folder as spice_data.py
#   2. Update CSV_PATH below to point to your RecipeNLG CSV
#   3. Run: python parse_spices.py
#   4. A report file "spice_audit_report.txt" will be generated
#   5. Paste the report back to Claude to update spice_data.py
# ─────────────────────────────────────────────────────────────────────────────

import re
import ast
import csv
from collections import Counter
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
CSV_PATH   = "/Users/daniellarson/Desktop/SpiceRack/cookingdataset/RecipeNLG_dataset.csv"
OUTPUT     = "spice_audit_report.txt"
CHUNK_SIZE = 10_000   # rows processed at a time (keeps RAM low)
TOP_N      = 200      # how many unlisted candidates to show in the report

# ── Import your existing spice list ───────────────────────────────────────────
try:
    from spice_data import SPICES, ALIASES, CANONICAL_SPICES
    print(f"✅ Loaded spice_data.py — {len(SPICES)} spices, {len(ALIASES)} aliases")
except ImportError:
    print("⚠️  Could not import spice_data.py — make sure it's in the same folder.")
    print("   Continuing with empty spice list for discovery mode.")
    SPICES, ALIASES, CANONICAL_SPICES = [], {}, []


# ── Known non-spice words to filter out of candidates ────────────────────────
# These are common ingredient words that are definitely NOT spices
NON_SPICE_WORDS = {
    # Measurements & quantities
    "cup", "cups", "tablespoon", "tablespoons", "tbsp", "teaspoon", "teaspoons",
    "tsp", "ounce", "ounces", "oz", "pound", "pounds", "lb", "lbs", "gram",
    "grams", "kg", "kilogram", "ml", "liter", "litre", "quart", "pint", "gallon",
    "large", "medium", "small", "whole", "half", "quarter", "piece", "pieces",
    "slice", "slices", "bunch", "can", "cans", "jar", "package", "packages",
    "bag", "box", "bottle", "clove", "cloves", "sprig", "sprigs", "handful",
    "pinch", "dash", "drop", "drops", "inch", "inches",

    # Cooking states / descriptors
    "fresh", "dried", "ground", "chopped", "minced", "sliced", "diced",
    "crushed", "grated", "shredded", "peeled", "seeded", "stemmed", "toasted",
    "roasted", "smoked", "pickled", "frozen", "cooked", "raw", "uncooked",
    "optional", "to taste", "divided", "softened", "melted", "beaten",
    "sifted", "packed", "heaping", "level", "about", "approximately",

    # Common non-spice ingredients
    "water", "oil", "butter", "flour", "sugar", "salt", "egg", "eggs",
    "milk", "cream", "cheese", "bread", "rice", "pasta", "chicken", "beef",
    "pork", "fish", "shrimp", "onion", "garlic", "tomato", "potato",
    "carrot", "celery", "pepper", "lemon", "lime", "orange", "apple",
    "wine", "vinegar", "stock", "broth", "sauce", "juice", "honey",
    "syrup", "jam", "yeast", "baking", "powder", "soda", "vanilla",
    "extract", "zest", "peel", "leaf", "leaves", "seed", "seeds",
    "and", "or", "with", "for", "the", "a", "an", "of", "in", "to",
    "from", "into", "plus", "more", "less", "taste",

    # Numbers and single letters
    *[str(i) for i in range(100)],
    *list("abcdefghijklmnopqrstuvwxyz"),
}

# ── Known spice-adjacent words that ARE worth flagging ────────────────────────
# If a candidate token contains any of these, it's more likely to be a spice
SPICE_HINTS = {
    "pepper", "chili", "chile", "chilli", "spice", "herb", "seed", "powder",
    "flake", "flakes", "dried", "ground", "smoked", "seasoning", "blend",
    "salt", "paprika", "cumin", "oregano", "thyme", "basil", "curry",
    "masala", "garam", "turmeric", "coriander", "cardamom", "cinnamon",
    "ginger", "fennel", "mustard", "anise", "clove", "nutmeg", "saffron",
    "sumac", "za'atar", "zaatar", "dukkah", "harissa", "baharat",
    "berbere", "ras", "annatto", "achiote", "fenugreek", "asafoetida",
    "tarragon", "marjoram", "savory", "dill", "parsley", "sage", "rosemary",
    "cayenne", "chipotle", "ancho", "guajillo", "habanero", "jalapeno",
    "serrano", "poblano", "pasilla", "mulato", "urfa", "aleppo",
    "gochugaru", "togarashi", "furikake", "five spice", "allspice",
    "mace", "galangal", "lemongrass", "kaffir", "makrut", "nigella",
    "caraway", "poppy", "sesame", "celery", "bay", "lavender", "hibiscus",
    "chamomile", "rose", "saffron", "vanilla", "truffle", "porcini",
    "shiitake", "miso", "bonito", "kombu", "msg", "nutritional",
}


# ── Utilities ─────────────────────────────────────────────────────────────────

def normalize(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z\s']", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_ingredients_field(x):
    """Parse RecipeNLG stringified list or plain string."""
    if isinstance(x, list):
        return x
    if not isinstance(x, str):
        return []
    s = x.strip()
    if s.startswith("[") and s.endswith("]"):
        # Try ast first (safer)
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list):
                return [str(i) for i in parsed]
        except Exception:
            pass
        # Fallback: regex
        items = re.findall(r"'([^']*)'|\"([^\"]*?)\"", s)
        return [a if a else b for a, b in items]
    return [s]


def extract_ngrams(text: str, max_n: int = 4) -> list:
    """Extract all 1–max_n word ngrams from normalized text."""
    words = text.split()
    ngrams = []
    for n in range(1, max_n + 1):
        for i in range(len(words) - n + 1):
            ngrams.append(" ".join(words[i:i+n]))
    return ngrams


def looks_like_spice(token: str) -> bool:
    """Heuristic: does this token look like it could be a spice/herb?"""
    if len(token) < 3:
        return False
    words = token.split()
    # Filter out purely numeric or single char words
    if all(w in NON_SPICE_WORDS for w in words):
        return False
    # Boost tokens that contain known spice-adjacent words
    for hint in SPICE_HINTS:
        if hint in token:
            return True
    # Multi-word tokens ending in common spice suffixes
    if len(words) >= 2:
        if words[-1] in {"powder", "flakes", "seed", "seeds", "leaf", "leaves",
                         "pepper", "salt", "spice", "seasoning", "blend", "herb"}:
            return True
    return False


# ── Main parsing loop ─────────────────────────────────────────────────────────

def run_audit():
    csv_path = Path(CSV_PATH)
    if not csv_path.exists():
        print(f"❌ File not found: {CSV_PATH}")
        print("   Update CSV_PATH at the top of this script.")
        return

    print(f"\n📂 Parsing: {csv_path}")
    print(f"   Chunk size : {CHUNK_SIZE:,} rows")
    print(f"   This may take 2–5 minutes for the full dataset...\n")

    # Counters
    existing_spice_counter  = Counter()   # spices already in your list
    candidate_counter       = Counter()   # new potential spices
    total_recipes           = 0
    recipes_with_any_spice  = 0

    # Build set of canonical spices for fast lookup
    canonical_set = set(CANONICAL_SPICES)

    # Also build patterns for existing spices
    existing_patterns = []
    all_known = sorted(set(list(SPICES) + list(ALIASES.keys())), key=len, reverse=True)
    for sp in all_known:
        norm = normalize(sp)
        pat  = re.compile(rf"(^| ){re.escape(norm)}( |$)")
        existing_patterns.append((normalize(ALIASES.get(sp, sp)), pat))

    # Stream CSV in chunks
    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)

        chunk = []
        for row in reader:
            chunk.append(row)
            if len(chunk) >= CHUNK_SIZE:
                process_chunk(
                    chunk, existing_patterns, canonical_set,
                    existing_spice_counter, candidate_counter,
                )
                total_recipes += len(chunk)
                recipes_with_any_spice += sum(
                    1 for r in chunk
                    if any(
                        pat.search(" " + normalize(" ".join(parse_ingredients_field(r.get("ingredients", "")))) + " ")
                        for _, pat in existing_patterns[:10]  # quick check
                    )
                )
                chunk = []
                if total_recipes % 100_000 == 0:
                    print(f"   Processed {total_recipes:,} recipes...")

        # Process final partial chunk
        if chunk:
            process_chunk(
                chunk, existing_patterns, canonical_set,
                existing_spice_counter, candidate_counter,
            )
            total_recipes += len(chunk)

    print(f"\n✅ Done — {total_recipes:,} recipes processed.\n")

    # ── Generate report ───────────────────────────────────────────────────────
    write_report(
        total_recipes,
        existing_spice_counter,
        candidate_counter,
        canonical_set,
    )


def process_chunk(chunk, existing_patterns, canonical_set,
                  existing_spice_counter, candidate_counter):
    """Process one chunk of rows."""
    for row in chunk:
        raw = row.get("ingredients", "") or row.get("NER", "")
        ingredients = parse_ingredients_field(raw)
        text = normalize(" ".join(str(i) for i in ingredients))

        if not text:
            continue

        # ── Count existing spice hits ──────────────────────────────────────
        padded = " " + text + " "
        found_any = False
        for canonical, pat in existing_patterns:
            if pat.search(padded):
                existing_spice_counter[canonical] += 1
                found_any = True

        # ── Extract candidate ngrams ───────────────────────────────────────
        # Strip out words we know are not spices, then look for ngrams
        # that might be unknown spices
        ngrams = extract_ngrams(text, max_n=3)
        for ng in ngrams:
            if ng in canonical_set:
                continue  # already known
            if looks_like_spice(ng):
                # Make sure it's not a substring match of a known spice
                candidate_counter[ng] += 1


def write_report(total_recipes, existing_counter, candidate_counter, canonical_set):
    lines = []

    lines.append("=" * 70)
    lines.append("  SPICERACK — SPICE AUDIT REPORT")
    lines.append("=" * 70)
    lines.append(f"\n  Total recipes scanned  : {total_recipes:,}")
    lines.append(f"  Existing spices tracked: {len(existing_counter)}")
    lines.append(f"  Candidate new spices   : {len(candidate_counter)}")

    # ── Section 1: Existing spice coverage ───────────────────────────────────
    lines.append("\n" + "─" * 70)
    lines.append("  SECTION 1: YOUR EXISTING SPICES — ranked by recipe appearances")
    lines.append("─" * 70)
    lines.append(f"  {'SPICE':<35} {'RECIPES':>10}  {'% OF DATASET':>12}")
    lines.append(f"  {'-'*35} {'-'*10}  {'-'*12}")

    for spice, count in existing_counter.most_common():
        pct = count / total_recipes * 100
        lines.append(f"  {spice:<35} {count:>10,}  {pct:>11.2f}%")

    # Spices with zero hits
    zero_hit = sorted(set(canonical_set) - set(existing_counter.keys()))
    if zero_hit:
        lines.append(f"\n  ⚠️  ZERO HITS ({len(zero_hit)} spices not found in dataset):")
        for sp in zero_hit:
            lines.append(f"     • {sp}")

    # ── Section 2: Candidate new spices ──────────────────────────────────────
    lines.append("\n" + "─" * 70)
    lines.append(f"  SECTION 2: TOP {TOP_N} CANDIDATES NOT IN YOUR LIST")
    lines.append("  (Paste this section to Claude to update spice_data.py)")
    lines.append("─" * 70)
    lines.append(f"  {'CANDIDATE TOKEN':<40} {'RECIPES':>10}  {'% OF DATASET':>12}")
    lines.append(f"  {'-'*40} {'-'*10}  {'-'*12}")

    # Filter: only show candidates that appear in enough recipes to be meaningful
    MIN_APPEARANCES = max(10, total_recipes // 10_000)
    filtered = [
        (token, count)
        for token, count in candidate_counter.most_common(TOP_N * 5)
        if count >= MIN_APPEARANCES
        and len(token) > 2
        and not all(w in NON_SPICE_WORDS for w in token.split())
    ][:TOP_N]

    for token, count in filtered:
        pct = count / total_recipes * 100
        lines.append(f"  {token:<40} {count:>10,}  {pct:>11.2f}%")

    # ── Section 3: Quick stats ────────────────────────────────────────────────
    lines.append("\n" + "─" * 70)
    lines.append("  SECTION 3: QUICK STATS")
    lines.append("─" * 70)

    if existing_counter:
        top5 = existing_counter.most_common(5)
        lines.append("\n  Top 5 most common spices in dataset:")
        for sp, count in top5:
            lines.append(f"    {sp:<35} {count:,} recipes")

        bottom5 = existing_counter.most_common()[:-6:-1]
        lines.append("\n  5 least common spices in dataset:")
        for sp, count in bottom5:
            lines.append(f"    {sp:<35} {count:,} recipes")

    lines.append("\n" + "=" * 70)
    lines.append("  END OF REPORT — paste Section 2 back to Claude to update spice_data.py")
    lines.append("=" * 70)

    # Write to file
    report_text = "\n".join(lines)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Also print to console
    print(report_text)
    print(f"\n📄 Report saved to: {OUTPUT}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_audit()
