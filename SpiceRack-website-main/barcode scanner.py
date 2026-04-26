import re
import requests
import cv2
import numpy as np
from pyzbar.pyzbar import decode

OFF_API = "https://world.openfoodfacts.org/api/v2/product/{barcode}?fields=product_name"

# brand names and packaging words to strip from product names
NOISE_WORDS = [
    # brands
    "olde thompson", "mccormick", "morton", "spice islands", "simply organic",
    "frontier", "badia", "lawrys", "lawry's", "trader joe", "trader joe's",
    "whole foods", "365", "kirkland", "costco", "kroger", "generic",
    # packaging
    "grinder", "shaker", "mill", "dispenser", "bottle", "jar", "container",
    "refill", "pack", "bag", "pouch", "organic", "natural", "pure", "premium",
    "gourmet", "artisan", "fresh", "ground", "whole", "crushed", "minced",
    "dried", "dehydrated", "freeze dried", "toasted",
    # geographic descriptors that aren't part of the spice name
    "mediterranean", "himalayan", "celtic", "french", "sicilian",
    "california", "spanish", "turkish", "mexican", "indian",
    # modifiers
    "coarse", "fine", "extra fine", "coarsely", "finely",
    "iodized", "non iodized", "sea", "pink", "grey", "gray",
    "smoked", "roasted",
]


def clean_product_name(name: str) -> str:
    """
    Strip brand names, packaging words, and descriptors to get the core spice.
    e.g. "Olde Thompson Mediterranean Sea Salt Grinder" → "salt"
         "McCormick Ground Cinnamon" → "cinnamon"
         "Frontier Organic Whole Cumin Seed" → "cumin seed"
    """
    cleaned = name.lower().strip()

    # remove noise words
    for word in NOISE_WORDS:
        cleaned = re.sub(rf'\b{re.escape(word)}\b', '', cleaned)

    # collapse whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # remove trailing/leading punctuation
    cleaned = cleaned.strip('.,/-')

    return cleaned if cleaned else name.lower()


def lookup_barcode(barcode: str) -> str | None:
    """Hit Open Food Facts with the barcode. Returns cleaned product name or None."""
    try:
        resp = requests.get(
            OFF_API.format(barcode=barcode),
            timeout=5,
            headers={"User-Agent": "Spicerack/1.0"}
        )
        data = resp.json()
        if data.get("status") != 1:
            return None
        name = data.get("product", {}).get("product_name", "").strip()
        if not name:
            return None
        return clean_product_name(name)
    except requests.RequestException:
        return None


def scan_image(image_bytes: bytes) -> dict:
    """
    Called by app.py's /scan_barcode route.
    Returns:
        success (bool)
        name    (str) — cleaned spice name to insert into DB
        message (str) — user-facing feedback
    """
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {"success": False, "name": None, "message": "Could not read image. Upload a JPG or PNG."}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # attempt 1 — raw
    barcodes = decode(gray)

    # attempt 2 — sharpen
    if not barcodes:
        kernel   = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        barcodes = decode(cv2.filter2D(gray, -1, kernel))

    # attempt 3 — resize 2x
    if not barcodes:
        big      = cv2.resize(gray, (gray.shape[1]*2, gray.shape[0]*2))
        barcodes = decode(big)

    if not barcodes:
        return {"success": False, "name": None, "message": "No barcode found. Try a clearer or closer photo."}

    barcode_str = barcodes[0].data.decode("utf-8").strip()
    name        = lookup_barcode(barcode_str)

    if name:
        return {
            "success": True,
            "name":    name,
            "message": f"Added: {name}"
        }
    else:
        return {
            "success": False,
            "name":    None,
            "message": f"Barcode read ({barcode_str}) but product not found. Add the spice name manually."
        }