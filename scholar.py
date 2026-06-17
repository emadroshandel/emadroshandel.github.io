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

    def get_stat(index, key):
        try:
            return table[index][key]["value"]
        except (IndexError, KeyError, TypeError):
            return 0

    data = {
        "citations":       get_stat(0, "citations"),
        "citations_since": get_stat(0, "citations") if len(table) <= 0 else table[0].get("citations", {}).get("since_2021", 0),
        "h_index":         get_stat(1, "h_index"),
        "h_index_since":   table[1].get("h_index", {}).get("since_2021", 0) if len(table) > 1 else 0,
        "i10_index":       get_stat(2, "i10_index"),
        "i10_index_since": table[2].get("i10_index", {}).get("since_2021", 0) if len(table) > 2 else 0,
        "yearly": {str(point["year"]): point["citations"] for point in graph}
    }

    return data

# ── Main ──
print("Fetching citation data via SerpApi...")

try:
    data = fetch_with_serpapi()
    print(f"SerpApi succeeded: {data['citations']} citations, h-index {data['h_index']}")

    with open('scholar.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("scholar.json updated successfully:")
    print(json.dumps(data, indent=2))

except Exception as e:
    print(f"SerpApi failed: {e}")
    print("Keeping existing scholar.json unchanged")
    exit(0)
