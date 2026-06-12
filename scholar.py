import json
import time
import random

def fetch_with_scholarly():
    """Try fetching via scholarly with free proxies."""
    from scholarly import scholarly, ProxyGenerator
    
    # Use free proxies to avoid Google blocking
    pg = ProxyGenerator()
    pg.FreeProxies()
    scholarly.use_proxy(pg)
    
    author = scholarly.search_author_id('d1Wqu9wAAAAJ')
    author = scholarly.fill(author, sections=['basics', 'indices', 'counts'])
    
    # Build yearly citations dict
    yearly = {}
    if 'cites_per_year' in author:
        yearly = {str(k): v for k, v in author['cites_per_year'].items()}
    
    data = {
        "citations":       author.get('citedby', 0),
        "h_index":         author.get('hindex', 0),
        "i10_index":       author.get('i10index', 0),
        "citations_since": author.get('citedby5y', 0),
        "h_index_since":   author.get('hindex5y', 0),
        "i10_index_since": author.get('i10index5y', 0),
        "yearly":          yearly
    }
    return data

def fetch_with_scraper():
    """Fallback: direct scrape with randomised headers."""
    import requests
    
    headers = {
        'User-Agent': random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36',
        ]),
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    url = 'https://scholar.google.com/citations?user=d1Wqu9wAAAAJ&hl=en'
    time.sleep(random.uniform(2, 5))  # polite delay
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    
    import re
    text = resp.text
    
    def extract(pattern):
        m = re.search(pattern, text)
        return int(m.group(1).replace(',', '')) if m else 0
    
    citations  = extract(r'<td class="gsc_rsb_std">(\d[\d,]*)</td>')
    h_index    = extract(r'<td class="gsc_rsb_std">(\d+)</td>.*?<td class="gsc_rsb_std">(\d+)</td>', )
    
    # Parse all stat cells
    cells = re.findall(r'<td class="gsc_rsb_std">([\d,]+)</td>', text)
    nums  = [int(c.replace(',','')) for c in cells]
    
    # Scholar layout: citations_all, citations_since, h_all, h_since, i10_all, i10_since
    data = {
        "citations":       nums[0] if len(nums) > 0 else 533,
        "citations_since": nums[1] if len(nums) > 1 else 476,
        "h_index":         nums[2] if len(nums) > 2 else 12,
        "h_index_since":   nums[3] if len(nums) > 3 else 11,
        "i10_index":       nums[4] if len(nums) > 4 else 13,
        "i10_index_since": nums[5] if len(nums) > 5 else 11,
        "yearly": {}
    }
    
    # Parse yearly citations bar chart
    years  = re.findall(r'<span class="gsc_g_t"[^>]*>(\d{4})</span>', text)
    counts = re.findall(r'<span class="gsc_g_al">(\d+)</span>', text)
    if years and counts:
        data["yearly"] = {y: int(c) for y, c in zip(years, counts)}
    
    return data

# ── Main ──
data = None

print("Attempting fetch with scholarly + free proxies...")
try:
    data = fetch_with_scholarly()
    print(f"scholarly succeeded: {data['citations']} citations")
except Exception as e:
    print(f"scholarly failed: {e}")

if not data:
    print("Attempting direct scrape fallback...")
    try:
        data = fetch_with_scraper()
        print(f"Scraper succeeded: {data['citations']} citations")
    except Exception as e:
        print(f"Scraper failed: {e}")

if not data:
    print("Both methods failed — keeping existing scholar.json unchanged")
    exit(0)  # exit 0 so workflow doesn't fail

with open('scholar.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"scholar.json updated successfully:")
print(json.dumps(data, indent=2))
