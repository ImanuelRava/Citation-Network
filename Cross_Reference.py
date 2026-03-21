import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import networkx as nx
from DOI import get_paper_details

def read_dois_from_excel(excel_path):
    df = pd.read_excel(excel_path)
    return df.iloc[:, 0].tolist()

def fetch_all_details(dois):
    details = {}
    labels = {}
    
    for doi in dois:
        try:
            corresponding_author, publication_year, citation_count, references = get_paper_details(doi)
            details[doi] = references
            labels[doi] = f"{corresponding_author}\n({publication_year})"
        except Exception as e:
            print(f"Error fetching details for DOI {doi}: {e}")
    return details, labels

def create_adjacency_matrix(dois, details):
    n = len(dois)
    matrix = np.zeros((n, n), dtype=int)
    
    for i in range(n):
        for j in range(n):
            if i != j:  # No self-reference
                ref_dois = [ref['DOI'] for ref in details[dois[i]] if 'DOI' in ref]
                if dois[j] in ref_dois:
                    matrix[i][j] = 1
    return matrix

def plot_heatmap(matrix, labels):
    plt.figure(figsize=(10, 8))
    sns.heatmap(matrix, annot=True, fmt='d', cmap='RdYlGn', 
                xticklabels=labels.values(), yticklabels=labels.values(), cbar=False)
    plt.title('DOI Reference Adjacency Matrix')
    plt.ylabel('Citing DOIs')
    plt.xlabel('Referenced DOIs')
    plt.xticks(rotation=90, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show()

def create_network(matrix, labels):
    G = nx.DiGraph()
    label_list = list(labels.keys()) 

    for i, doi in enumerate(label_list):
        citing_count = matrix[:, i].sum()
        G.add_node(doi, label=labels[doi], citing_count=citing_count)

    n = matrix.shape[0]
    for i in range(n):
        for j in range(n):
            if matrix[i][j] == 1:
                G.add_edge(label_list[i], label_list[j])
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=0.5)

    node_colors = []
    for _, data in G.nodes(data=True):
        color = plt.cm.coolwarm(data['citing_count'] / max(1, max([d['citing_count'] for _, d in G.nodes(data=True)])))
        node_colors.append(color)
    # Draw nodes
    nx.draw(G, pos, with_labels=True, labels={doi: G.nodes[doi]['label'] for doi in G.nodes()},
            node_color=node_colors, node_size=1000, font_size=10, font_color='black')
    
    # Draw edges        
    nx.draw_networkx_edges(G, pos, alpha=0.2, edge_color='black', arrowstyle='-|>', arrowsize=10)

    plt.title('Local Citation Network')
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def main(excel_path):
    dois = read_dois_from_excel(excel_path)
    details, labels = fetch_all_details(dois)
    adjacency_matrix = create_adjacency_matrix(dois, details)
    plot_heatmap(adjacency_matrix, labels)
    create_network(adjacency_matrix, labels)

if __name__ == "__main__":
    excel_file_path = r"C:\Users\DELL\Documents\Research Project\Review\Test_DOI.xlsx"
    main(excel_file_path)