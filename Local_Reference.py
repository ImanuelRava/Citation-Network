# Local_Reference.py
import networkx as nx
import plotly.graph_objects as go
import random
import time
from DOI import extract_doi_from_pdf, get_paper_details, get_referenced_dois
from utils import get_citation_class, get_y_axis_labels, generate_adjacency_heatmap

# ---------------------------------------------------------
# Backward Citation Network
# ---------------------------------------------------------
def build_reference_network(pdf_path, progress_callback=None):
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
        main_author, main_year, main_citations, main_refs, main_title = get_paper_details(main_doi)
        G.add_node(main_doi, author=main_author or "Unknown", year=main_year or 0, 
                   citations=main_citations, is_main=True, title=main_title)
    except Exception as e:
        if progress_callback: progress_callback(f"Error fetching main paper: {e}")
        return None, []

    # 3. Get References
    ref_dois = get_referenced_dois(main_refs) if main_refs else []
    valid_refs = []
    total_refs = len(ref_dois)
    
    # 4. Build Network
    for i, doi in enumerate(ref_dois):
        if progress_callback: progress_callback(f"Processing reference {i+1}/{total_refs}...")
        try:
            time.sleep(0.4) # Rate limiting
            author, year, cites, _, title = get_paper_details(doi)
            G.add_node(doi, author=author or "Unknown", year=year or 0, 
                       citations=cites, is_main=False, title=title)
            G.add_edge(main_doi, doi) # Main paper -> Reference
            valid_refs.append(doi)
        except Exception:
            continue

    # 5. Check Cross-References (References citing each other)
    if progress_callback: progress_callback("Checking cross-references (Local Citations)...")
    for i, doi in enumerate(valid_refs):
        try:
            time.sleep(0.4)
            _, _, _, sources, _ = get_paper_details(doi)
            cited = get_referenced_dois(sources)
            for c in cited:
                if c in valid_refs:
                    G.add_edge(doi, c) # Reference A -> Reference B
        except Exception:
            continue

    # ---------------------------------------------------------
    # Analysis & Suggestions
    # ---------------------------------------------------------
    suggestions = []
    if progress_callback: progress_callback("Generating suggestions...")

    try:
        main_year_int = int(main_year)
    except:
        main_year_int = 0

    # Criteria 1: Recent High Impact References
    recent_refs = []
    for doi in valid_refs:
        try:
            ref_year = int(G.nodes[doi].get('year', 0))
            if (main_year_int - 2) <= ref_year <= main_year_int:
                recent_refs.append(doi)
        except:
            continue
    
    recent_refs.sort(key=lambda d: G.nodes[d].get('citations', 0), reverse=True)
    selected_recent = recent_refs[:5]
    
    for doi in selected_recent:
        node = G.nodes[doi]
        suggestions.append({
            'doi': doi, 'title': node.get('title', 'No Title'),
            'citations': node.get('citations', 0), 'year': node.get('year'),
            'author': node.get('author'), 'source': 'Recent High Impact Reference'
        })

    # Criteria 2: High Local Citation References
    remaining_refs = [d for d in valid_refs if d not in selected_recent]
    remaining_refs.sort(key=lambda d: G.in_degree(d), reverse=True)
    
    for doi in remaining_refs[:5]:
        node = G.nodes[doi]
        suggestions.append({
            'doi': doi, 'title': node.get('title', 'No Title'),
            'citations': node.get('citations', 0), 'year': node.get('year'),
            'author': node.get('author'), 'source': 'High Local Citation Reference'
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
    
    # Jitter
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
        f"<b>DOI:</b> {n}<br>"
        f"<b>Author:</b> {G.nodes[n].get('author')}<br>"
        f"<b>Year:</b> {years[i]}<br>"
        f"<b>Global Citations:</b> {raw_citations[i]}<br>"
        f"<b>Local Citations:</b> {local_citations[i]}" 
        for i, n in enumerate(nodes)
    ]

    fig1.add_trace(go.Scatter(
        x=years_j, y=y_j, mode='markers',
        marker=dict(size=10, color=colors, line_width=1),
        hovertemplate="%{hovertext}<extra></extra>", hovertext=hover_texts,
        customdata=nodes
    ))

    fig1.update_layout(
        title="Backward Citation Network",
        xaxis_title="Publication Year", yaxis_title="Citation Count Range",
        yaxis=dict(tickmode='array', tickvals=list(range(1, 22)), ticktext=list(get_y_axis_labels().values())),
        height=600, showlegend=False, clickmode='event+select'
    )

    # Use shared heatmap logic
    fig2 = generate_adjacency_heatmap(G)

    return fig1, fig2