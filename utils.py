# utils.py
import numpy as np
import plotly.graph_objects as go
import networkx as nx
from typing import Optional, Set, Tuple, Dict, List

# ---------------------------------------------------------
# Classification
# ---------------------------------------------------------
def get_citation_class(citations: int) -> int:
    if citations < 50: return 1
    return min(int(citations // 50) + 1, 21)

def get_y_axis_labels() -> dict:
    y_labels_map = {i: f"{(i-1)*50}-{i*50}" for i in range(1, 22)}
    y_labels_map[1] = "<50"
    y_labels_map[21] = ">1000"
    return y_labels_map

def get_stable_jitter(val: int, node_str: str, scale: float = 0.3) -> float:
    """
    Generates a consistent jitter value based on the node string hash.
    This prevents nodes from "dancing" when the app re-renders.
    """
    # Hash the string to get an integer, modulo to keep it small, normalize to -1 to 1
    hash_val = (hash(str(node_str)) % 10000) / 5000.0 - 1.0
    return val + (hash_val * scale)

# ---------------------------------------------------------
# Shared Plotting Logic
# ---------------------------------------------------------
def generate_network_plot(
    G: nx.DiGraph, 
    title: str, 
    highlight_node: Optional[str] = None,
    default_color_map: dict = None,
) -> go.Figure:
    
    if not G or G.number_of_nodes() < 2:
        return go.Figure()

    # Sort nodes to ensure order is always consistent for index mapping
    nodes = sorted(G.nodes())
    
    # --- 1. Data Preparation ---
    years = [G.nodes[n].get('year', 0) for n in nodes]
    raw_citations = [G.nodes[n].get('citations', 0) for n in nodes]
    y_classes = [get_citation_class(c) for c in raw_citations]
    local_citations = [G.in_degree(n) for n in nodes]
    
    # Jitter using stable hash function
    years_j = [get_stable_jitter(y, n, 0.3) for y, n in zip(years, nodes)]
    y_j = [get_stable_jitter(y, n, 0.1) for y, n in zip(y_classes, nodes)]
    
    node_idx_map = {n: i for i, n in enumerate(nodes)}
    node_positions = {n: (years_j[i], y_j[i]) for i, n in enumerate(nodes)}

    # --- 2. Identify Neighbors and Edges ---
    neighbors: Set[str] = set()
    connected_edges: Set[Tuple[str, str]] = set()

    if highlight_node and highlight_node in G:
        neighbors = set(G.predecessors(highlight_node)) | set(G.successors(highlight_node))
        connected_edges = set(G.in_edges(highlight_node)) | set(G.out_edges(highlight_node))

    # --- 3. Draw Edges ---
    normal_edge_x, normal_edge_y = [], []
    highlight_edge_x, highlight_edge_y = [], []

    for u, v in G.edges():
        if u not in node_positions or v not in node_positions: continue
        x0, y0 = node_positions[u]
        x1, y1 = node_positions[v]
        
        if (u, v) in connected_edges:
            highlight_edge_x.extend([x0, x1, None])
            highlight_edge_y.extend([y0, y1, None])
        else:
            normal_edge_x.extend([x0, x1, None])
            normal_edge_y.extend([y0, y1, None])

    fig = go.Figure()

    # Trace 0: Normal Edges
    fig.add_trace(go.Scatter(
        x=normal_edge_x, y=normal_edge_y,
        mode='lines', line=dict(color='rgba(128, 128, 128, 0.4)', width=1.0),
        hoverinfo='none', showlegend=False, name='Edges'
    ))

    # Trace 1: Highlighted Edges (Red)
    if highlight_edge_x:
        fig.add_trace(go.Scatter(
            x=highlight_edge_x, y=highlight_edge_y,
            mode='lines', line=dict(color='red', width=2.5),
            hoverinfo='none', showlegend=False, name='Connected Edges'
        ))

    # --- 4. Draw Nodes ---
    node_colors = []
    node_sizes = []
    
    for n in nodes:
        base_color = '#88C0D0'
        if default_color_map and n in default_color_map:
            base_color = default_color_map[n]
            
        if n == highlight_node:
            node_colors.append('#FFD700') # Gold
            node_sizes.append(18)
        elif n in neighbors:
            node_colors.append('#0000FF') # Blue
            node_sizes.append(14)
        else:
            node_colors.append(base_color)
            node_sizes.append(10)

    hover_texts = [
        f"<b>Title:</b> {G.nodes[n].get('title', 'N/A')}<br>"
        f"<b>DOI:</b> {n if not str(n).startswith('ref_') else 'N/A'}<br>"
        f"<b>Year:</b> {years[i]}<br>"
        f"<b>Citations:</b> {raw_citations[i]}" 
        for i, n in enumerate(nodes)
    ]

    # Trace 2: Nodes
    fig.add_trace(go.Scatter(
        x=years_j, y=y_j, mode='markers',
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=1, color='white')),
        hovertemplate="%{hovertext}<extra></extra>", hovertext=hover_texts,
        customdata=nodes, 
        name='Nodes'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Publication Year", yaxis_title="Citation Count Range",
        yaxis=dict(tickmode='array', tickvals=list(range(1, 22)), ticktext=list(get_y_axis_labels().values())),
        height=600, showlegend=False, clickmode='event+select',
        hovermode='closest',
        dragmode='pan' # Allow panning
    )

    return fig