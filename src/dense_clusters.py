"""Connected, moving coauthor community explorer (view-only; no invented edges)."""
from __future__ import annotations
import json
import math
from html import escape
import networkx as nx
from pyvis.network import Network

from src.palette import CATEGORICAL as PALETTE

def display_subgraph(graph: nx.Graph, limit: int = 350) -> nx.Graph:
    """Select connected components, then highest-strength nodes within each; never fabricate links."""
    if not 50 <= limit <= 800:
        raise ValueError('limit must be between 50 and 800')
    # Keep the largest real components, spending the capacity across communities.
    comps = [set(c) for c in nx.connected_components(graph) if len(c) >= 2]
    comps.sort(key=lambda c: (-len(c), min(map(str,c))))
    chosen = []
    # Prefer connected component coverage rather than globally highest-degree isolated cliques.
    for comp in comps:
        available = limit - len(chosen)
        if available <= 0: break
        # Include entire smaller components; for giant components, take a connected BFS sample.
        if len(comp) <= available:
            chosen.extend(sorted(comp, key=str))
        else:
            seed = max(comp, key=lambda n:(graph.degree(n,weight='strength'),graph.degree(n),str(n)))
            seen = {seed}; queue = [seed]; idx=0
            while idx < len(queue) and len(seen)<available:
                n=queue[idx];idx+=1
                neighbors=sorted((v for v in graph.neighbors(n) if v in comp and v not in seen),key=lambda v:(-graph.degree(v,weight='strength'),-graph.degree(v),str(v)))
                for v in neighbors:
                    if len(seen)>=available:break
                    seen.add(v);queue.append(v)
            chosen.extend(queue)
            break
    return graph.subgraph(chosen).copy()

def moving_community_html(graph: nx.Graph, display_names: bool = False) -> tuple[str,int]:
    if graph.number_of_nodes()==0:
        return '',0
    comms = (list(nx.community.greedy_modularity_communities(graph,weight='strength'))
             if graph.number_of_edges() else [set([n]) for n in graph])
    comms.sort(key=lambda c:(-len(c),min(map(str,c))))
    membership={n:k for k,group in enumerate(comms) for n in group}
    net=Network(height='850px',width='100%',bgcolor='#0b0e19',font_color='#e9edf9',cdn_resources='in_line',directed=False)
    # Community centers are display-only starting locations; link lengths have no measured meaning.
    centers={}
    for i,group in enumerate(comms):
        theta=2*math.pi*i/max(1,len(comms))
        radius=500 if len(comms)>3 else 320
        cx,cy=radius*math.cos(theta),radius*math.sin(theta)
        local=graph.subgraph(group)
        initial=(nx.spring_layout(local,weight='strength',seed=42+i,scale=80+7*math.sqrt(len(group))) if len(group)>1 else {next(iter(group)):(0,0)})
        for n,p in initial.items():centers[n]=(cx+float(p[0]),cy+float(p[1]))
    for n,d in graph.nodes(data=True):
        i=membership[n]; degree=graph.degree(n)
        name=str(d.get('name',n))
        x,y=centers[n]
        net.add_node(str(n),x=x,y=y,physics=True,
             label=name[:24] if display_names else '',
             title=(f'<b>{escape(name)}</b><br>Community {i+1}<br>'
                    f'{degree} displayed collaborators<br>{int(d.get("papers",0))} selected papers'),
             color={'background':PALETTE[i%len(PALETTE)],'border':'#f3f6ff',
                    'highlight':{'background':'#ffffff','border':PALETTE[i%len(PALETTE)]}},
             size=min(28,3.5+2.4*math.sqrt(degree)),borderWidth=0.5)
    for u,v,d in graph.edges(data=True):
        within=membership[u]==membership[v]
        net.add_edge(str(u),str(v),width=min(2,0.35+0.22*float(d.get('shared',1))),
          title=f'{int(d.get("shared",1))} shared paper(s)',
          color={'color':PALETTE[membership[u]%len(PALETTE)] if within else '#8a92b5','opacity':0.18 if within else 0.09},
          selectionWidth=2)
    net.set_options(json.dumps({
       'interaction':{'hover':True,'dragNodes':True,'dragView':True,'zoomView':True,'keyboard':True,'navigationButtons':True},
       'nodes':{'shape':'dot','font':{'color':'#f6f7ff','size':12,'strokeWidth':3,'strokeColor':'#0b0e19'}},
       'edges':{'smooth':False},
       'physics':{'enabled':True,'solver':'forceAtlas2Based',
                  'forceAtlas2Based':{'gravitationalConstant':-60,'centralGravity':0.01,'springLength':85,'springConstant':0.035,'damping':0.6,'avoidOverlap':0.6},
                  'stabilization':{'enabled':False},'minVelocity':0.12}
    }))
    html=net.generate_html(notebook=False)
    # Hide the PyVis progress overlay when physics stabilization is disabled.
    # The default HTML waits for stabilizationIterationsDone, an event that is
    # not guaranteed when stabilization.enabled is false. The fixed 0% overlay
    # obscures the otherwise functioning moving network.
    html=html.replace(
        '</head>',
        '<style id="atlas-hide-pyvis-loading">'
        '#loadingBar{display:none!important;visibility:hidden!important;}'
        '#mynetwork{opacity:1!important;visibility:visible!important;}'
        '</style></head>',
        1,
    )
    # Explicit start: the graph moves upon iframe creation, then settles naturally.
    return html,len(comms)
