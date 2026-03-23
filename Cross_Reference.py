# Cross_Reference.py
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import networkx as nx
import random
from DOI import get_paper_details
from utils import get_citation_class, get_y_axis_labels, generate_adjacency_heatmap

# ---------------------------------------------------------
# Data Processing
# ---------------------------------------------------------
def read_dois_from_excel(excel_file_like):
    try:
        df = pd.read_excel(excel_file_like)
        return df.iloc[:, 0].dropna().tolist()
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def fetch_all_details(dois, progress_callback=None):
    details, labels = {}, {}
    total = len(dois)
    
    for i, doi in enumerate(dois):
        if progress_callback: progress_callback(f"Fetching DOI {i+1}/{total}...")
        try:
            author, year, global_citations, references, title = get_paper_details(doi)
            
            citation_count = sum(1 for ref in references if 'DOI' in ref) 
            
            details[doi] = references
            labels[doi] = {
                "author": author, "year": year,
                "global_citations": global_citations,
                "ref_count": citation_count, "title": title
            }
        except Exception as e:
            print(f"Error fetching details for DOI {doi}: {e}")
            continue
    return details, labels

# ---------------------------------------------------------
# Cross-Reference Network
# ---------------------------------------------------------
def create_adjacency_matrix(dois, details):
    n = len(dois)
    matrix = np.zeros((n, n), dtype=int)
    doi_index = {doi: idx for idx, doi in enumerate(dois)}
    
    for i, doi in enumerate(dois):
        if doi in details:
            ref_dois = {ref['DOI'] for ref in details[doi] if 'DOI' in ref}
            for j, target_doi in enumerate(dois):
                if i != j and target_doi in ref_dois:
                    matrix[i][j] = 1
    return matrix

def build_cross_reference_network(excel_file_like, progress_callback=None):
    dois = read_dois_from_excel(excel_file_like)
    if not dois:
        if progress_callback: progress_callback("No DOIs found in Excel.")
        return None

    details, labels = fetch_all_details(dois, progress_callback)
    
    valid_dois = [d for d in dois if d in labels]
    if not valid_dois: return None
        
    adjacency_matrix = create_adjacency_matrix(valid_dois, details)
    
    G = nx.DiGraph()
    for doi in valid_dois:
        data = labels[doi]
        G.add_node(doi, 
                   author=data['author'], year=data['year'], 
                   global_citations=data['global_citations'],
                   ref_count=data['ref_count'], title=data['title'])

    n = adjacency_matrix.shape[0]
    for i in range(n):
        for j in range(n):
            if adjacency_matrix[i][j] == 1:
                # Node i references Node j
                G.add_edge(valid_dois[i], valid_dois[j])
    return G

# ---------------------------------------------------------
# Network Plots
# ---------------------------------------------------------
def get_cross_ref_plots(G, highlight_node=None):
    if not G or G.number_of_nodes() == 0:
        return None, None

    nodes = list(G.nodes())
    
    # Data Preparation
    raw_citations = [G.nodes[n].get('global_citations', 0) for n in nodes]
    y_classes = [get_citation_class(c) for c in raw_citations]
    local_citations = [G.in_degree(n) for n in nodes]

    # Determine valid years and jitter
    x_vals = []
    for node in nodes:
        try:
            x = int(G.nodes[node]['year'])
        except:
            x = 2000 # Fallback default
        x_vals.append(x + random.uniform(-0.2, 0.2))
        
    y_vals = [y + random.uniform(-0.1, 0.1) for y in y_classes]

    fig1 = go.Figure()

    # Draw Edges
    node_idx_map = {node: i for i, node in enumerate(nodes)}
    for u, v in G.edges():
        i_u, i_v = node_idx_map[u], node_idx_map[v]
        fig1.add_trace(go.Scatter(
            x=[x_vals[i_u], x_vals[i_v]], y=[y_vals[i_u], y_vals[i_v]],
            mode='lines', line=dict(color='rgba(128, 128, 128, 0.6)', width=1.0),
            hoverinfo='none', showlegend=False
        ))

    # Node Colors
    node_colors = ['#2ca02c' if c > 200 else '#1f77b4' for c in raw_citations]

    # Hover Text
    hover_texts = [
        f"<b>Title:</b> {G.nodes[n].get('title', 'N/A')}<br>"
        f"<b>Author:</b> {G.nodes[n]['author']}<br>"
        f"<b>Year:</b> {G.nodes[n]['year']}<br>"
        f"<b>Global Citations:</b> {raw_citations[i]}<br>"
        f"<b>Local Citations:</b> {local_citations[i]}"
        for i, n in enumerate(nodes)
    ]

    fig1.add_trace(go.Scatter(
        x=x_vals, y=y_vals, mode='markers',
        marker=dict(size=10, color=node_colors, line_width=1),
        hovertemplate="%{hovertext}<extra></extra>", hovertext=hover_texts,
        customdata=nodes, showlegend=False
    ))

    fig1.update_layout(
        title='Local Citation Network',
        xaxis_title='Publication Year', yaxis_title='Citation Count Range',
        hovermode='closest', showlegend=False,
        yaxis=dict(tickmode='array', tickvals=list(range(1, 22)), ticktext=list(get_y_axis_labels().values())),
        clickmode='event+select'
    )

    # Use shared heatmap logic
    fig2 = generate_adjacency_heatmap(G)

    return fig1, fig2