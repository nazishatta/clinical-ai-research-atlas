"""Clinical AI Research Atlas: a frozen corpus, three connected modalities."""
from __future__ import annotations
import json
from pathlib import Path
import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.motion import animated_html, animated_network_html
from src.live_network import build_live_network_html
from src.clustered_network import build_clustered_network_html
from src.analysis import SIGNALS, annual_counts, build_graph, filter_works, graph_ranking, signal_shares, term_frequencies, topic_shares_by_period, topic_shares_by_year, representative_papers
from src.palette import CATEGORICAL
from src.evidence import apply_evidence_filters, papers_for_author, papers_for_pair, population_counts, export_columns, reading_table
from src.author_topics import NO_HIGHLIGHT, MUTED_FILL, author_topic_profiles, authors_in_topic, hover_text
from src import state
from src import summaries

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Clinical AI Research Atlas',page_icon='◈',layout='wide')
st.markdown('''<style>
.block-container {max-width:1400px;padding-top:2rem;}
h1,h2,h3 {letter-spacing:-.025em;}
[data-testid="stMetric"] {background:#1B222C;border:1px solid #435064;border-radius:12px;padding:14px;}
[data-testid="stCaptionContainer"] p {color:#CBD5E1;}
a {color:#96E2D2;}
@media(max-width:700px){.block-container {padding:1rem;} h1 {font-size:1.8rem;}}
</style>''',unsafe_allow_html=True)
px.defaults.template='plotly_dark'
# Colour-blind-safe categorical palette; see src/palette.py for the contrast and CVD checks.
COLORS=CATEGORICAL
px.defaults.color_discrete_sequence=COLORS

@st.cache_data
def load_data():
    p=ROOT/'data/processed'
    return (pd.read_json(p/'works.jsonl',lines=True,convert_dates=False),json.loads((p/'topics.json').read_text()),
            json.loads((p/'audit.json').read_text()),json.loads((p/'retrieval_manifest.json').read_text()))

@st.cache_data
def cached_graph(records_json: str, minimum: int):
    from io import StringIO
    return build_graph(pd.read_json(StringIO(records_json),orient='records'),minimum)

def chart(fig, description: str, table: pd.DataFrame, key: str, selectable: bool = False, summary: str | None = None):
    fig.update_layout(font={'size':14},paper_bgcolor='#101318',plot_bgcolor='#1B222C',
                      margin={'l':35,'r':20,'t':65,'b':45},legend_title_text='')
    # The HTML reveal is decorative and cannot send Plotly selection events back to Streamlit.
    # Keep the native chart for any evidence-selection chart, even when motion is enabled.
    animate = st.session_state.get('motion_enabled', True) and key in {
        'annual_works', 'signal_shares', 'document_terms', 'topic_distribution', 'coauthorship', 'collaborator_ranking', 'community_sizes'
    } and not (table.empty and key != 'coauthorship')
    if animate:
        motion_fig = go.Figure(fig)
        if key == 'annual_works' and 'Works' in table:
            motion_fig.update_yaxes(range=[0, max(1, float(table['Works'].max()) * 1.1)])
        elif key == 'signal_shares':
            motion_fig.update_yaxes(range=[0, 100])
        elif key == 'community_sizes' and 'Researchers' in table.columns:
            motion_fig.update_xaxes(range=[0, max(1, float(table['Researchers'].max()) * 1.2)])
        elif key == 'collaborator_ranking':
            metric = st.session_state.get('rank_measure', 'Team-normalized strength')
            if metric in table.columns:
                motion_fig.update_xaxes(range=[0, max(1, float(table[metric].max()) * 1.15)])
        elif key in {'document_terms', 'topic_distribution'}:
            col = 'Documents' if key == 'document_terms' else 'Works'
            if col in table:
                motion_fig.update_xaxes(range=[0, max(1, float(table[col].max()) * 1.1)])
        alt_text = summary or str(fig.layout.title.text or key.replace('_', ' '))
        st.iframe(animated_network_html(motion_fig) if key == 'coauthorship' else animated_html(motion_fig, auto_loop=(key == 'signal_shares')), height=int(motion_fig.layout.height or 500) + 120, alt=alt_text)
        if selectable:
            if key == 'annual_works':
                st.caption('Choose years in the sidebar under Selected chart years to filter papers. The animated chart displays the same annual counts.')
            else:
                if key == 'document_terms':
                    st.caption('Select a term using Evidence selection → Selected term in the sidebar. This animation does not capture clicks.')
                elif key == 'topic_distribution':
                    st.caption('Select topics using Evidence selection → Selected chart topics in the sidebar. This animation does not capture clicks.')
                else:
                    st.caption('Animated preview above. Select the native chart below to filter evidence.')
        else:
            st.caption('The chart animates once when it scrolls into view. Use Pause/Resume, Replay or Show final values above it; with reduced motion turned on in your system settings, final values show at once.')
    event = (st.plotly_chart(fig,width='stretch',key=key,
                             on_select='rerun' if selectable else 'ignore',
                             selection_mode='points') if (selectable and key not in {'annual_works', 'document_terms', 'topic_distribution'}) or not animate else None)
    if summary:
        st.markdown(f'**In short:** {summary}')
    st.markdown(description)
    with st.expander('Accessible data table · '+key.replace('_',' ')):
        st.dataframe(table,width='stretch',hide_index=True)
    return event

def reset_filters(start_year: int, end_year: int):
    state.reset_filters(st.session_state,start_year,end_year)

def clear_chart_selections():
    state.clear_chart_selections(st.session_state)

if not (ROOT/'data/processed/works.jsonl').exists():
    st.error('Prepared corpus is missing. Run the documented fetch and build commands first.');st.stop()
works,topics,audit,manifest=load_data()
scope=manifest['scope'];topic_names={t['id']:t['label'] for t in topics}
# One fixed colour per topic, shared by every topic chart.
topic_colours={name:COLORS[i%len(COLORS)] for i,name in enumerate(topic_names.values())}
st.caption('RESEARCH INTELLIGENCE / OPENALEX SNAPSHOT')
st.title('Clinical AI Research Atlas')
st.markdown('**When did the literature change, what language distinguishes it, and who collaborated?**')
st.caption('A search-defined exploration of clinical prediction and decision support, 2016–2025. Descriptive evidence, not an assessment of clinical safety.')
with st.sidebar:
    st.header('Explore the corpus')
    st.caption('Animated charts play once when they scroll into view and have Pause/Resume, Replay and Show final values buttons. If your system asks for reduced motion, charts show their final values immediately.')
    years=st.slider('Publication years',scope['start_year'],scope['end_year'],(scope['start_year'],scope['end_year']),key='years')
    chosen_signals=st.multiselect('Trustworthiness signals',list(SIGNALS),key='signals',help='Title/abstract term matches. Multiple selections use OR. These overlap and are not quality labels.')
    selected_topic=st.selectbox('NMF topic',['All topics']+list(topic_names.values()),key='topic')
    st.caption('Topics are fixed across years. Labels use automatic top terms; human interpretation review remains pending.')
    st.button('Reset all filters',on_click=reset_filters,args=(scope['start_year'],scope['end_year']))
    st.caption('Reset clears every filter and selection (years, signals, topic, evidence filters, selected paper, focus author, author pair, community). Network display settings are kept.')
    st.markdown('#### Evidence selection')
    st.caption('OR within a category; AND between categories. Chart clicks override the corresponding sidebar evidence selection until cleared. Author focus never silently filters the corpus.')
    evidence_years=st.multiselect('Selected chart years',list(range(scope['start_year'],scope['end_year']+1)),key='evidence_years')
    evidence_topics=st.multiselect('Selected chart topics',list(topic_names),format_func=lambda x:topic_names[x],key='evidence_topics')
    evidence_term=st.text_input('Selected term (exact token or bigram)',key='evidence_term')
    st.button('Clear chart selections',on_click=clear_chart_selections)
    st.divider()
    st.caption('Views share one selection. Text needs ≥30 abstract words; networks need identified authors.')
topic_id=next((k for k,v in topic_names.items() if v==selected_topic),None)
selected=filter_works(works,years,chosen_signals,topic_id)
selected=apply_evidence_filters(selected, st.session_state.get('chart_pick_year') or evidence_years, st.session_state.get('chart_pick_topic') or evidence_topics, st.session_state.get('chart_pick_term') or evidence_term.strip() or None)
pop=population_counts(selected)
text_selected=selected[selected.text_eligible]
authors={a['id'] for values in selected.authors for a in values}
topic_assigned=int(text_selected.topic.isin(list(topic_names)).sum())
c1,c2,c3,c4,c5=st.columns(5)
c1.metric('Selected works',f'{len(selected):,}');c2.metric('Text-eligible works',f'{len(text_selected):,}')
c3.metric('Topic-assigned works',f'{topic_assigned:,}');c4.metric('Network-eligible works',f"{pop['network_eligible']:,}")
c5.metric('Snapshot works',f'{len(works):,}')
st.caption(f"Selection: {years[0]}–{years[1]} · {' OR '.join(chosen_signals) if chosen_signals else 'all signals / no restriction'} · {selected_topic} · chart years: {st.session_state.get('chart_pick_year') or evidence_years or 'all'} · chart topics: {st.session_state.get('chart_pick_topic') or evidence_topics or 'all'} · term: {st.session_state.get('chart_pick_term') or evidence_term or 'none'} · {pop['unique_authors']:,} identified authors")
with st.expander('Export current evidence selection',expanded=False):
    st.download_button('Download selected evidence (CSV)',export_columns(selected).to_csv(index=False),'selected_evidence.csv','text/csv',key='download_evidence')
    st.caption('This export contains exactly the records counted in Selected works. Author focus is separate.')
tabs=st.tabs(['Overview','Research Evolution','Research Language','Collaboration Network','Synthesis & Methods'])

with tabs[0]:
    st.subheader('One corpus. Three connected perspectives.')
    st.write(scope['question'])
    st.markdown('**Time-series** tracks publication activity. **Text** reveals language and model-derived themes. **Networks** preserve documented coauthorship relationships.')
    if selected.empty:
        st.info('No works match. Widen the years or clear a filter.')
    else:
        counts=annual_counts(selected,*years);peak=counts.loc[counts.Works.idxmax()]
        st.markdown(f"**Observed activity:** the highest annual count in this selection is **{int(peak.Works):,} works in {int(peak.Year)}**. Ties use the earliest year. This describes retrieved records, not the entire clinical-AI field.")
        st.markdown(f"**Text coverage:** **{len(text_selected):,}/{len(selected):,}** selected works meet the abstract-length rule. Missing text can change the apparent theme mix.")
        st.markdown('#### Inspect the evidence')
        st.dataframe(selected.sort_values(['year','id'],ascending=[False,True]).head(8)[['title','year','type','doi']],hide_index=True,width='stretch',column_config={'doi':st.column_config.LinkColumn('DOI')})
    st.markdown('#### How to explore')
    st.write('Use the sidebar to filter research papers by publication year, trustworthiness signal, or topic. Explore publication trends in Research Evolution, discover key terms and abstracts in Research Language, and investigate coauthor communities in Collaboration Network. Your filters remain active across tabs.')

with tabs[1]:
    st.subheader('Publication activity and language over time')
    counts=annual_counts(selected,*years)
    fig=px.bar(counts,x='Year',y='Works',color_discrete_sequence=COLORS,title='Annual works in the selected corpus')
    fig.update_xaxes(dtick=1);fig.update_yaxes(rangemode='tozero')
    year_event=chart(fig,'Bars count unique eligible works. Zero means no retained records, not proof of no research. All years are completed calendar years. Use Selected chart years in the sidebar to filter works by year.',counts,'annual_works',selectable=True,summary=summaries.annual_works(counts))
    if year_event and year_event.selection.points:
        chosen=int(year_event.selection.points[0]['x'])
        if st.session_state.get('chart_pick_year') != [chosen]:
            st.session_state['chart_pick_year']=[chosen]
            st.rerun()
    shares=signal_shares(selected,*years)
    fig=px.line(shares,x='Year',y='Share (%)',color='Signal',line_dash='Signal',markers=True,color_discrete_sequence=COLORS,custom_data=['Works','Denominator'],title='Trends in Clinical AI Trustworthiness')
    fig.update_traces(hovertemplate='%{x}: %{y:.1f}%<br>%{customdata[0]} of %{customdata[1]} text-eligible works<extra>%{fullData.name}</extra>')
    fig.update_yaxes(range=[0,100]);fig.update_xaxes(dtick=1)
    chart(fig,'Signals use term rules in titles/abstracts. Categories overlap; shares need not total 100%. Missing denominators appear as gaps. A signal filter conditions these shares on that selection.',shares,'signal_shares',summary=summaries.signal_shares(shares))
    with st.expander('Full-corpus abstract coverage by year'):
        st.dataframe(pd.DataFrame(audit['by_year']),hide_index=True,width='stretch')

with tabs[2]:
    st.subheader('Research language, with papers behind the terms')
    st.caption(f'{len(text_selected):,} text-eligible selected works. NMF was fitted once on the full text-eligible snapshot; filters do not refit it.')
    frequency=term_frequencies((text_selected.title+' '+text_selected.abstract).tolist())
    if frequency.empty:st.info('No usable terms in this selection.')
    else:
        fig=px.bar(frequency.sort_values('Documents'),x='Documents',y='Term',orientation='h',height=600,color_discrete_sequence=COLORS,title='Terms by number of selected documents')
        term_event=chart(fig,'A term counts at most once per document. English stop words are removed; unigrams/bigrams are included. Select a term from the Evidence selection sidebar control.',frequency,'document_terms',selectable=True,summary=summaries.document_terms(frequency))
        if term_event and term_event.selection.points:
            term=str(term_event.selection.points[0]['y'])
            if st.session_state.get('chart_pick_term')!=term:
                st.session_state['chart_pick_term']=term
                st.rerun()
    dist=text_selected.groupby('topic').size().rename('Works').reset_index();dist['Topic']=dist.topic.map(topic_names).fillna('Unassigned')
    if not dist.empty:
        # NMF_TOPIC_CIRCLE_PACKING_V1: a single one-shot animated visual, not duplicate bars.
        from src.topic_bubbles import topic_bubbles_html
        st.markdown('#### NMF topic distribution')
        topic_summary=summaries.topic_distribution(dist[['Topic','Works']])
        st.iframe(topic_bubbles_html(dist[['Topic','Works']].to_dict(orient='records'),topic_colours),
                  height=750, alt='Topic bubble chart. '+topic_summary)
        st.markdown(f'**In short:** {topic_summary}')
        st.caption('Each circle represents one fixed NMF topic; circle area is proportional to assigned papers. '
                   'Topic labels are provisional, not clinically validated categories. '
                   'Use Evidence selection → Selected chart topics to filter supporting papers.')
        with st.expander('Accessible data table · topic distribution'):
            st.dataframe(dist[['Topic','Works']].sort_values('Works',ascending=False),
                         hide_index=True,width='stretch')
    st.markdown('#### How the topic mix changed over time')
    topic_view=st.radio('Topic-mix view',['Pooled periods (stable)','Every year'],horizontal=True,key='topic_view',
                        help='Pooled periods merge sparse early years until each period has at least 30 text-eligible works. '
                             'Every year shows all years, with small samples marked.')
    if topic_view=='Every year':
        topic_shares=topic_shares_by_year(text_selected,topic_names,*years)
    else:
        topic_shares=topic_shares_by_period(text_selected,topic_names,*years)
    topics_present=topic_shares.loc[topic_shares.Works>0,'Topic'].nunique() if not topic_shares.empty else 0
    if topics_present<2 and not text_selected.empty:
        st.info('The topic-mix-over-time chart needs at least two topics. Clear the NMF topic or chart-topic filter to see it.')
    elif not topic_shares.empty and topic_shares.Period.nunique()>=2:
        # Axis labels carry the period and its sample size. Labels such as "2020" alone would be
        # read by Plotly as numbers, so the "n=" suffix also keeps the axis categorical.
        small=topic_shares.get('Small sample',pd.Series(False,index=topic_shares.index)).fillna(False).astype(bool)
        plot_shares=topic_shares.assign(Label=topic_shares.Period+'<br>n='+topic_shares.Denominator.map('{:,}'.format)+small.map({True:'*',False:''}))
        label_order=list(dict.fromkeys(plot_shares.Label))
        fig=px.bar(plot_shares,x='Label',y='Share (%)',color='Topic',pattern_shape='Topic',color_discrete_map=topic_colours,
                   category_orders={'Label':label_order,'Topic':list(topic_names.values())},
                   custom_data=['Period','Works','Denominator'],height=540,
                   title='Share of text-eligible works by NMF topic'+(' · every year' if topic_view=='Every year' else ' · pooled periods'))
        fig.update_traces(hovertemplate='%{customdata[0]}: %{y:.1f}%<br>%{customdata[1]} of %{customdata[2]} works<extra>%{fullData.name}</extra>',
                          marker_line_color='#101318',marker_line_width=1)
        fig.update_yaxes(range=[0,100],ticksuffix='%')
        fig.update_xaxes(type='category',title_text='Period (n = text-eligible works)')
        fig.update_layout(legend={'orientation':'h','y':-0.25})
        if topic_view=='Every year':
            note=('Each bar is one year and sums to 100% of that year\'s text-eligible works. '
                  '* marks years with fewer than 30 works, where one or two papers can move a share by several points. '
                  'A year with n=0 has no bar. ')
        else:
            note=('Each bar is one period and sums to 100% of its text-eligible works (n under the bar). '
                  'Years with few works are pooled until a period has at least 30, so early shares are not driven by a handful of papers. ')
        chart(fig,note+'Shares describe this retrieved, text-eligible corpus, not the whole field. '
                  'Topics are fixed NMF assignments with automatic labels; read the representative papers below before naming a trend.',
              topic_shares[['Period','Topic','Works','Denominator','Share (%)']],'topic_shares',summary=summaries.topic_shares(topic_shares))
    with st.expander('Representative papers for each topic · read these before interpreting a topic'):
        st.caption('The papers the NMF model ranks as most representative of each topic, from the full snapshot (filters do not change them). '
                   'Topic labels stay provisional until these are reviewed.')
        st.dataframe(representative_papers(works,topics),hide_index=True,width='stretch',
                     column_config={'Source':st.column_config.LinkColumn('Source')})
    if not text_selected.empty:
        title_lookup=text_selected.set_index('id').title.to_dict()
        paper_id=st.selectbox('Read a selected paper',text_selected.id.tolist(),format_func=lambda wid:title_lookup[wid],key='paper',index=None,placeholder='Choose a paper to read its abstract')
        if paper_id is not None and paper_id in title_lookup:
            record=text_selected[text_selected.id==paper_id].iloc[0]
            st.markdown('#### '+record.title)
            st.caption(f"{record.year} · {topic_names.get(record.topic,'Unassigned')} · normalized dominant NMF weight {record.topic_weight_share:.2f} (not a probability)")
            st.write(record.abstract);st.link_button('Open source record',record.id)
    with st.expander('Topic evaluation · initialization stability, not semantic validation'):
        st.dataframe(pd.DataFrame(audit['topic_evaluation']),hide_index=True,width='stretch')
        st.write('Three candidate counts, five seeds, aligned component cosine and top-term overlap. Smallest converged candidate with mean cosine ≥0.90 is selected provisionally. Human topic/relevance reviews remain pending; review sheets are bundled.')

with tabs[3]:
    # LARGE_MOVING_COMMUNITIES_V1 - independent of the 60-author ranked view.
    st.markdown('### Research Communities')
    # Topic-aware layer: who in the selected corpus publishes in which NMF topic.
    author_profiles=author_topic_profiles(selected,topic_names)
    author_hover=hover_text(author_profiles)
    highlight_label=st.selectbox('Highlight a research topic on the networks',[NO_HIGHLIGHT]+list(topic_names.values()),key='highlight_topic',
                                 help='Fills authors who have at least one selected, topic-assigned paper in the topic; others turn grey. '
                                      'Borders keep the collaboration-community colour. Physics and layout are unchanged.')
    highlight=None; highlight_colour=None
    if highlight_label!=NO_HIGHLIGHT:
        topic_authors=authors_in_topic(author_profiles,highlight_label)
        highlight={author:(author in topic_authors) for author in author_profiles['Author ID']}
        highlight_colour=topic_colours[highlight_label]
        st.caption(f'{len(topic_authors):,} of {len(author_profiles):,} selected authors have at least one topic-assigned paper in '
                   f'{highlight_label}. Fill = in this topic (grey = not); border = collaboration community. '
                   'Having a paper in a topic is not the same as specialising in it; see the author topic profiles below.')
    st.caption('Visualizes documented coauthorship within the selected corpus. The large view includes single-paper edges and samples connected components; community colors are algorithmic, not subject labels.')
    dense_limit=st.slider('Researchers in large cluster view',100,600,350,50,key='large_cluster_limit')
    dense_labels=st.checkbox('Show all author names on the large cluster graph',value=False,key='large_cluster_names',help='Off by default: only the 12 most-connected authors are named. Hover any node for its name.')
    from src.dense_clusters import display_subgraph, moving_community_html
    dense_graph=cached_graph(selected[['id','authors']].to_json(orient='records'),1)
    dense_view=display_subgraph(dense_graph,dense_limit)
    if dense_view.number_of_edges():
        dense_html, dense_community_count=moving_community_html(dense_view,dense_labels,highlight,highlight_colour,author_hover)
        st.caption(f'Large view: {len(dense_view):,}/{len(dense_graph):,} authors; {dense_view.number_of_edges():,}/{dense_graph.number_of_edges():,} real collaboration edges; {dense_community_count} displayed-graph communities.')
        st.iframe(dense_html,height=880,alt=summaries.network(len(dense_view),dense_view.number_of_edges(),dense_community_count,'Moving community network'))
        st.caption('Drag and zoom to explore. Nodes initially form community islands and move under physics before settling; distance is not a measured similarity. Hover to identify researchers. The original ranked network and paper evidence continue below.')
    else:
        st.info('No multi-author collaborations for this selection. Clear filters or widen publication years.')
    st.divider()
    st.markdown('#### Ranked collaboration network and evidence')
    st.subheader('Who collaborated in the selected literature?')
    minimum=st.slider('Minimum shared papers per edge',1,5,2,key='shared')
    cap=st.slider('Maximum displayed authors',20,150,60,step=10,key='cap')
    graph=cached_graph(selected[['id','authors']].to_json(orient='records'),minimum);ranking=graph_ranking(graph)
    rank_measure=st.selectbox('Rank authors by',['Team-normalized strength','Collaborators'],key='rank_measure')
    ranking=ranking.sort_values([rank_measure,'Author ID'],ascending=[False,True])
    a,b,c=st.columns(3);a.metric('Selected graph nodes',len(graph));b.metric('Retained edges',graph.number_of_edges());c.metric('Isolates',len(list(nx.isolates(graph))))
    st.caption('Nodes = identified authors; edges = shared publications. Rankings describe the selected graph, not global scientific influence.')
    st.caption('Default edges require two shared papers to reduce single-paper cliques. Large teams can inflate raw degree; compare the team-normalized ranking. Isolates remain in graph totals.')
    if graph.number_of_edges()==0:st.info('No collaboration edges survive. Reduce the threshold or widen the selection.')
    else:
        focus=st.selectbox('Focus author and direct collaborators',['All authors']+ranking['Author ID'].tolist(),format_func=lambda n:n if n=='All authors' else graph.nodes[n]['name'],key='focus')
        chosen_nodes=ranking['Author ID'].head(cap).tolist() if focus=='All authors' else [focus]+sorted(graph.neighbors(focus),key=lambda n:(-graph.degree(n),n))[:cap-1]
        view=graph.subgraph(chosen_nodes).copy()
        st.caption(f'Displaying {len(view):,}/{len(graph):,} authors and {view.number_of_edges():,}/{graph.number_of_edges():,} edges. Display cap does not change rankings; focus neighborhoods may be truncated.')
        layout_name=st.radio('Layout',['Force-directed','Circular'],horizontal=True)
        communities=list(nx.community.greedy_modularity_communities(view,weight='strength')) if view.number_of_edges() else [{n} for n in view]
        render_mode=st.radio('Network experience',['Cluster islands (moving)','Live moving network (PyVis)','Plotly fixed network'],horizontal=True,help='PyVis moves and allows dragging; Plotly retains native hover/zoom. Circular layouts use fixed positions.',index=0,key='network_mode_cluster_default_v2')
        if render_mode in ('Cluster islands (moving)','Live moving network (PyVis)'):
            show_labels=st.checkbox('Show all author names (can become crowded)',value=False,key='show_network_labels',help='Off by default: only the 12 most-connected authors are named. Hover any node for its name.')
            st.caption('Hover over a node to read its author name and collaborator count. Use the author selectors below for keyboard-accessible evidence exploration.')
            st.caption('Live physics is active by default in force-directed mode. Drag authors to explore; physics settles as the network stabilizes. Switch to Circular for intentionally fixed positions.')
            network_html=(build_clustered_network_html(view,communities,COLORS,show_labels=show_labels,highlight=highlight,topic_colour=highlight_colour,extra_hover=author_hover) if render_mode=='Cluster islands (moving)' else build_live_network_html(view,communities,layout_name,COLORS,show_labels=show_labels,highlight=highlight,topic_colour=highlight_colour,extra_hover=author_hover))
            st.iframe(network_html,height=800 if render_mode=='Cluster islands (moving)' else 650,alt=summaries.network(len(view),view.number_of_edges(),len(communities),'Ranked coauthorship network'))
            st.caption('Live network: size = selected-graph collaborator count, color = detected community, edges = shared papers. Positions have no measured distance interpretation.')
        else:
            pos=nx.spring_layout(view,seed=42,weight='strength') if layout_name=='Force-directed' else nx.circular_layout(view)
            ex=[];ey=[]
            for u,v in view.edges():ex.extend([pos[u][0],pos[v][0],None]);ey.extend([pos[u][1],pos[v][1],None])
            fig=go.Figure(go.Scatter(x=ex,y=ey,mode='lines',line={'width':.7,'color':'#718096'},hoverinfo='skip',showlegend=False))
            symbols=['circle','square','diamond','triangle-up','cross','x']
            for cid,comm in enumerate(communities):
                nodes=sorted(comm)
                fig.add_trace(go.Scatter(x=[pos[n][0] for n in nodes],y=[pos[n][1] for n in nodes],mode='markers',name=f'Community {cid+1}',marker={'size':[10+2*np.sqrt(graph.degree(n)) for n in nodes],
                        'color':([highlight_colour if highlight.get(n) else MUTED_FILL for n in nodes] if highlight else COLORS[cid%len(COLORS)]),
                        'symbol':symbols[cid%len(symbols)],
                        'line':{'width':2.5 if highlight else 1,'color':COLORS[cid%len(COLORS)] if highlight else '#EDF2F7'}},
                text=[f"{graph.nodes[n]['name']}<br>{graph.degree(n)} selected-graph collaborators<br>{graph.nodes[n]['papers']} selected papers<br>{author_hover.get(n,'')}" for n in nodes],hovertemplate='%{text}<extra></extra>'))
            fig.update_layout(title='Coauthorship · selected graph, capped display',height=600,xaxis={'visible':False},yaxis={'visible':False},showlegend=len(communities)<=12)
            chart(fig,'Size encodes selected-graph collaborator count. Color/shape encode algorithmic communities of the displayed subgraph. Layout distance is not measured similarity; communities are not confirmed laboratories.',ranking.head(cap),'coauthorship',summary=summaries.network(len(view),view.number_of_edges(),len(communities),'Ranked coauthorship network'))
        st.markdown('#### Research communities · collaboration clustering')
        st.caption('Communities are detected using weighted greedy modularity on the displayed author subgraph, not on all researchers. Community membership and sizes may change with filters, ranking, author focus, and display cap. Colors are algorithmic group identifiers, not research topics or verified institutions.')
        community_rows = []
        for cid, group in enumerate(communities, start=1):
            group_nodes = sorted(group)
            community_rows.append({
                'Community': f'Community {cid}',
                'Researchers': len(group_nodes),
                'Internal collaborations': view.subgraph(group_nodes).number_of_edges(),
                'Authors': ', '.join(view.nodes[node]['name'] for node in group_nodes[:5])
                           + (' …' if len(group_nodes)>5 else ''),
            })
        community_table = pd.DataFrame(community_rows)
        if not community_table.empty:
            summary_fig = px.bar(
                community_table.sort_values('Researchers', ascending=True),
                x='Researchers', y='Community', orientation='h',
                color='Community', text='Researchers',
                hover_data=['Internal collaborations', 'Authors'],
                title='Displayed coauthor communities · group sizes',
                color_discrete_sequence=COLORS,
            )
            summary_fig.update_layout(
                height=max(320, min(850, 105+46*len(community_table))),
                showlegend=False, xaxis_title='Researchers in displayed subgraph',
                yaxis_title='',
            )
            chart(summary_fig, 'Community sizes reflect only the displayed author subgraph. Community colors do not indicate research topics.', community_table, 'community_sizes', summary=summaries.communities(community_table))
            st.dataframe(community_table, hide_index=True, width='stretch')
            community_choice=st.selectbox(
                'Explore a collaboration community',
                ['Choose a community']+community_table['Community'].tolist(),
                key='community_choice',
            )
            if community_choice!='Choose a community':
                index=int(community_choice.split()[-1])-1
                member_ids=sorted(communities[index], key=lambda node:(-view.degree(node), node))
                member_table=pd.DataFrame([
                    {'Author':view.nodes[node]['name'],
                     'Author ID':node,
                     'Collaborators in displayed graph':view.degree(node),
                     'Selected-corpus papers':view.nodes[node]['papers']}
                    for node in member_ids
                ])
                st.markdown(f'**{community_choice}: {len(member_ids)} displayed researcher(s)**')
                st.dataframe(member_table,hide_index=True,width='stretch')
                community_papers=selected[
                    selected['authors'].apply(
                        lambda listed: any(
                            isinstance(author,dict) and author.get('id') in set(member_ids)
                            for author in listed
                        ) if isinstance(listed,list) else False
                    )
                ]
                st.caption('Papers below include at least one member of this community. A paper need not be coauthored by multiple community members. Membership is restricted to the displayed graph.')
                st.write(f'**{len(community_papers):,} selected-corpus paper(s) involving these researchers**')
                st.dataframe(export_columns(community_papers),hide_index=True,width='stretch')
                st.download_button('Download community papers (CSV)',export_columns(community_papers).to_csv(index=False), f'community_{index+1}_papers.csv','text/csv',key='download_community_papers')
        else:
            st.info('No communities available for the displayed graph.')
        edges=pd.DataFrame([{'Author A':view.nodes[u]['name'],'Author B':view.nodes[v]['name'],'Shared papers':d['shared'],'Team-normalized strength':d['strength']} for u,v,d in view.edges(data=True)])
        with st.expander('Relationships and adjacency matrix'):
            st.dataframe(edges,hide_index=True,width='stretch')
            order=chosen_nodes[:40];matrix=nx.to_numpy_array(view,nodelist=order,weight='shared')
            fig=px.imshow(matrix,x=[view.nodes[n]['name'] for n in order],y=[view.nodes[n]['name'] for n in order],color_continuous_scale='Teal',title='Shared-paper adjacency · first 40 displayed authors')
            st.plotly_chart(fig,width='stretch',key='adjacency')
            st.caption('Only the first 40 displayed authors are included. Values are shared-paper counts; the relationship table is the text alternative.')
        st.markdown('#### Author and pair evidence (within current selection)')
        focus_author=st.selectbox('Inspect author papers',['None']+ranking['Author ID'].tolist(),format_func=lambda a:'No author selected' if a=='None' else graph.nodes[a]['name']+' · '+a,key='author_focus')
        if focus_author!='None':
            author_papers=papers_for_author(selected,focus_author)
            st.write(f'**{len(author_papers):,} paper(s)** associated with this author in the current selected corpus.')
            profile=author_profiles[author_profiles['Author ID']==focus_author]
            if not profile.empty:
                p=profile.iloc[0]
                st.markdown(f"**Topic profile:** {p['Topic profile']} → **{p['Classification']}**"
                            + (f" ({p['Dominant topic']})" if p['Classification']=='Dominant' else '')
                            + f" · {int(p['Topic-assigned papers'])} of {int(p['Selected papers'])} papers have a topic.")
                st.caption('Dominant = at least 2 topic-assigned papers and one topic above 50%. Mixed = no topic above 50%. '
                           'Insufficient evidence = fewer than 2 topic-assigned papers.')
            st.dataframe(reading_table(author_papers,topic_names),hide_index=True,width='stretch',
                         column_config={'Source':st.column_config.LinkColumn('Source')})
            st.download_button('Download author evidence',export_columns(author_papers).to_csv(index=False),'author_papers.csv','text/csv')
            other=st.selectbox('Inspect shared papers with another author',['None']+[a for a in ranking['Author ID'] if a!=focus_author],key='pair_author',format_func=lambda a:'Choose collaborator' if a=='None' else graph.nodes[a]['name']+' · '+a)
            if other!='None':
                common=papers_for_pair(selected,focus_author,other)
                st.write(f'**{len(common):,} shared paper(s)** in the current selected corpus. Zero means no matching shared papers in this selection, not necessarily no collaboration elsewhere.')
                st.dataframe(reading_table(common,topic_names),hide_index=True,width='stretch',
                             column_config={'Source':st.column_config.LinkColumn('Source')})
                st.download_button('Download shared-paper evidence',export_columns(common).to_csv(index=False),'author_pair_papers.csv','text/csv')
        with st.expander('Author topic profiles · every selected author, as a table'):
            st.caption('One row per author in the current selection. Topic counts use only papers with a usable abstract and an NMF topic. '
                       'Dominant needs at least 2 topic-assigned papers and one topic above 50%; exactly 50% counts as Mixed.')
            shown_profiles=author_profiles if highlight_label==NO_HIGHLIGHT else author_profiles[author_profiles[highlight_label]>0]
            st.dataframe(shown_profiles,hide_index=True,width='stretch')
            st.download_button('Download author topic profiles (CSV)',shown_profiles.to_csv(index=False),'author_topic_profiles.csv','text/csv',key='download_author_topics')
        st.markdown('#### Top 10 collaborators')
        top = ranking.head(10).copy()
        if not top.empty:
            top['Display author'] = top['Author'].astype(str)
            ranking_fig = px.bar(
                top.iloc[::-1], x=rank_measure, y='Display author',
                orientation='h', text=rank_measure,
                hover_data={'Author ID': True, 'Corpus papers': True,
                            'Collaborators': True, 'Team-normalized strength': ':.3f',
                            'Display author': False},
                title='Top authors by ' + rank_measure.lower(),
            )
            ranking_fig.update_layout(height=620, xaxis_title=rank_measure, yaxis_title='')
            ranking_fig.update_traces(textposition='outside', cliponaxis=False)
            chart(ranking_fig,
                  'Ranking describes collaboration within the selected OpenAlex corpus; '
                  'it does not measure scientific impact.', top,
                  'collaborator_ranking', summary=summaries.ranking(top, rank_measure))
        else:
            st.info('No authors match the current selection.')
        st.markdown('#### Collaborator ranking')
        st.dataframe(ranking.head(100),hide_index=True,width='stretch')

with tabs[4]:
    st.subheader('Synthesis, provenance, and interpretation boundaries')
    st.write('Read views together: time locates changes, abstracts reveal language, and coauthorship preserves contributor relationships. Descriptive associations do not establish causes or clinical model quality.')
    st.markdown('#### Three verified snapshot observations')
    full_counts=works.groupby('year').size()
    st.write(f"1. The retained corpus contains {int(full_counts.get(scope['start_year'],0)):,} works in {scope['start_year']} and {int(full_counts.get(scope['end_year'],0)):,} in {scope['end_year']}. Search/index coverage may contribute; this is not a field-wide growth estimate.")
    st.write(f"2. Usable abstracts exist for {int(works.text_eligible.sum()):,} of {len(works):,} retained works. Coverage varies across years; interpret language shifts with the coverage table.")
    st.write(f"3. The full unthresholded coauthorship graph has {audit['network_components']:,} components; its largest has {audit.get('largest_component_authors','unreported')} authors. Fragmentation describes this corpus, not the entire field.")
    st.markdown('#### What the corpus supports')
    st.write('Comparisons within this retrieved corpus; transparent term mentions; exploratory topic structure; documented coauthorship. Search terms select trustworthiness language by design, so its prevalence across all clinical AI cannot be estimated.')
    st.markdown('#### Human interpretation review')
    st.write('Relevance precision, known-paper coverage, topic labels, ambiguous identities, and final substantive conclusions require review. Supplied worksheets make these decisions auditable. No manual validation is claimed.')
    st.markdown('#### Accessibility')
    st.markdown(
        '- **Colour:** a colour-blind-safe Okabe-Ito palette, reordered for the dark theme. Every series colour has at least 3:1 '
        'contrast with the chart background, and the closest pair of the first six colours stays distinguishable under simulated '
        'protanopia, deuteranopia and tritanopia (details in `src/palette.py`).\n'
        '- **Not colour alone:** signal lines also differ by dash style, topic bars by fill pattern, network communities by marker '
        'shape, and every value is available on hover and in a table.\n'
        '- **Alt text:** every animated or embedded chart carries alt text, and each chart has an "In short" sentence stating its '
        'main point, generated from the same numbers the chart draws.\n'
        '- **Text alternatives:** each chart has an "Accessible data table" with its exact values; network views have keyboard-'
        'operable author selectors and relationship tables.\n'
        '- **Labels and motion:** charts have titles, axis labels and units. Animated bar and line charts have keyboard-operable '
        'Pause/Resume, Replay and Show final values buttons with a spoken status, and show final values at once when the system asks '
        'for reduced motion; the topic bubbles also skip their entrance animation then. The moving networks use live physics; '
        'the Circular layout and the Plotly fixed network are static alternatives.\n'
        '- **Network names:** only the 12 most-connected authors are named by default, to keep the networks readable; every name is '
        'available on hover, in the author selectors and in the tables, and "Show all author names" draws them all.\n'
        '- **Not yet verified:** full screen-reader, keyboard-only and small-screen testing.'
    )
    st.markdown('#### Retrieval and eligibility');st.code(manifest['filter'],language=None)
    st.write(f"Retrieved {manifest['retrieved_count']:,}/{manifest['expected_count']:,} candidates at {manifest['retrieved_at_utc']}. Retained {len(works):,} English article/review/preprint works after deduplication and retraction-flag exclusions. Type does not establish peer review.")
    st.write('Text needs ≥30 reconstructed abstract words. Short/missing abstracts remain in temporal and eligible network analyses. OpenAlex IDs support joins; author disambiguation can still be wrong.')
    st.write('Team-normalized edge strength adds 1/(team size − 1) per shared paper. Each author contributes total strength 1 per multi-author paper. Raw shared counts are retained. Layout seed = 42.')
    st.caption('Source: OpenAlex · https://openalex.org · https://help.openalex.org. Abstracts retain their original rights; preserve attribution and verify redistribution terms for your intended use.')
    with st.expander('Full audit and computational settings'):st.json(audit)
    export=selected[['id','doi','title','year','type','topic','topic_weight_share','author_count']]
    st.download_button('Download selected records (CSV)',export.to_csv(index=False),'selected_works.csv','text/csv')
    st.download_button('Download data audit (JSON)',json.dumps(audit,indent=2),'data_audit.json','application/json')
