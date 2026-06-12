from scholarly import scholarly
import json

author = scholarly.search_author_id('d1Wqu9wAAAAJ')
author = scholarly.fill(author, sections=['basics', 'indices'])

data = {
    "citations": author['citedby'],
    "h_index": author['hindex'],
    "i10_index": author['i10index']
}

with open('scholar.json', 'w') as f:
    json.dump(data, f)
