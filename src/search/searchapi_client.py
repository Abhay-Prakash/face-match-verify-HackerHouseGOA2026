"""
SearchApi.io Google Lens client - genuine reverse-image search, no mocking.

Provider: SearchApi.io (https://www.searchapi.io/docs/google-lens) - NOT
SerpApi.com. Different service, different endpoint, different key. We
switched providers because SerpApi's free tier required a card on file;
SearchApi.io's did not.

Important constraint: like SerpApi, SearchApi.io's `google_lens` engine
takes a publicly reachable image URL (the `url` parameter), not raw
uploaded bytes. If your input photo is a local file, you must host it
somewhere temporarily public before calling this client.
"""

import os
import requests

SEARCHAPI_ENDPOINT = "https://www.searchapi.io/api/v1/search"


class SearchApiError(Exception):
    """Raised when the SearchApi.io request fails or returns an error payload."""


def search_by_image_url(image_url: str, api_key: str | None = None) -> dict:
    """
    Run a Google Lens reverse-image search via SearchApi.io for the given
    publicly-reachable image URL. Returns the raw parsed JSON response.
    """
    api_key = api_key or os.environ.get("SEARCHAPI_KEY")
    if not api_key:
        raise SearchApiError("SEARCHAPI_KEY not set (env var or api_key argument)")

    params = {
        "engine": "google_lens",
        "search_type": "visual_matches",
        "url": image_url,
        "api_key": api_key,
    }

    resp = requests.get(SEARCHAPI_ENDPOINT, params=params, timeout=30)

    if resp.status_code != 200:
        raise SearchApiError(f"SearchApi.io request failed: HTTP {resp.status_code} - {resp.text[:300]}")

    data = resp.json()

    if "error" in data:
        raise SearchApiError(f"SearchApi.io returned an error: {data['error']}")

    return data


def extract_visual_matches(searchapi_response: dict) -> list[dict]:
    """
    Extract the list of visual match candidates from a raw SearchApi.io
    Google Lens response. Each item typically has: title, link, source,
    thumbnail. Returns [] if no matches are present (not an error - a
    valid "no results" outcome that match_finder.py must handle).
    """
    return searchapi_response.get("visual_matches", [])
