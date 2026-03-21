# Local_Reference.py
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import time
import random
import mplcursors

from DOI import extract_doi_from_pdf, get_paper_details, get_referenced_dois

def get_citation_class(citations):
    if citations < 20:
        return 1
    elif citations < 40:
        return 2
    elif citations < 60:
        return 3
    elif citations < 80:
        return 4
    elif citations < 100:
        return 5
    elif citations < 120:
        return 6
    elif citations < 140:
        return 7
    elif citations < 160:
        return 8
    elif citations < 180:
        return 9
    elif citations < 200:
        return 10
    elif citations < 300:
        return 11
    elif citations < 400:
        return 12
    elif citations < 500:
        return 13
    elif citations < 1000:
        return 14
    else: # >= 1000
        return 15

def build_reference_network(pdf_path):
    try:
        main_doi = extract_doi_from_pdf(pdf_path)
        print(f"Main DOI: {main_doi}")
    except ValueError as e:
        print(e)
        return None

    G = nx.DiGraph()

    try:
        main_author, main_year, main_citations, _ = get_paper_details(main_doi)
        G.add_node(main_doi, author=main_author or "Unknown", year=main_year or 0, 
                   citations=main_citations, is_main=True)
    except Exception as e:
        print(f"Error fetching main paper: {e}")
        return None

    try:
        _, _, _, main_refs = get_paper_details(main_doi)
        ref_dois = get_referenced_dois(main_refs)
    except Exception:
        ref_dois = []

    valid_refs = []
    print(f"Processing {len(ref_dois)} references")
    
    for doi in ref_dois:
        try:
            time.sleep(0.4) # Be polite to API
            author, year, cites, _ = get_paper_details(doi)
            G.add_node(doi, author=author or "Unknown", year=year or 0, 
                       citations=cites, is_main=False)
            G.add_edge(main_doi, doi)
            valid_refs.append(doi)
        except Exception:
            continue

    print("Checking cross-references among valid references")
    for doi in valid_refs:
        try:
            time.sleep(0.4)
            _, _, _, sources = get_paper_details(doi)
            cited = get_referenced_dois(sources)
            for c in cited:
                if c in valid_refs:
                    G.add_edge(doi, c)
        except Exception:
            continue
            
    return G

def plot_networks(G):
    if not G or G.number_of_nodes() < 2:
        print("Not enough data to plot.")
        return

    fig1, ax = plt.subplots(figsize=(14, 10))
    nodes = list(G.nodes())
    
    years = [G.nodes[n].get('year', 0) for n in nodes]
    raw_citations = [G.nodes[n].get('citations', 0) for n in nodes]

    y_classes = [get_citation_class(c) for c in raw_citations]
    
    years_j = [y + random.uniform(-0.3, 0.3) for y in years]

    y_j = [y + random.uniform(-0.1, 0.1) for y in y_classes]
    
    main_node = nodes[0]
    
    for u, v in G.edges():
        i_u, i_v = nodes.index(u), nodes.index(v)
        
        if u == main_node:
            linestyle = '-'
            color = 'purple'
            alpha = 0.3
        else:
            linestyle = '--'
            color = 'gray'
            alpha = 0.4
            
        ax.plot([years_j[i_u], years_j[i_v]], [y_j[i_u], y_j[i_v]], 
                color=color, linestyle=linestyle, alpha=alpha, zorder=1)

    colors = ['#FF4444' if G.nodes[n].get('is_main') else '#88C0D0' for n in nodes]
    scatter = ax.scatter(years_j, y_j, c=colors, s=100, zorder=2)

    hover_texts = []
    for i, n in enumerate(nodes):
        txt = (f"DOI: {n}\n"
               f"Author: {G.nodes[n].get('author')}\n"
               f"Year: {years[i]}\n"
               f"Citations: {raw_citations[i]}")
        hover_texts.append(txt)
    
    cursor = mplcursors.cursor(scatter, hover=True)
    @cursor.connect("add")
    def on_add(sel):
        sel.annotation.set_text(hover_texts[sel.index])
        sel.annotation.get_bbox_patch().set(fc="lightyellow", alpha=0.9)

    y_labels_map = {
        1: "<20",
        2: "20-40",
        3: "40-60",
        4: "60-80",
        5: "80-100",
        6: "100-120",
        7: "120-140",
        8: "140-160",
        9: "160-180",
        10: "180-200",
        11: "200-300",
        12: "300-400",
        13: "400-500",
        14: "500-1000",
        15: ">1000"
    }

    ax.set_yticks(range(1, 16))

    ax.set_yticklabels([y_labels_map[i] for i in range(1, 16)], fontsize=9)

    ax.set_ylim(0.5, 15.5)

    ax.set_title("Citation Network")
    ax.set_xlabel("Publication Year")
    ax.set_ylabel("Citation Count Range") 
    ax.grid(True, linestyle=':', alpha=0.5)
    fig1.tight_layout()
    
    plot_cross_reference_matrix(G)

    plt.show()

def plot_cross_reference_matrix(G):
    nodes = list(G.nodes())
    n = len(nodes)
    matrix = np.zeros((n, n), dtype=int)
    node_idx = {n: i for i, n in enumerate(nodes)}
    
    for u, v in G.edges():
        if u in node_idx and v in node_idx:
            matrix[node_idx[u], node_idx[v]] = 1
            
    labels = [f"{G.nodes[n].get('author','?')} ({G.nodes[n].get('year','?')})" for n in nodes]
    
    plt.figure(figsize=(10, 8))
    
    sns.heatmap(matrix, cmap='Blues', xticklabels=labels, yticklabels=labels, linewidths=0.5, linecolor='gray')
    
    plt.title("Cross-Reference Matrix")
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=8)
    plt.tight_layout()