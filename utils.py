# utils.py
import numpy as np
import plotly.graph_objects as go
import networkx as nx

# ---------------------------------------------------------
# Classification
# ---------------------------------------------------------
def get_citation_class(citations: int) -> int:
    """
    Maps citation count to a class interval (1-21).
    Logic: <50=1, <100=2, ..., <1000=20, >=1000=21
    """
    if citations < 50:
        return 1
    # Math: 50-99 -> 2, ..., 950-999 -> 20. 1000+ -> 21.
    return min(int(citations // 50) + 1, 21)

def get_y_axis_labels() -> dict:
    """Generates standard Y-axis label map for plots."""
    y_labels_map = {i: f"{(i-1)*50}-{i*50}" for i in range(1, 22)}
    y_labels_map[1] = "<50"
    y_labels_map[21] = ">1000"
    return y_labels_map

# ---------------------------------------------------------
# Shared Plotting Logic
# ---------------------------------------------------------
def generate_adjacency_heatmap(G: nx.DiGraph) -> go.Figure:
    """Generates an adjacency matrix heatmap from a graph."""
    nodes = list(G.nodes())
    n = len(nodes)
    if n == 0:
        return go.Figure()

    matrix = np.zeros((n, n), dtype=int)
    node_idx = {node: i for i, node in enumerate(nodes)}
    
    for u, v in G.edges():
        if u in node_idx and v in node_idx:
            matrix[node_idx[u], node_idx[v]] = 1
            
    labels = [f"{G.nodes[n].get('author','?')} ({G.nodes[n].get('year','?')})" for n in nodes]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix, x=labels, y=labels, colorscale='Blues',
        showscale=False, showlegend=False
    ))
    
    fig.update_layout(
        title="Adjacency Matrix",
        xaxis=dict(tickangle=90, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10)),
        height=700, width=700
    )
    return fig