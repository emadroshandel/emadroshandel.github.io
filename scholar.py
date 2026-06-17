import json
import os
import requests

SERPAPI_KEY = os.environ.get('SERPAPI_KEY')
AUTHOR_ID = 'd1Wqu9wAAAAJ'


def fetch_with_serpapi():
    """Fetch citation data via SerpApi's Google Scholar Author endpoint."""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_scholar_author",
        "author_id": AUTHOR_ID,
        "api_key": SERPAPI_KEY
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    result = resp.json()

    if "error" in result:
        raise Exception(result["error"])

    table = result.get("cited_by", {}).get("table", [])
    graph = result.get("cited_by", {}).get("graph", [])

    # table is a list of single-key dicts, e.g.:
    # [ {"citations": {"all": 535, "since_2021": 478}},
    #   {"h_index":   {"all": 12,  "since_2021": 11}},
    #   {"i10_index": {"all": 13,  "since_2021": 11}} ]
    # Build a flat lookup keyed by stat name instead of relying on index order.
    stats = {}
    for entry in table:
        for key, val in entry.items():
            stats[key] = val

    def get_all(key):
        return stats.get(key, {}).get("all", 0)

    def get_since(key):
        return stats.get(key, {}).get("since_2021", 0)

    data = {
        "citations":       get_all("citations"),
        "citations_since": get_since("citations"),
        "h_index":         get_all("h_index"),
        "h_index_since":   get_since("h_index"),
        "i10_index":       get_all("i10_index"),
        "i10_index_since": get_since("i10_index"),
        "yearly": {str(point["year"]): point["citations"] for point in graph}
    }

    return data


# ── Main ──
print("Fetching citation data via SerpApi...")

try:
    data = fetch_with_serpapi()
    print(f"SerpApi succeeded: {data['citations']} citations, h-index {data['h_index']}, i10-index {data['i10_index']}")

    with open('scholar.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("scholar.json updated successfully:")
    print(json.dumps(data, indent=2))

except Exception as e:
    print(f"SerpApi failed: {e}")
    print("Keeping existing scholar.json unchanged")
    exit(0)
