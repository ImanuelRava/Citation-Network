# Forward_Reference.py
import networkx as nx
import plotly.graph_objects as go
import random
from datetime import datetime
from DOI import extract_doi_from_pdf, get_paper_details, get_forward_citations
from utils import get_citation_class, get_y_axis_labels, generate_adjacency_heatmap

# ---------------------------------------------------------
# Forward Citation Network
# ---------------------------------------------------------
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
    id_map = {} # Map OpenAlex ID -> Node ID (DOI or generated)

    # Add Citing Nodes
    for paper in citing_papers:
        doi = paper.get('doi')
        oaid = paper.get('id')
        
        node_id = doi if doi else f"ref_{random.randint(10000, 99999)}"
        if oaid: id_map[oaid] = node_id
            
        G.add_node(node_id, 
                   author=paper.get('author', 'Unknown'), 
                   year=paper.get('year') or 0, 
                   citations=paper.get('citations', 0), 
                   is_main=False, 
                   title=paper.get('title', 'No Title'),
                   type='citing')
        
        G.add_edge(node_id, main_doi) # Citing paper -> Main paper
        citing_nodes.append(node_id)

    # 5. Check Cross-References (Citing papers citing each other)
    if progress_callback: progress_callback("Checking cross-references...")
    
    cross_ref_count = 0
    for paper in citing_papers:
        source_oaid = paper.get('id')
        source_node = id_map.get(source_oaid)
        
        if not source_node: continue
            
        for ref_oaid in paper.get('referenced_ids', []):
            if ref_oaid in id_map:
                target_node = id_map[ref_oaid]
                if source_node != target_node and not G.has_edge(source_node, target_node):
                    G.add_edge(source_node, target_node)
                    cross_ref_count += 1

    if progress_callback: progress_callback(f"Found {cross_ref_count} cross-references.")

    # ---------------------------------------------------------
    # Analysis & Suggestions
    # ---------------------------------------------------------
    suggestions = []
    current_year = datetime.now().year
    selected_ids = set()

    # Criteria 1: Recent High Impact
    recent_papers = [
        p for p in citing_papers 
        if p.get('year') and (current_year - 2) <= p.get('year') <= current_year
    ]
    recent_papers.sort(key=lambda x: x.get('citations', 0), reverse=True)
    
    for paper in recent_papers[:5]:
        pid = paper.get('id')
        if pid in id_map:
            selected_ids.add(pid)
            suggestions.append({
                'doi': paper.get('doi'), 'title': paper.get('title', 'No Title'),
                'citations': paper.get('citations', 0), 'year': paper.get('year'),
                'author': paper.get('author'), 'source': 'Recent High Impact'
            })

    # Criteria 2: High Local Citation
    local_cite_list = []
    for paper in citing_papers:
        pid = paper.get('id')
        if pid not in selected_ids and pid in id_map:
            node_id = id_map[pid]
            local_count = G.in_degree(node_id)
            local_cite_list.append((paper, local_count))
    
    local_cite_list.sort(key=lambda x: x[1], reverse=True)
    
    for paper, count in local_cite_list[:5]:
        suggestions.append({
            'doi': paper.get('doi'), 'title': paper.get('title', 'No Title'),
            'citations': paper.get('citations', 0), 'year': paper.get('year'),
            'author': paper.get('author'), 'source': 'High Local Citation'
        })

    return G, suggestions

# ---------------------------------------------------------
# Network Plots
# ---------------------------------------------------------
def get_network_plots(G, highlight_node=None):
    if not G or G.number_of_nodes() < 2:
        return None, None

    nodes = list(G.nodes())
    
    # Data Preparation
    years = [G.nodes[n].get('year', 0) for n in nodes]
    raw_citations = [G.nodes[n].get('citations', 0) for n in nodes]
    y_classes = [get_citation_class(c) for c in raw_citations]
    local_citations = [G.in_degree(n) for n in nodes]
    
    # Jitter for visibility
    years_j = [y + random.uniform(-0.3, 0.3) for y in years]
    y_j = [y + random.uniform(-0.1, 0.1) for y in y_classes]

    fig1 = go.Figure()

    # Draw Edges
    node_idx_map = {n: i for i, n in enumerate(nodes)}
    for u, v in G.edges():
        i_u, i_v = node_idx_map[u], node_idx_map[v]
        fig1.add_trace(go.Scatter(
            x=[years_j[i_u], years_j[i_v]], y=[y_j[i_u], y_j[i_v]],
            mode='lines', line=dict(color='rgba(128, 128, 128, 0.6)', width=1.0),
            hoverinfo='none', showlegend=False
        ))

    # Node Colors
    colors = ['#FF4444' if G.nodes[n].get('is_main') else '#88C0D0' for n in nodes]
    
    # Hover Text
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
        x=years_j, y=y_j, mode='markers',
        marker=dict(size=10, color=colors),
        hovertemplate="%{hovertext}<extra></extra>", hovertext=hover_texts,
        customdata=nodes
    ))

    fig1.update_layout(
        title="Forward Citation Network",
        xaxis_title="Publication Year", yaxis_title="Citation Count Range",
        yaxis=dict(tickmode='array', tickvals=list(range(1, 22)), ticktext=list(get_y_axis_labels().values())),
        height=600, showlegend=False, clickmode='event+select'
    )

    # Use shared heatmap logic
    fig2 = generate_adjacency_heatmap(G)

    return fig1, fig2