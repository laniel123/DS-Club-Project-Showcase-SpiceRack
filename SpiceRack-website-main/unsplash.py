"""
unsplash.py
Fetches a photo URL for a recipe title using the Unsplash API.
Caches results in memory so we don't hit the API on every click.

NOTE: You must add your domain to the Unsplash app allowlist at:
https://unsplash.com/oauth/applications
During local development, add: localhost
"""

import urllib.request
import urllib.parse
import json

ACCESS_KEY = "n5oAXLrI1Jyo2dGik1PjYZZEvejVeY0z8s8oGBjhTL0"
_cache = {}


def get_photo_url(recipe_title: str) -> str:
    if recipe_title in _cache:
        return _cache[recipe_title]

    try:
        query = urllib.parse.quote(recipe_title + " food recipe")
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
                return photo_url
    except Exception as e:
        print(f"[unsplash] error for '{recipe_title}': {e}")

    _cache[recipe_title] = ""
    return ""
