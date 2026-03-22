# Local_Reference.py
import networkx as nx
import plotly.graph_objects as go
import numpy as np
import time
import random
from DOI import extract_doi_from_pdf, get_paper_details, get_referenced_dois

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
        main_author, main_year, main_citations, _ = get_paper_details(main_doi)
        G.add_node(main_doi, author=main_author or "Unknown", year=main_year or 0, 
                   citations=main_citations, is_main=True)
    except Exception as e:
        if progress_callback: progress_callback(f"Error fetching main paper: {e}")
        return None, []

    # 3. Get References of Main Paper
    try:
        _, _, _, main_refs = get_paper_details(main_doi)
        ref_dois = get_referenced_dois(main_refs)
    except Exception:
        ref_dois = []

    valid_refs = []
    total_refs = len(ref_dois)
    
    # 4. Build Network (Backward Citations)
    for i, doi in enumerate(ref_dois):
        if progress_callback: progress_callback(f"Processing reference {i+1}/{total_refs}...")
        try:
            time.sleep(0.4) 
            author, year, cites, _ = get_paper_details(doi)
            G.add_node(doi, author=author or "Unknown", year=year or 0, 
                       citations=cites, is_main=False)
            G.add_edge(main_doi, doi)
            valid_refs.append(doi)
        except Exception:
            continue

    # 5. Check Cross-References (Calculates Local Citations)
    if progress_callback: progress_callback("Checking cross-references (Local Citations)...")
    for i, doi in enumerate(valid_refs):
        try:
            time.sleep(0.4)
            _, _, _, sources = get_paper_details(doi)
            cited = get_referenced_dois(sources)
            for c in cited:
                if c in valid_refs:
                    G.add_edge(doi, c)
        except Exception:
            continue

    # ---------------------------------------------------------
    # NEW SUGGESTION LOGIC
    # ---------------------------------------------------------
    suggestions = []
    
    if progress_callback: progress_callback("Generating suggestions...")

    # Get Main Year (integer)
    try:
        main_year_int = int(main_year)
    except:
        main_year_int = 0

    # Helper to get year safely
    def get_node_year(doi):
        try:
            return int(G.nodes[doi].get('year', 0))
        except:
            return 0

    # --- CRITERIA 1: Recent High Impact References ---
    # Condition: (MainYear - 2) <= RefYear <= MainYear
    recent_refs = []
    for doi in valid_refs:
        ref_year = get_node_year(doi)
        # Check range [MainYear - 2, MainYear]
        if (main_year_int - 2) <= ref_year <= main_year_int:
            recent_refs.append(doi)
    
    # Sort by Global Citations (descending)
    recent_refs.sort(key=lambda d: G.nodes[d].get('citations', 0), reverse=True)
    
    # Select Top 5
    selected_recent = recent_refs[:5]
    for doi in selected_recent:
        node = G.nodes[doi]
        suggestions.append({
            'doi': doi,
            'title': f"Reference: {node.get('author', '?')} ({node.get('year', '?')})",
            'citations': node.get('citations', 0),
            'year': node.get('year'),
            'author': node.get('author'),
            'source': 'Recent High Impact Reference'
        })

    # --- CRITERIA 2: High Local Citation References ---
    # Exclude references already selected in Criteria 1
    remaining_refs = [d for d in valid_refs if d not in selected_recent]
    
    # Sort by Local Citations (in-degree) descending
    remaining_refs.sort(key=lambda d: G.in_degree(d), reverse=True)
    
    # Select Top 5
    selected_local = remaining_refs[:5]
    for doi in selected_local:
        node = G.nodes[doi]
        suggestions.append({
            'doi': doi,
            'title': f"Reference: {node.get('author', '?')} ({node.get('year', '?')})",
            'citations': node.get('citations', 0),
            'year': node.get('year'),
            'author': node.get('author'),
            'source': 'High Local Citation Reference'
        })

    return G, suggestions

def get_network_plots(G):
    if not G or G.number_of_nodes() < 2:
        return None, None

    # --- PLOT 1: Citation Network Scatter ---
    nodes = list(G.nodes())
    years = [G.nodes[n].get('year', 0) for n in nodes]
    raw_citations = [G.nodes[n].get('citations', 0) for n in nodes]
    y_classes = [get_citation_class(c) for c in raw_citations]
    
    # Add jitter
    years_j = [y + random.uniform(-0.3, 0.3) for y in years]
    y_j = [y + random.uniform(-0.1, 0.1) for y in y_classes]

    main_node = nodes[0]
    
    fig1 = go.Figure()

    # Draw Edges
    for u, v in G.edges():
        i_u, i_v = nodes.index(u), nodes.index(v)
        
        if u == main_node:
            color = 'rgba(128, 0, 128, 0.5)' # Purple
        else:
            color = 'rgba(128, 128, 128, 0.4)' # Gray
            
        fig1.add_trace(go.Scatter(
            x=[years_j[i_u], years_j[i_v]], 
            y=[y_j[i_u], y_j[i_v]],
            mode='lines',
            line=dict(color=color, width=1),
            hoverinfo='none',
            showlegend=False
        ))

    # Draw Nodes
    colors = ['#FF4444' if G.nodes[n].get('is_main') else '#88C0D0' for n in nodes]
    
    local_citations = [G.in_degree(n) for n in nodes]
    
    hover_texts = [
        f"DOI: {n}<br>"
        f"Author: {G.nodes[n].get('author')}<br>"
        f"Year: {years[i]}<br>"
        f"Global Citations: {raw_citations[i]}<br>"
        f"Local Citations: {local_citations[i]}" 
        for i, n in enumerate(nodes)
    ]

    fig1.add_trace(go.Scatter(
        x=years_j, y=y_j,
        mode='markers',
        marker=dict(size=10, color=colors),
        hovertext=hover_texts,
        hoverinfo='text'
    ))

    y_labels_map = {i: f"{(i-1)*50}-{i*50}" for i in range(1, 21)}
    y_labels_map[1] = "<50"
    y_labels_map[21] = ">1000"
    
    fig1.update_layout(
        title="Citation Network",
        xaxis_title="Publication Year",
        yaxis_title="Citation Count Range",
        yaxis=dict(tickmode='array', tickvals=list(range(1, 22)), ticktext=list(y_labels_map.values())),
        height=600,
        showlegend=False
    )

    # --- PLOT 2: Cross-Reference Matrix Heatmap ---
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
        title="Cross-Reference Matrix",
        xaxis=dict(tickangle=90, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10)),
        height=700,
        width=700
    )

    return fig1, fig2