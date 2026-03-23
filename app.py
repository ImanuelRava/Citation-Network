# app.py
import streamlit as st
import streamlit.components.v1 as components
import tempfile
import os
import Local_Reference
import Forward_Reference
import Cross_Reference

st.set_page_config(page_title="Research Network Builder", layout="wide")

st.title("📚 Research Network Visualizer")

st.markdown("""
Upload a **PDF** to analyze its citation network, or an **Excel file** (list of DOIs) to cross-reference multiple papers.
""")

# --- Helper Function for Interactive Plotting ---
def show_interactive_plot(fig):
    div_id = "network_plot"
    html_string = fig.to_html(include_plotlyjs='cdn', div_id=div_id)
    
    # JavaScript to handle immediate interaction
    # 1. Identifies connected nodes via edges.
    # 2. Restores original color (from meta) for connected nodes.
    # 3. Fades out unconnected nodes.
    js_script = f"""
    <script>
    var plotDiv = document.getElementById('{div_id}');
    
    plotDiv.on('plotly_click', function(data){{
        var selectedNode = data.points[0].customdata; 
        
        var connectedNodes = new Set();
        connectedNodes.add(selectedNode);
        
        var edgeUpdates = {{ 'line.color': [], 'line.width': [] }};
        var edgeIndices = [];
        
        var traces = plotDiv.data;
        
        // 1. Process Edges to find neighbors and style edges
        for(var i = 0; i < traces.length; i++){{
            var trace = traces[i];
            
            if(trace.mode === 'lines' && trace.meta && trace.meta.length === 2){{
                var u = trace.meta[0];
                var v = trace.meta[1];
                
                edgeIndices.push(i);
                
                if(u === selectedNode || v === selectedNode){{
                    edgeUpdates['line.color'].push('rgba(255, 0, 0, 1.0)');
                    edgeUpdates['line.width'].push(2.5);
                    connectedNodes.add(u);
                    connectedNodes.add(v);
                }} else {{
                    edgeUpdates['line.color'].push('rgba(200, 200, 200, 0.2)');
                    edgeUpdates['line.width'].push(1);
                }}
            }}
        }}
        
        // Apply Edge Updates
        Plotly.restyle(plotDiv, edgeUpdates, edgeIndices);
        
        // 2. Process Nodes to style nodes (Fade unconnected)
        for(var i = 0; i < traces.length; i++){{
            var trace = traces[i];
            if(trace.mode === 'markers' && trace.customdata){{
                var newColors = [];
                
                for(var j = 0; j < trace.customdata.length; j++){{
                    var nodeId = trace.customdata[j];
                    if(connectedNodes.has(nodeId)){{
                        // Connected Node: Restore original color from 'meta'
                        if(trace.meta && trace.meta[j]){{
                             newColors.push(trace.meta[j]);
                        }} else {{
                             // Fallback if meta is missing
                             newColors.push('#1f77b4'); 
                        }}
                    }} else {{
                        // Unconnected Node: Fade to light gray
                        newColors.push('rgba(211, 211, 211, 0.4)'); 
                    }}
                }}
                
                Plotly.restyle(plotDiv, {{'marker.color': [newColors]}}, i);
                break; 
            }}
        }}
    }});
    </script>
    """
    
    components.html(html_string + js_script, height=650)

# --- File Uploader Logic ---
uploaded_file = st.file_uploader(
    "Choose a file",
    type=['pdf', 'xlsx', 'xls'],
    help="Select a PDF or Excel file"
)

if uploaded_file is not None:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext == '.pdf':
        analysis_mode = st.selectbox(
            "Select Analysis Mode:",
            ("Reference Network (Backward)", "Citation Network (Forward)")
        )
        
        st.info(f"Processing PDF in {analysis_mode} mode...")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        status_placeholder = st.empty()
        def update_status(msg):
            status_placeholder.info(msg)

        # --- Logic Branching ---
        if analysis_mode == "Reference Network (Backward)":
            G, suggestions = Local_Reference.build_reference_network(tmp_path, progress_callback=update_status)
            plot_func = Local_Reference.get_network_plots
        else: # Forward
            G, suggestions = Forward_Reference.build_forward_network(tmp_path, progress_callback=update_status)
            plot_func = Forward_Reference.get_network_plots
        
        os.unlink(tmp_path)
        
        if G:
            status_placeholder.success("Processing Complete!")
            st.write(f"**Nodes found:** {G.number_of_nodes()}")
            
            fig_net, fig_mat = plot_func(G, highlight_node=None)
            
            tab1, tab2 = st.tabs(["Citation Network", "Cross-Reference Matrix"])
            
            with tab1:
                if fig_net:
                    show_interactive_plot(fig_net)
                else:
                    st.warning("Not enough data for plot.")
                    
            with tab2:
                if fig_mat:
                    st.plotly_chart(fig_mat, use_container_width=True)

            # --- Suggestions ---
            st.divider()
            if suggestions:
                st.subheader("📚 Recommended Articles")
                
                for i, paper in enumerate(suggestions):
                    title = paper.get('title', 'Unknown Title')
                    st.markdown(f"**{i+1}. {title}**")
                    
                    source_tag = paper.get('source', '')
                    if "Recent" in source_tag: color = "green"
                    elif "Local" in source_tag: color = "blue"
                    else: color = "gray"

                    st.caption(f":{color}[{source_tag}]")
                    st.caption(f"Author: {paper.get('author', 'N/A')} | Year: {paper.get('year', 'N/A')} | Citations: {paper.get('citations', 0)}")
                    if paper.get('doi'):
                        st.caption(f"DOI: [{paper['doi']}](https://doi.org/{paper['doi']})")
                    st.markdown("---")
            else:
                st.info("No suggestions found for this paper.")
        else:
            st.error("Could not build network. Ensure the PDF contains a valid DOI.")

    elif file_ext in ['.xlsx', '.xls']:
        st.info("Processing Excel file... fetching data for each DOI.")
        
        status_placeholder = st.empty()
        def update_status(msg):
            status_placeholder.info(msg)
            
        G = Cross_Reference.build_cross_reference_network(uploaded_file, progress_callback=update_status)
        
        if G:
            status_placeholder.success("Processing Complete!")
            st.write(f"**Papers processed:** {G.number_of_nodes()}")
            
            fig_net, fig_mat = Cross_Reference.get_cross_ref_plots(G, highlight_node=None)
            
            tab1, tab2 = st.tabs(["Network Graph", "Adjacency Matrix"])
            
            with tab1:
                if fig_net:
                    show_interactive_plot(fig_net)
                else:
                    st.warning("Not enough data for plot.")
                    
            with tab2:
                if fig_mat:
                    st.plotly_chart(fig_mat, use_container_width=True)
        else:
            st.error("No valid DOIs processed. Check your Excel file column.")
            
    else:
        st.error("Unsupported file format.")