# app.py
import streamlit as st
import networkx as nx
import plotly.graph_objects as go

# Import your modules
from Forward_Reference import build_forward_network
from Local_Reference import build_reference_network
from Cross_Reference import build_cross_reference_network
from utils import generate_network_plot

# ---------------------------------------------------------
# Page Setup
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="Citation Network Explorer")
st.title("📚 Citation Network Explorer")

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if 'graph' not in st.session_state:
    st.session_state.graph = None
if 'graph_type' not in st.session_state:
    st.session_state.graph_type = None
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = []
if 'highlight_node' not in st.session_state:
    st.session_state.highlight_node = None

# ---------------------------------------------------------
# Sidebar: Controls
# ---------------------------------------------------------
st.sidebar.header("1. Build Network")

analysis_type = st.sidebar.radio("Select Analysis Type", [
    "Forward Citation (PDF)", 
    "Backward Reference (PDF)", 
    "Cross Reference (Excel)"
])

uploaded_file = st.sidebar.file_uploader("Upload File", type=['pdf', 'xlsx'])

# Progress placeholder in sidebar
progress_placeholder = st.sidebar.empty()

def log_progress(msg):
    """Log progress to UI and console"""
    progress_placeholder.write(f"⏳ {msg}")
    print(msg)

if st.sidebar.button("Build Network"):
    if uploaded_file is not None:
        # Reset state for new network
        st.session_state.highlight_node = None
        
        with st.spinner("Processing network..."):
            try:
                G = None
                suggestions = []
                g_type = None
                
                if analysis_type == "Forward Citation (PDF)":
                    G, suggestions = build_forward_network(uploaded_file, progress_callback=log_progress)
                    g_type = "forward"
                elif analysis_type == "Backward Reference (PDF)":
                    G, suggestions = build_reference_network(uploaded_file, progress_callback=log_progress)
                    g_type = "local"
                elif analysis_type == "Cross Reference (Excel)":
                    G = build_cross_reference_network(uploaded_file, progress_callback=log_progress)
                    suggestions = [] 
                    g_type = "cross"
                
                if G and G.number_of_nodes() > 0:
                    st.session_state.graph = G
                    st.session_state.graph_type = g_type
                    st.session_state.suggestions = suggestions
                    st.success(f"Network built! Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
                    progress_placeholder.empty() # Clear progress text
                elif G is not None and G.number_of_nodes() < 2:
                     st.warning("Network built, but too few nodes to display.")
                else:
                    st.error("Failed to build network or no data found.")
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.error(traceback.format_exc())
    else:
        st.warning("Please upload a file.")

# ---------------------------------------------------------
# Sidebar: Suggestions Display
# ---------------------------------------------------------
if st.session_state.suggestions:
    st.sidebar.header("2. Suggested Articles")
    st.sidebar.markdown("Top papers based on impact & recency:")
    
    for i, sugg in enumerate(st.session_state.suggestions):
        with st.sidebar.expander(f"{i+1}. {sugg.get('title', 'No Title')[:50]}..."):
            st.markdown(f"**Source:** {sugg.get('source', 'N/A')}")
            st.markdown(f"**Author:** {sugg.get('author', 'N/A')}")
            st.markdown(f"**Year:** {sugg.get('year', 'N/A')}")
            st.markdown(f"**Citations:** {sugg.get('citations', 0)}")
            if sugg.get('doi'):
                st.markdown(f"[View Paper](https://doi.org/{sugg.get('doi')})")

# ---------------------------------------------------------
# Main Area: Visualization
# ---------------------------------------------------------
G = st.session_state.graph
g_type = st.session_state.graph_type

if G and G.number_of_nodes() > 1:
    # Define Title and Color Map
    title = "Citation Network"
    color_map = {}
    
    if g_type == 'forward':
        title = "Forward Citation Network"
        for n in G.nodes():
            color_map[n] = '#FF4444' if G.nodes[n].get('is_main') else '#88C0D0'
    elif g_type == 'local':
        title = "Backward Reference Network"
        for n in G.nodes():
            color_map[n] = '#FF4444' if G.nodes[n].get('is_main') else '#88C0D0'
    elif g_type == 'cross':
        title = "Cross Reference Network"
        for n in G.nodes():
            color_map[n] = '#2ca02c' if G.nodes[n].get('citations', 0) > 200 else '#1f77b4'

    # Instruction
    st.info("🖱️ **Interaction:** Click a node to highlight its connections. Click the background to reset.")

    # --- Plotting ---
    # We pass the highlight_node from session_state
    fig = generate_network_plot(
        G, 
        title=title, 
        highlight_node=st.session_state.highlight_node,
        default_color_map=color_map
    )
    
    # Render chart with interactivity
    # on_select="rerun" ensures the app reloads when you click a point
    selection = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

    # Handle Click Interaction
    if selection and selection['selection'] and selection['selection']['point_indices']:
        # Get the index of the clicked point
        idx = selection['selection']['point_indices'][0]
        
        # Retrieve the sorted list of nodes used in the plot
        # We must sort nodes to ensure index matches the plot
        nodes_sorted = sorted(G.nodes())
        
        if 0 <= idx < len(nodes_sorted):
            clicked_node = nodes_sorted[idx]
            
            # Only update state if it changed to prevent unnecessary reruns
            if st.session_state.highlight_node != clicked_node:
                st.session_state.highlight_node = clicked_node
                st.rerun()
    elif selection and selection['selection'] is None:
        # If user clicked empty space (deselected)
        if st.session_state.highlight_node is not None:
            st.session_state.highlight_node = None
            st.rerun()

elif G and G.number_of_nodes() == 1:
    st.info("Only one node found. Need more data for a network.")
else:
    st.info("Upload a file and click 'Build Network' to begin.")