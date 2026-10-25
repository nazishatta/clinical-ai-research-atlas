"""Fetch a dated OpenAlex snapshot; no credentials are bundled or logged."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from datetime import datetime, timezone
import urllib.request
import urllib.parse
import urllib.error

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True, help='New snapshot directory; must not already exist')
    args = parser.parse_args()
    scope = json.loads((ROOT/'configs/study_scope.json').read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    filt = f"from_publication_date:{scope['start_year']}-01-01,to_publication_date:{scope['end_year']}-12-31,{scope['search_field']}:{scope['query']}"
    page_number = 1
    pages = []
    expected = None
    retrieved = 0
    while True:
        params = {'filter': filt, 'per_page': 200, 'page': page_number,
                  'select': 'id,doi,title,publication_year,publication_date,type,language,authorships,abstract_inverted_index,cited_by_count,primary_location,is_retracted'}
        if os.environ.get('OPENALEX_API_KEY'):
            params['api_key'] = os.environ['OPENALEX_API_KEY']
        url = 'https://api.openalex.org/works?' + urllib.parse.urlencode(params)
        for attempt in range(4):
            try:
                req = urllib.request.Request(url, headers={'User-Agent':'ClinicalAIResearchAtlas/1.0 educational corpus audit'})
                with urllib.request.urlopen(req, timeout=60) as response:
                    data = json.load(response)
                break
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
                if attempt == 3:
                    raise RuntimeError('OpenAlex retrieval failed; retained pages are incomplete. Retry into a NEW directory.') from exc
                time.sleep(2 ** attempt)
        if expected is None:
            expected = data['meta']['count']
        page = args.output/f'page_{len(pages)+1:03d}.json'
        page.write_text(json.dumps(data, ensure_ascii=False))
        results = data.get('results', [])
        retrieved += len(results)
        pages.append({'file':page.name,'records':len(results),'sha256':hashlib.sha256(page.read_bytes()).hexdigest()})
        print(f'Page {len(pages)}: {retrieved}/{expected}', flush=True)
        page_number += 1
        if not results or retrieved >= expected:
            break
    manifest = {'retrieved_at_utc':datetime.now(timezone.utc).isoformat(), 'endpoint':'https://api.openalex.org/works',
                'filter':filt,'expected_count':expected,'retrieved_count':retrieved,
                'retrieval_complete':retrieved == expected,'pagination':'basic pages (within OpenAlex 10,000-result limit)', 'pages':pages,'scope':scope}
    (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2))
    if not manifest['retrieval_complete']:
        raise RuntimeError('Incomplete snapshot; do not interpret corpus trends.')

if __name__ == '__main__':
    main()
