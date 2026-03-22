# Cross_Reference.py
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import networkx as nx
import random
from DOI import get_paper_details

# --- Added Logic: Citation Class Function ---
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
            # Modified: Unpacked global_citations (3rd return value)
            corresponding_author, publication_year, global_citations, references = get_paper_details(doi)
            
            # Existing logic for local reference count
            citation_count = sum(1 for ref in references if 'DOI' in ref) 
            
            details[doi] = references
            labels[doi] = {
                "author": corresponding_author,
                "year": publication_year,
                "citations": citation_count,
                "global_citations": global_citations, # Added: Store global citations
            }
        except Exception as e:
            print(f"Error fetching details for DOI {doi}: {e}")
            continue
    return details, labels

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
        citation_count = labels[doi]['citations']
        # Added: Pass global_citations to node
        G.add_node(doi, label=labels[doi]['author'], citing_count=citation_count, year=labels[doi]['year'], global_citations=labels[doi]['global_citations'])

    n = adjacency_matrix.shape[0]
    for i in range(n):
        for j in range(n):
            if adjacency_matrix[i][j] == 1:
                G.add_edge(valid_dois[j], valid_dois[i])
    return G

def get_cross_ref_plots(G):
    if not G or G.number_of_nodes() == 0:
        return None, None

    nodes = list(G.nodes())
    
    # --- Plot 1: Network Graph (Year vs Citation Count) ---
    
    # 1. Calculate Positions (X=Year, Y=Citation Count)
    valid_years = []
    for node in G.nodes():
        try:
            year_int = int(G.nodes[node]['year'])
            valid_years.append(year_int)
        except:
            continue
            
    min_valid_year = min(valid_years) if valid_years else 2000
    invalid_year_x = min_valid_year - 5

    x_vals = []
    y_vals = []
    
    # Added: Logic to bin citations and create Y-values
    raw_citations = [G.nodes[n].get('global_citations', 0) for n in nodes]
    y_classes = [get_citation_class(c) for c in raw_citations]

    for i, node in enumerate(nodes):
        # X-axis: Year
        try:
            x = int(G.nodes[node]['year'])
        except:
            x = invalid_year_x
        x_vals.append(x + random.uniform(-0.2, 0.2))
        
        # Y-axis: Citation Class
        y = y_classes[i]
        y_vals.append(y + random.uniform(-0.1, 0.1))

    fig1 = go.Figure()

    node_idx_map = {node: i for i, node in enumerate(nodes)}
    
    for u, v in G.edges():
        i_u = node_idx_map[u]
        i_v = node_idx_map[v]
        
        fig1.add_trace(go.Scatter(
            x=[x_vals[i_u], x_vals[i_v]],
            y=[y_vals[i_u], y_vals[i_v]],
            mode='lines',
            line=dict(color='rgba(100,100,100,0.2)', width=1),
            hoverinfo='none',
            showlegend=False
        ))

    local_citations = [G.in_degree(n) for n in nodes]
    
    hover_texts = [
        f"Author: {G.nodes[n]['label']}<br>"
        f"Year: {G.nodes[n]['year']}<br>"
        f"Global Citations: {raw_citations[i]}<br>" # Added: Show global citations in hover
        f"Local Citations: {local_citations[i]}"
        for i, n in enumerate(nodes)
    ]

    fig1.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='markers',
        marker=dict(
            size=10,
            color=local_citations, 
            colorscale='Viridis',
            showscale=False, # Kept False as per previous request
            line_width=1
        ),
        hovertext=hover_texts,
        hoverinfo='text',
        showlegend=False
    ))

    # Added: Y-axis label mapping
    y_labels_map = {i: f"{(i-1)*50}-{i*50}" for i in range(1, 21)}
    y_labels_map[1] = "<50"
    y_labels_map[21] = ">1000"

    fig1.update_layout(
        title='Local Citation Network',
        xaxis_title='Publication Year',
        yaxis_title='Citation Count Range', # Updated Title
        hovermode='closest',
        xaxis=dict(showgrid=True, zeroline=True, showticklabels=True),
        # Modified: Y-axis ticks to match bins
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 16)),
            ticktext=list(y_labels_map.values()),
            showgrid=True, 
            zeroline=True
        ),
        showlegend=False,
    )

    # --- Plot 2: Heatmap Matrix ---
    n = len(nodes)
    matrix = np.zeros((n, n), dtype=int)
    node_idx = {node: i for i, node in enumerate(nodes)}
    
    for u, v in G.edges():
        if u in node_idx and v in node_idx:
            matrix[node_idx[u], node_idx[v]] = 1
        
    labels = [f"{G.nodes[n].get('label','?')} ({G.nodes[n].get('year','?')})" for n in nodes]
    
    fig2 = go.Figure(data=go.Heatmap(
        z=matrix,
        x=labels,
        y=labels,
        colorscale='Blues',
        showscale=False,
        showlegend=False
    ))
    
    fig2.update_layout(
        title="Cross-Reference Matrix",
        xaxis=dict(tickangle=90, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10)),
        height=700, width=700,
    )

    return fig1, fig2