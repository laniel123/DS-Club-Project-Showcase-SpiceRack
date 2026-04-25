import requests
import cv2
import numpy as np
from pyzbar.pyzbar import decode

OFF_API = "https://world.openfoodfacts.org/api/v2/product/{barcode}?fields=product_name"


def lookup_barcode(barcode: str) -> str | None:
    """Hit Open Food Facts with the barcode. Returns product name or None."""
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
        return name if name else None
    except requests.RequestException:
        return None


def scan_image(image_bytes: bytes) -> dict:
    """
    Called by app.py's /scan_barcode route.

    Takes raw bytes from request.files['barcode_image'].read()
    Returns a dict:
        success  (bool) — True if a spice name was found and ready to insert
        name     (str)  — lowercased spice name to insert into DB (or None)
        message  (str)  — user-facing feedback string
    """
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {"success": False, "name": None, "message": "Could not read image. Upload a JPG or PNG."}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    barcodes = decode(gray)
    if not barcodes:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        barcodes = decode(cv2.filter2D(gray, -1, kernel))

    if not barcodes:
        return {"success": False, "name": None, "message": "No barcode found. Try a clearer or closer photo."}

    barcode_str = barcodes[0].data.decode("utf-8").strip()
    name = lookup_barcode(barcode_str)

    if name:
        return {
            "success": True,
            "name": name.lower(),
            "message": f"Added: {name}"
        }
    else:
        return {
            "success": False,
            "name": None,
            "message": f"Barcode read ({barcode_str}) but product not found. Add the spice name manually."
        }
