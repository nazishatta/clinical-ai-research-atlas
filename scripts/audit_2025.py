"""Audit the observed 2025 rise without claiming its cause."""
from __future__ import annotations
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def count_query(task):
 name,query,field,year=task
 filt=f'from_publication_date:{year}-01-01,to_publication_date:{year}-12-31,language:en,type:article|review|preprint,is_retracted:false,{field}:{query}'
 url='https://api.openalex.org/works?'+urllib.parse.urlencode({'filter':filt,'per_page':1,'select':'id'})
 try:
  with urllib.request.urlopen(url,timeout=40) as r: payload=json.load(r)
  return {'variant':name,'year':year,'filter':filt,'count':payload['meta']['count'],'status':'success'}
 except Exception as exc:
  return {'variant':name,'year':year,'filter':filt,'count':None,'status':type(exc).__name__ + (f':HTTP_{exc.code}' if isinstance(exc,urllib.error.HTTPError) else '')}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--query-variants',action='store_true');args=parser.parse_args()
 D=pd.read_json(ROOT/'data/processed/works.jsonl',lines=True,convert_dates=False)
 scope=json.loads((ROOT/'configs/study_scope.json').read_text());folder=ROOT/'docs/spike_audit';folder.mkdir(exist_ok=True)
 yearly=D.groupby('year').size(); types=pd.crosstab(D.year,D.type)
 types.to_csv(folder/'document_types_by_year.csv')
 month=D.assign(month=pd.to_datetime(D.date,errors='coerce').dt.strftime('%Y-%m')).groupby('month').size().rename('Works').reset_index();month.to_csv(folder/'publication_months.csv',index=False)
 title_duplicates=D[D.title.str.lower().duplicated(keep=False)].sort_values('title')
 title_duplicates[['id','title','year','doi']].to_csv(folder/'repeated_titles.csv',index=False)
 text_duplicates=D[D.text_eligible & D.abstract.duplicated(keep=False)]
 text_duplicates[['id','title','year','doi']].to_csv(folder/'repeated_abstracts.csv',index=False)
 lookup={}
 for page in (ROOT/'data/raw/snapshot_final_20261022').glob('page_*.json'):
  for w in json.loads(page.read_text())['results']:
   lookup.setdefault(w['id'],w)
 rows=[]
 for row in D.itertuples():
  w=lookup[row.id];location=w.get('primary_location') or {}; source=location.get('source') or {}
  rows.append({'id':row.id,'year':row.year,'source_id':source.get('id') or 'unknown','source':source.get('display_name') or 'Unknown'})
 sources=pd.DataFrame(rows);table=sources.groupby(['year','source_id','source']).size().rename('Works').reset_index();table.to_csv(folder/'sources_by_year.csv',index=False)
 top5=set(sources[sources.year==2025].source_id.value_counts().head(5).index)
 without=sources[~sources.source_id.isin(top5)].groupby('year').size()
 stats={'baseline_2024':int(yearly.get(2024,0)),'baseline_2025':int(yearly.get(2025,0)),
        'ratio_2025_to_2024':float(yearly.get(2025,0)/yearly.get(2024,1)),
        'article_only_2024':int(types.loc[2024,'article']),'article_only_2025':int(types.loc[2025,'article']),
        'excluding_top5_2025_sources_2024':int(without.get(2024,0)),'excluding_top5_2025_sources_2025':int(without.get(2025,0)),
        'top5_source_ids_excluded':sorted(top5),'duplicate_title_rows':len(title_duplicates),'duplicate_abstract_rows':len(text_duplicates),
        'indexing_date_analysis':'NOT POSSIBLE: created/updated dates were not selected in the frozen snapshot',
        'retrieved_at_utc':datetime.now(timezone.utc).isoformat()}
 if args.query_variants:
  trust='(calibration OR explainability OR uncertainty OR interpretability)'
  ai='("machine learning" OR "artificial intelligence")'
  variants=[('baseline',scope['query'],'title_and_abstract.search'),
            ('prediction_only','"clinical prediction" AND '+ai+' AND '+trust,'title_and_abstract.search'),
            ('decision_support_only','"clinical decision support" AND '+ai+' AND '+trust,'title_and_abstract.search'),
            ('title_only',scope['query'],'title.search')]
  tasks=[(name,q,field,year) for name,q,field in variants for year in [2024,2025]]
  with ThreadPoolExecutor(max_workers=3) as pool: result=list(pool.map(count_query,tasks))
  (folder/'query_variants.json').write_text(json.dumps(result,indent=2));pd.DataFrame(result).to_csv(folder/'query_variants.csv',index=False)
  stats['query_variant_status']='See query_variants.json; new API count queries, not a manually screened corpus'
 (folder/'summary.json').write_text(json.dumps(stats,indent=2))
 lines=['# Investigation of the 2025 rise','',f"Frozen retained corpus: **{stats['baseline_2024']} works (2024)** and **{stats['baseline_2025']} (2025)**; ratio **{stats['ratio_2025_to_2024']:.2f}**.",'',
 '## What the actual records establish','',f"- Article-only counts: {stats['article_only_2024']} → {stats['article_only_2025']}. Preprints/reviews alone therefore do not account for the increase.",
 f"- Excluding the five largest 2025 source-ID groups from BOTH years: {stats['excluding_top5_2025_sources_2024']} → {stats['excluding_top5_2025_sources_2025']}. This is a sensitivity check, not a defensible revised sampling rule.",
 f"- Exact case-normalized repeated-title rows: {stats['duplicate_title_rows']}; exact repeated abstract rows among eligible text records: {stats['duplicate_abstract_rows']}. Inspect the CSVs; matching titles do not prove duplicate works.",
 '- Source and monthly distributions are supplied as CSV. Source concentration can be inspected without assigning unsupported journal-quality labels.','',
 '## What remains unresolved','',
 'The snapshot did not retain created/updated indexing timestamps. It cannot determine whether publication growth, newly indexed sources, indexing backfill, evolving terminology, or relevance differences caused the rise. Original dates, versions, and source records need review.',
 'Query-variant counts, where requested and successful, are API metadata counts on the new query date. They use language/type/retraction filters but not the frozen DOI deduplication; do not compare them as perfectly identical populations.',
 'Relevance and topic review are still required, particularly a stratified comparison of 2024 versus 2025. Known relevant papers should be assembled independently of these results.',
 '', '## Defensible presentation wording','',
 '> Within this query-defined frozen corpus, retained 2025 records outnumber 2024 records by roughly three to one. The increase persists in article-only counts. Its cause and its representativeness of clinical-AI research remain unverified.',
 '', 'Do not call this an acceleration in the whole clinical-AI field. Do not claim that similar query-variant ratios establish absence of coverage bias.']
 (ROOT/'docs/2025_SPIKE_AUDIT.md').write_text('\n'.join(lines))
 print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
