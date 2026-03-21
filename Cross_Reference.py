# Cross_Reference.py
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import networkx as nx
import mplcursors
from DOI import get_paper_details

def read_dois_from_excel(excel_path):
    try:
        df = pd.read_excel(excel_path)
        return df.iloc[:, 0].dropna().tolist()
    except Exception as e:
        print(f"Error reading Excel file {excel_path}: {e}")
        return []

def fetch_all_details(dois):
    details, labels = {}, {}
    
    print(f"Fetching details for {len(dois)} DOIs")
    for doi in dois:
        try:
            corresponding_author, publication_year, _, references = get_paper_details(doi)
            citation_count = sum(1 for ref in references if 'DOI' in ref) # Local citation count based on references
            details[doi] = references
            labels[doi] = {
                "author": corresponding_author,
                "year": publication_year,
                "citations": citation_count,
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

def build_cross_reference_network(excel_path):
    dois = read_dois_from_excel(excel_path)
    if not dois:
        print("No DOIs found.")
        return None

    details, labels = fetch_all_details(dois)
    
    valid_dois = [d for d in dois if d in labels]
    
    if not valid_dois:
        return None
        
    adjacency_matrix = create_adjacency_matrix(valid_dois, details)
    
    G = nx.DiGraph()
    
    for doi in valid_dois:
        citation_count = labels[doi]['citations']
        # Note: storing author in 'label' attribute
        G.add_node(doi, label=labels[doi]['author'], citing_count=citation_count, year=labels[doi]['year'])

    n = adjacency_matrix.shape[0]
    for i in range(n):
        for j in range(n):
            if adjacency_matrix[i][j] == 1:
                G.add_edge(valid_dois[j], valid_dois[i])
                
    return G

def plot_cross_reference_matrix(G):
    nodes = list(G.nodes())
    n = len(nodes)
    matrix = np.zeros((n, n), dtype=int)
    node_idx = {node: i for i, node in enumerate(nodes)}
    
    for u, v in G.edges():
        if u in node_idx and v in node_idx:
            matrix[node_idx[u], node_idx[v]] = 1
        
    labels = [f"{G.nodes[n].get('label','?')} ({G.nodes[n].get('year','?')})" for n in nodes]
    
    plt.figure(figsize=(10, 8))
    
    sns.heatmap(matrix, cmap='Blues', xticklabels=labels, yticklabels=labels, cbar=False, linewidths=0.5, linecolor='gray')
    
    plt.title("Cross-Reference Matrix")
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=8)
    plt.tight_layout()

def plot_cross_reference_network(G):
    if not G or G.number_of_nodes() == 0:
        print("No data to plot.")
        return

    # --- Plot 1: Network Graph ---
    plt.figure(figsize=(12, 8))
    
    # --- Positioning Logic ---
    pos = {}
    
    valid_years = []
    for node in G.nodes():
        try:
            year_int = int(G.nodes[node]['year'])
            valid_years.append(year_int)
        except (ValueError, TypeError):
            continue
            
    min_valid_year = min(valid_years) if valid_years else 0
    invalid_year_x = min_valid_year - 1

    for node in G.nodes():
        y_val = G.nodes[node]['citing_count']
        
        try:
            x_val = int(G.nodes[node]['year'])
        except (ValueError, TypeError):
            x_val = invalid_year_x
            
        pos[node] = (x_val, y_val)
    
    # --- Color and Size ---
    max_citing_count = max((data['citing_count'] for _, data in G.nodes(data=True)), default=1)

    node_colors = [
        plt.cm.coolwarm(data['citing_count'] / max(1, max_citing_count)) for _, data in G.nodes(data=True)
    ]

    nodes = nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=200)

    nx.draw_networkx_edges(G, pos, alpha=0.2, edge_color='black', arrowstyle='-|>', arrowsize=10)

    # --- Hover Tooltips ---
    tooltip_data = [
        (f'DOI: {doi}\n'
         f'Author: {G.nodes[doi]["label"]}\n'
         f'Publication Year: {G.nodes[doi]["year"]}\n'
         f'Citations: {G.nodes[doi]["citing_count"]}\n'
         f'Local Citations: {G.in_degree(doi)}')
        for doi in G.nodes()
    ]

    mplcursors.cursor(nodes).connect("add", lambda sel: sel.annotation.set_text(tooltip_data[sel.index]))

    plt.title('Local Citation Network')
    
    plt.xlabel('Publication Year')
    plt.ylabel('Citation Count')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.axis('on') 
    
    plt.tight_layout()
    plot_cross_reference_matrix(G)

    plt.show()