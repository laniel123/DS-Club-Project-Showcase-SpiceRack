import requests
import cv2
import numpy as np
from pyzbar.pyzbar import decode

OFF_API = "https://world.openfoodfacts.org/api/v2/product/{barcode}?fields=product_name,product_name_en,generic_name,brands,image_url,ingredients_text,nutriments"


def lookup_barcode(barcode: str) -> dict | None:
    try:
        resp = requests.get(
            OFF_API.format(barcode=barcode),
            timeout=5,
            headers={"User-Agent": "Spicerack/1.0"}
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != 1:
            return None

        product = data.get("product", {})

        name = (
            product.get("product_name", "").strip()
            or product.get("product_name_en", "").strip()
            or product.get("generic_name", "").strip()
        )

        if not name:
            return None

        return {
            "name": name,
            "brand": product.get("brands", "").strip() or None,
            "image_url": product.get("image_url", "").strip() or None,
            "ingredients": product.get("ingredients_text", "").strip() or None,
            "nutriments": product.get("nutriments") or None,
        }

    except (requests.RequestException, ValueError):
        return None


def preprocess_image(gray: np.ndarray) -> list:
    attempts = [gray]

    kernel_sharpen = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    attempts.append(cv2.filter2D(gray, -1, kernel_sharpen))

    attempts.append(cv2.equalizeHist(gray))

    attempts.append(cv2.GaussianBlur(gray, (3, 3), 0))

    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    attempts.append(thresh)

    return attempts


def scan_image(image_bytes: bytes) -> dict:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        return {"success": False, "name": None, "message": "Could not read image. Upload a JPG or PNG."}

    h, w = img.shape[:2]
    if w > 1920:
        scale = 1920 / w
        img = cv2.resize(img, (1920, int(h * scale)))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    barcodes = []
    for processed in preprocess_image(gray):
        barcodes = decode(processed)
        if barcodes:
            break

    if not barcodes:
        return {"success": False, "name": None, "message": "No barcode found. Try a clearer or closer photo."}

    barcode_str = barcodes[0].data.decode("utf-8").strip()

    if not barcode_str:
        return {"success": False, "name": None, "message": "Barcode detected but could not be read."}

    product = lookup_barcode(barcode_str)

    if product:
        return {
            "success": True,
            "name": product["name"].lower(),
            "message": f"Added: {product['name']}",
            "brand": product["brand"],
            "image_url": product["image_url"],
            "ingredients": product["ingredients"],
            "nutriments": product["nutriments"],
            "barcode": barcode_str,
        }
    else:
        return {
            "success": False,
            "name": None,
            "message": f"Barcode read ({barcode_str}) but product not found. Add the spice name manually.",
            "barcode": barcode_str,
        }