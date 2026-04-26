"""
unsplash.py
Fetches recipe photos from Unsplash API.
Caches results to data/photo_cache.json so URLs persist across restarts.
Free tier: 50 requests/hour — cached URLs never hit the API again.
"""

import json
import os
import urllib.request
import urllib.parse

ACCESS_KEY = "n5oAXLrI1Jyo2dGik1PjYZZEvejVeY0z8s8oGBjhTL0"

BASE       = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE, "data", "photo_cache.json")

# load cache from disk on startup
def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_cache(cache: dict):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"[unsplash] could not save cache: {e}")

_cache = _load_cache()
print(f"[unsplash] loaded photo cache — {len(_cache)} cached photos")


def get_photo_url(recipe_title: str) -> str:
    """
    Return a photo URL for the recipe title.
    Checks disk cache first — only hits the API if not cached.
    Saves to disk after every new fetch.
    """
    if recipe_title in _cache:
        return _cache[recipe_title]

    try:
        query = urllib.parse.quote(f"{recipe_title} food recipe")
        url   = f"https://api.unsplash.com/search/photos?query={query}&per_page=1&orientation=landscape"
        req   = urllib.request.Request(url, headers={
            "Authorization":  f"Client-ID {ACCESS_KEY}",
            "Accept-Version": "v1",
            "User-Agent":     "SpiceRack/1.0"
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            data    = json.loads(resp.read())
            results = data.get("results", [])
            if results:
                photo_url = results[0]["urls"]["regular"]
                _cache[recipe_title] = photo_url
                _save_cache(_cache)   # persist to disk immediately
                return photo_url
    except Exception as e:
        print(f"[unsplash] error for '{recipe_title}': {e}")

    # cache empty string so we don't retry failed lookups
    _cache[recipe_title] = ""
    _save_cache(_cache)
    return ""