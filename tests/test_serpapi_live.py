"""
Run this on YOUR machine (needs real internet access).
Usage: python test_searchapi_live.py
"""

import os
import requests
from src.blockchain.chain_config import load_project_env

load_project_env()

SEARCHAPI_ENDPOINT = "https://www.searchapi.io/api/v1/search"
API_KEY = os.environ.get("SEARCHAPI_KEY")
IMAGE_URL = "https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/obama.jpg"


def main():
    params = {
        "engine": "google_lens",
        "search_type": "visual_matches",
        "url": IMAGE_URL,
        "api_key": API_KEY,
    }
    resp = requests.get(SEARCHAPI_ENDPOINT, params=params, timeout=30)
    print(f"HTTP {resp.status_code}")

    if resp.status_code != 200:
        print(resp.text[:500])
        return

    data = resp.json()
    if "error" in data:
        print(f"SearchApi.io error: {data['error']}")
        return

    matches = data.get("visual_matches", [])
    print(f"\nFound {len(matches)} visual match(es).\n")
    for i, m in enumerate(matches[:5]):
        print(f"[{i}] title={m.get('title')!r}")
        print(f"    link={m.get('link')}")
        print(f"    source={m.get('source')}")
        print()

    if not matches:
        print("No visual matches - response keys:", list(data.keys()))


if __name__ == "__main__":
    main()