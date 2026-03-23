# Forward_Reference.py
import networkx as nx
import plotly.graph_objects as go
import numpy as np
import random
from datetime import datetime
from DOI import extract_doi_from_pdf, get_paper_details, get_forward_citations

def get_citation_class(citations):
    if citations < 50: return 1
    elif citations < 100: return 2
    elif citations < 150: return 3
    elif citations < 200: return 4
    elif citations < 250: return 5
    elif citations < 300: return 6
    elif citations < 350: return 7
    elif citations < 400: return 8
    elif citations < 450: return 9
    elif citations < 500: return 10
    elif citations < 550: return 11
    elif citations < 600: return 12
    elif citations < 650: return 13
    elif citations < 700: return 14
    elif citations < 750: return 15
    elif citations < 800: return 16
    elif citations < 850: return 18
    elif citations < 900: return 19
    elif citations < 950: return 20
    else: return 21

def build_forward_network(pdf_path, progress_callback=None):
    # 1. Extract Main DOI
    try:
        main_doi = extract_doi_from_pdf(pdf_path)
        if progress_callback: progress_callback(f"Main DOI found: {main_doi}")
    except ValueError as e:
        if progress_callback: progress_callback(f"Error: {e}")
        return None, []

    G = nx.DiGraph()

    # 2. Get Main Paper Details
    try:
        main_author, main_year, main_citations, _, main_title = get_paper_details(main_doi)
        G.add_node(main_doi, author=main_author or "Unknown", year=main_year or 0, 
                   citations=main_citations, is_main=True, title=main_title, type='main')
    except Exception as e:
        if progress_callback: progress_callback(f"Error fetching main paper: {e}")
        return None, []

    # 3. Get Forward Citations
    if progress_callback: progress_callback("Querying database for forward citations...")
    citing_papers = get_forward_citations(main_doi)
    
    if progress_callback: progress_callback(f"Found {len(citing_papers)} citing papers. Building network...")

    # 4. Build Network
    citing_nodes = [] 
    id_map = {} 

    # Add Citing Nodes
    for paper in citing_papers:
        doi = paper.get('doi')
        oaid = paper.get('id')
        
        if not doi:
            node_id = f"ref_{random.randint(10000, 99999)}"
        else:
            node_id = doi
            
        if oaid:
            id_map[oaid] = node_id
            
        G.add_node(node_id, 
                   author=paper.get('author', 'Unknown'), 
                   year=paper.get('year') or 0, 
                   citations=paper.get('citations', 0), 
                   is_main=False, 
                   title=paper.get('title', 'No Title'),
                   type='citing')
        
        G.add_edge(node_id, main_doi)
        citing_nodes.append(node_id)

    # 5. Check Cross-References
    if progress_callback: progress_callback("Checking cross-references...")
    
    cross_ref_count = 0
    for paper in citing_papers:
        source_id = paper.get('id')
        source_doi = id_map.get(source_id)
        
        if not source_doi:
            continue
            
        referenced_ids = paper.get('referenced_ids', [])
        
        for ref_id in referenced_ids:
            if ref_id in id_map:
                target_doi = id_map[ref_id]

                if source_doi != target_doi and not G.has_edge(source_doi, target_doi):
                    G.add_edge(source_doi, target_doi)
                    cross_ref_count += 1

    if progress_callback: progress_callback(f"Found {cross_ref_count} cross-references.")

    # ---------------------------------------------------------
    # SUGGESTION LOGIC
    # ---------------------------------------------------------
    suggestions = []
    
    current_year = datetime.now().year

    # --- CRITERIA 1: Recent High Impact Citing Papers ---
    recent_papers = []
    for paper in citing_papers:
        year = paper.get('year')
        if year and (current_year - 5) <= year <= current_year:
            recent_papers.append(paper)
    
    recent_papers.sort(key=lambda x: x.get('citations', 0), reverse=True)
    
    selected_recent_ids = set()
    for paper in recent_papers[:5]:
        node_id = id_map.get(paper.get('id'))
        if node_id and G.has_node(node_id):
            selected_recent_ids.add(paper.get('id'))
            suggestions.append({
                'doi': paper.get('doi'), 
                'title': paper.get('title', 'No Title'),
                'citations': paper.get('citations', 0),
                'year': paper.get('year'),
                'author': paper.get('author'),
                'source': 'Recent High Impact Citing Paper'
            })

    # --- CRITERIA 2: High Local Citation Papers ---
    local_cite_list = []
    for paper in citing_papers:
        pid = paper.get('id')
        if pid in selected_recent_ids:
            continue
            
        node_id = id_map.get(pid)
        if node_id and G.has_node(node_id):
            local_count = G.in_degree(node_id)
            local_cite_list.append((paper, local_count))
    
    local_cite_list.sort(key=lambda x: x[1], reverse=True)
    
    for paper, count in local_cite_list[:5]:
        node_id = id_map.get(paper.get('id'))
        suggestions.append({
            'doi': paper.get('doi'), 
            'title': paper.get('title', 'No Title'),
            'citations': paper.get('citations', 0),
            'year': paper.get('year'),
            'author': paper.get('author'),
            'source': 'High Local Citation Citing Paper'
        })

    return G, suggestions

def get_network_plots(G):
    if not G or G.number_of_nodes() < 2:
        return None, None

    nodes = list(G.nodes())
    
    main_node = None
    for n in nodes:
        if G.nodes[n].get('is_main'):
            main_node = n
            break
            
    years = [G.nodes[n].get('year', 0) for n in nodes]
    raw_citations = [G.nodes[n].get('citations', 0) for n in nodes]
    y_classes = [get_citation_class(c) for c in raw_citations]
    
    local_citations = [G.in_degree(n) for n in nodes]
    
    years_j = [y + random.uniform(-0.3, 0.3) for y in years]
    y_j = [y + random.uniform(-0.1, 0.1) for y in y_classes]

    fig1 = go.Figure()

    # Draw Edges
    for u, v in G.edges():
        i_u, i_v = nodes.index(u), nodes.index(v)
        
        if v == main_node:
            color = 'rgba(128, 0, 128, 0.3)'
            width = 1.5
        else:
            color = 'rgba(255, 165, 0, 0.1)'
            width = 1
            
        fig1.add_trace(go.Scatter(
            x=[years_j[i_u], years_j[i_v]], 
            y=[y_j[i_u], y_j[i_v]],
            mode='lines',
            line=dict(color=color, width=width),
            hoverinfo='none',
            showlegend=False
        ))

    colors = []
    for n in nodes:
        if G.nodes[n].get('is_main'):
            colors.append('#FF4444')
        else:
            colors.append('#88C0D0')
    
    # --- UPDATED: Hover Text with Local Citations ---
    hover_texts = [
        f"<b>Title:</b> {G.nodes[n].get('title', 'N/A')}<br>"
        f"<b>DOI:</b> {n if not str(n).startswith('ref_') else 'N/A'}<br>"
        f"<b>Author:</b> {G.nodes[n].get('author')}<br>"
        f"<b>Year:</b> {years[i]}<br>"
        f"<b>Global Citations:</b> {raw_citations[i]}<br>"
        f"<b>Local Citations:</b> {local_citations[i]}" 
        for i, n in enumerate(nodes)
    ]

    fig1.add_trace(go.Scatter(
        x=years_j, y=y_j,
        mode='markers',
        marker=dict(size=10, color=colors),
        hovertemplate = "%{hovertext}<extra></extra>",
        hovertext = hover_texts,
        hoverinfo = 'text'
    ))

    y_labels_map = {i: f"{(i-1)*50}-{i*50}" for i in range(1, 22)}
    y_labels_map[1] = "<50"
    y_labels_map[21] = ">1000"
    
    fig1.update_layout(
        title="Forward Citation Network",
        xaxis_title="Publication Year",
        yaxis_title="Citation Count Range",
        yaxis=dict(tickmode='array', tickvals=list(range(1, 22)), ticktext=list(y_labels_map.values())),
        height=600,
        showlegend=False
    )

    # Plot 2: Heatmap
    n = len(nodes)
    matrix = np.zeros((n, n), dtype=int)
    node_idx = {n: i for i, n in enumerate(nodes)}
    
    for u, v in G.edges():
        if u in node_idx and v in node_idx:
            matrix[node_idx[u], node_idx[v]] = 1
            
    labels = [f"{G.nodes[n].get('author','?')} ({G.nodes[n].get('year','?')})" for n in nodes]
    
    fig2 = go.Figure(data=go.Heatmap(
        z=matrix,
        x=labels,
        y=labels,
        colorscale='Blues',
        showscale=False,
        showlegend=False
    ))
    
    fig2.update_layout(
        title="Adjacency Matrix",
        xaxis=dict(tickangle=90, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10)),
        height=700,
        width=700
    )

    return fig1, fig2