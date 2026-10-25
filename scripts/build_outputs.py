"""Prepare a frozen corpus, quality evidence, and evaluated NMF model."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import warnings
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import NMF
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.analysis import reconstruct_abstract, signals, build_graph

def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('--snapshot',type=Path,required=True);args=parser.parse_args()
    manifest=json.loads((args.snapshot/'manifest.json').read_text())
    if not manifest['retrieval_complete']:
        raise ValueError('Refuse incomplete retrieval')
    scope=manifest['scope'];out=ROOT/'data/processed';out.mkdir(exist_ok=True,parents=True)
    rows=[]; exclusions=[]; seen_ids=set(); seen_dois=set(); candidates=[]
    for page in manifest['pages']:
        path=args.snapshot/page['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=page['sha256']:
            raise ValueError('Raw snapshot checksum mismatch')
        for work in json.loads(path.read_text())['results']:
            candidates.append(work)
            doi=(work.get('doi') or '').lower().strip()
            reason=None
            if not work.get('id'): reason='missing_work_id'
            elif work['id'] in seen_ids: reason='duplicate_work_id'
            elif doi and doi in seen_dois: reason='duplicate_doi'
            elif work.get('is_retracted'): reason='flagged_retracted'
            elif work.get('language') != scope['language']: reason='non_english_or_unknown_language'
            elif work.get('type') not in scope['eligible_types']: reason='ineligible_document_type'
            elif not scope['start_year']<=int(work.get('publication_year') or 0)<=scope['end_year']: reason='invalid_year'
            if reason:
                exclusions.append({'id':work.get('id'),'title':work.get('title'),'reason':reason});continue
            seen_ids.add(work['id'])
            if doi: seen_dois.add(doi)
            abstract=reconstruct_abstract(work.get('abstract_inverted_index'))
            authors=[{'id':a['author']['id'],'name':a['author'].get('display_name','Unknown')} for a in work.get('authorships',[]) if a.get('author',{}).get('id')]
            title=work.get('title') or ''
            rows.append({'id':work['id'],'doi':doi,'title':title,'year':int(work['publication_year']),
                         'date':work.get('publication_date'),'type':work.get('type'),'abstract':abstract,
                         'text_eligible':len(abstract.split())>=30,'abstract_available':bool(abstract),
                         'signals':signals(title+' '+abstract),'authors':authors,'author_count':len({a['id'] for a in authors}),
                         'citations_at_retrieval':work.get('cited_by_count',0)})
    df=pd.DataFrame(rows).sort_values(['year','id']).reset_index(drop=True)
    df['topic']=-1;df['topic_weight_share']=0.0
    eligible=df[df.text_eligible]; texts=(eligible.title+' '+eligible.abstract).tolist()
    extra_stop={'use','used','using','new','based','study','paper','proposed','results','method','methods','approach','model','models','data'}
    vec=TfidfVectorizer(stop_words=sorted(set(ENGLISH_STOP_WORDS)|extra_stop),min_df=3,max_df=.95,max_features=7000,ngram_range=(1,2),sublinear_tf=True)
    X=vec.fit_transform(texts); terms=vec.get_feature_names_out()
    evaluations=[]; models={}
    for k in scope['topic_counts']:
        if k>=min(X.shape): continue
        components=[]; errors=[]; converged=[]
        for seed in scope['topic_seeds']:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always',ConvergenceWarning)
                model=NMF(n_components=k,init='nndsvdar',random_state=seed,max_iter=600)
                W=model.fit_transform(X)
            components.append(model.components_);errors.append(float(model.reconstruction_err_));converged.append(not any(issubclass(w.category,ConvergenceWarning) for w in caught))
            if seed==42: models[k]=(model,W)
        base=components[0]; scores=[]; overlaps=[]
        for comp in components[1:]:
            similarity=cosine_similarity(base,comp);r,c=linear_sum_assignment(-similarity)
            scores.extend(similarity[r,c].tolist())
            for i,j in zip(r,c):
                a=set(np.argsort(base[i])[-10:]);b=set(np.argsort(comp[j])[-10:]);overlaps.append(len(a&b)/len(a|b))
        evaluations.append({'topics':k,'mean_aligned_cosine':float(np.mean(scores)),
                            'mean_top10_jaccard':float(np.mean(overlaps)), 'mean_reconstruction_error':float(np.mean(errors)),
                            'all_runs_converged':all(converged)})
    # Explicit provisional rule: smallest candidate with high initialization stability.
    choices=[v['topics'] for v in evaluations if v['mean_aligned_cosine']>=.9 and v['all_runs_converged']]
    chosen=min(choices) if choices else min(models)
    model,W=models[chosen];den=W.sum(axis=1); assignment=np.where(den>0,W.argmax(axis=1),-1)
    bootstrap=[]
    for seed in scope['topic_seeds']:
        indices=np.random.default_rng(seed).choice(X.shape[0],X.shape[0],replace=True)
        replica=NMF(n_components=chosen,init='nndsvdar',random_state=seed,max_iter=600).fit(X[indices])
        sim=cosine_similarity(model.components_,replica.components_)
        r,c=linear_sum_assignment(-sim)
        bootstrap.append({'seed':seed,'mean_aligned_cosine':float(sim[r,c].mean())})
    weight=np.divide(W.max(axis=1),den,out=np.zeros_like(den),where=den>0)
    df.loc[eligible.index,'topic']=assignment;df.loc[eligible.index,'topic_weight_share']=weight
    topics=[]
    for k in range(chosen):
        ids=np.argsort(model.components_[k])[-12:][::-1]; top=[str(terms[i]) for i in ids]
        members=np.flatnonzero(assignment==k)
        rep=members[np.argsort(W[members,k])[::-1][:5]]
        topics.append({'id':k,'label':f"T{k+1} · "+' / '.join(top[:3]),'terms':top,
                       'representative_ids':eligible.iloc[rep].id.tolist(),'label_status':'automatic_terms_not_expert_validated'})
    graph=build_graph(df);yearly=[]
    for year,group in df.groupby('year'):
        yearly.append({'year':int(year),'works':len(group),'abstract_available_pct':round(100*group.abstract_available.mean(),2),
                       'text_eligible_pct':round(100*group.text_eligible.mean(),2),'valid_author_record_pct':round(100*(group.author_count>0).mean(),2)})
    audit={'created_at_utc':datetime.now(timezone.utc).isoformat(),'candidate_records':len(candidates),'eligible_works':len(df),
           'excluded_records':len(exclusions),'exclusion_reasons':pd.Series([e['reason'] for e in exclusions]).value_counts().to_dict(),
           'abstract_available_pct':100*df.abstract_available.mean(),'text_eligible_count':int(df.text_eligible.sum()),
           'network_nodes':graph.number_of_nodes(),'network_edges':graph.number_of_edges(),
           'network_isolates':len(list(__import__('networkx').isolates(graph))),
           'network_components':__import__('networkx').number_connected_components(graph),
           'largest_component_authors':len(max(__import__('networkx').connected_components(graph),key=len,default=set())),
           'repeated_collaboration_edges':sum(d['shared']>1 for _,_,d in graph.edges(data=True)),
           'max_team_size':int(df.author_count.max()),'selected_topic_count':chosen,'topic_evaluation':evaluations,
           'topic_selection_status':'provisional_numeric_selection_pending_human_interpretability_review',
           'bootstrap_stability_fixed_vocabulary':bootstrap,
           'preprocessing':{'min_df':3,'max_df':0.95,'max_features':7000,'ngrams':[1,2],'sublinear_tf':True,'extra_stopwords':sorted(extra_stop)},
           'manual_relevance_review':'PENDING; no human labels fabricated',
           'known_paper_retrieval_review':'PENDING; independent benchmark not supplied',
           'by_year':yearly,'versions':{p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','networkx']}}
    # JSONL preserves nested authors/signals with simple, portable deserialization.
    df.to_json(out/'works.jsonl',orient='records',lines=True,force_ascii=False)
    (out/'topics.json').write_text(json.dumps(topics,indent=2));(out/'audit.json').write_text(json.dumps(audit,indent=2))
    pd.DataFrame(exclusions).to_csv(out/'exclusions.csv',index=False)
    pd.DataFrame(evaluations).to_csv(out/'topic_evaluation.csv',index=False)
    # Ten works per year; never label them automatically as manual relevance decisions.
    sample=pd.concat([g.sample(n=min(10,len(g)),random_state=42) for _,g in df.groupby('year')])
    sample[['id','title','year','abstract','doi']].assign(decision='',reason='',reviewer='').to_csv(out/'manual_review.csv',index=False)
    review_rows=[]
    for topic in topics:
        for wid in topic['representative_ids']:
            record=df[df.id==wid].iloc[0]
            review_rows.append({'topic':topic['label'],'id':wid,'title':record.title,'abstract':record.abstract,
                                'interpretability_1_to_5':'','proposed_label':'','notes':''})
    pd.DataFrame(review_rows).to_csv(out/'topic_review.csv',index=False)
    (out/'retrieval_manifest.json').write_text(json.dumps(manifest,indent=2))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='checksums.json'}
    (out/'checksums.json').write_text(json.dumps(hashes,indent=2))
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
