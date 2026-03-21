import requests
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import seaborn as sns
from DOI import extract_doi_from_pdf, get_paper_details, get_referenced_dois

def process_uploaded_pdf(pdf_path):
    """Process the uploaded PDF file to extract DOI and build a reference network."""
    main_doi = extract_doi_from_pdf(pdf_path)
    if main_doi:
        reference_network = build_reference_network(main_doi)
        plot_reference_network(reference_network)
    else:
        print("Could not extract DOI from the PDF.")

def get_all_referenced_dois(main_doi):
    """Retrieve all DOIs referenced by the main DOI."""
    try:
        _, _, _, main_references = get_paper_details(main_doi)
        return get_referenced_dois(main_references)
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def build_reference_network(main_doi):
    """Construct a directed reference network based on the main DOI."""
    G = nx.DiGraph()
    referenced_dois = get_all_referenced_dois(main_doi)

    # Main Article Node
    main_author, main_year, _, _ = get_paper_details(main_doi)
    G.add_node(main_doi, label=f"{main_author} ({main_year})", citations=0, year=main_year)

    # Referenced Articles Nodes
    for doi in referenced_dois:
        author, year, citation_count, _ = get_paper_details(doi)
        G.add_node(doi, label=f"{author} ({year})", citations=citation_count, year=year)

    # Edges
    for doi in referenced_dois:
        G.add_edge(main_doi, doi)
        try:
            _, _, _, source_references = get_paper_details(doi)
            cited_dois = get_referenced_dois(source_references)
            for cited_doi in cited_dois:
                if cited_doi in referenced_dois:
                    G.add_edge(doi, cited_doi)
        except ValueError as e:
            print(f"Could not retrieve details for DOI: {doi}. Error: {e}")

    return G

def plot_reference_network(G):
    """Visualize the reference network with citation numbers on the y-axis and years on the x-axis."""
    
    # Prepare data for plotting
    years = [G.nodes[node]['year'] for node in G.nodes()]
    citation_counts = [G.nodes[node]['citations'] for node in G.nodes()]
    labels = {node: G.nodes[node]['label'] for node in G.nodes()}

    plt.figure(figsize=(12, 8))

    # Scatter plot of nodes
    for i, node in enumerate(G.nodes()):
        plt.scatter(years[i], citation_counts[i], 
                    color='red' if node == list(G.nodes())[0] else 'blue', 
                    s=800, label=labels[node])
        plt.text(years[i], citation_counts[i], labels[node], fontsize=8, ha='right')

    # Draw edges manually
    for edge in G.edges():
        x_values = [G.nodes[edge[0]]['year'], G.nodes[edge[1]]['year']]
        y_values = [G.nodes[edge[0]]['citations'], G.nodes[edge[1]]['citations']]
        plt.plot(x_values, y_values, color='black', alpha=0.5, linestyle="-")

    plt.title("Citation Network", fontsize=14)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Citation Numbers", fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid()
    plt.show()

    plot_cross_reference_matrix(G)

def plot_cross_reference_matrix(G):
    """Generate and display a heatmap of the cross-reference matrix."""
    nodes = list(G.nodes())
    n = len(nodes)
    
    matrix = np.zeros((n, n), dtype=int)
    
    # Fill matrix with citation data
    for i, node in enumerate(nodes):
        for j, target in enumerate(nodes):
            if G.has_edge(node, target):
                matrix[i, j] = 1  # Indicator of a citation

    labels = {node: G.nodes[node]['label'] for node in nodes}

    plt.figure(figsize=(10, 10))
    sns.heatmap(matrix, annot=False, cmap='Blues', xticklabels=labels.values(), yticklabels=labels.values(), cbar=False)
    plt.title("Cross-Reference Matrix", fontsize=14)
    plt.xlabel("Cited Papers (Author Year)", fontsize=12)
    plt.ylabel("Citing Papers (Author Year)", fontsize=12)
    plt.tight_layout()
    plt.show()