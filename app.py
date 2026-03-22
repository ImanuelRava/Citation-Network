# app.py
import streamlit as st
import tempfile
import os

# Import logic
import Local_Reference
import Cross_Reference

st.set_page_config(page_title="Research Network Builder", layout="wide")

st.title("📚 Research Network Visualizer")

st.markdown("""
Upload a **PDF** to analyze its citation network, or an **Excel file** (list of DOIs) to cross-reference multiple papers.
""")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=['pdf', 'xlsx', 'xls'],
    help="Select a PDF or Excel file"
)

if uploaded_file is not None:
    file_details = {"filename": uploaded_file.name, "filetype": uploaded_file.type}
    
    # Determine file type
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext == '.pdf':
        st.info("Processing PDF... this may take a few minutes depending on the number of references.")
        
        # PDF processing requires a file path, so we save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        # Status placeholder
        status_placeholder = st.empty()
        
        def update_status(msg):
            status_placeholder.info(msg)

        # --- FIX IS HERE ---
        # build_reference_network now returns TWO values: G and suggestions
        G, suggestions = Local_Reference.build_reference_network(tmp_path, progress_callback=update_status)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if G:
            status_placeholder.success("Processing Complete!")
            st.write(f"**Nodes found:** {G.number_of_nodes()}")
            
            # --- 1. DISPLAY PLOTS FIRST ---
            # Get Plots
            fig_net, fig_mat = Local_Reference.get_network_plots(G)
            
            tab1, tab2 = st.tabs(["Citation Network", "Cross-Reference Matrix"])
            
            with tab1:
                st.plotly_chart(fig_net, use_container_width=True)
                
            with tab2:
                st.plotly_chart(fig_mat, use_container_width=True)

            # --- 2. DISPLAY SUGGESTIONS SECOND ---
            st.divider() # Visual separator
            if suggestions:
                st.subheader("📚 Recommended Articles")
                st.markdown("Suggestions based on citation impact and network analysis:")
                
                for i, paper in enumerate(suggestions):
                    title = paper.get('title', 'Unknown Title')
                    source_tag = paper.get('source', '')
                    
                    # Add a badge/color based on source
                    if "Cites Main" in source_tag:
                        color = "green"
                    elif "High Local" in source_tag:
                        color = "blue"
                    else:
                        color = "orange"
                        
                    st.markdown(f"**{i+1}. {title}** :{color}[{source_tag}]")
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
            
        # Excel logic
        G = Cross_Reference.build_cross_reference_network(uploaded_file, progress_callback=update_status)
        
        if G:
            status_placeholder.success("Processing Complete!")
            st.write(f"**Papers processed:** {G.number_of_nodes()}")
            
            fig_net, fig_mat = Cross_Reference.get_cross_ref_plots(G)
            
            tab1, tab2 = st.tabs(["Network Graph", "Adjacency Matrix"])
            
            with tab1:
                st.plotly_chart(fig_net, use_container_width=True)
                
            with tab2:
                st.plotly_chart(fig_mat, use_container_width=True)
        else:
            st.error("No valid DOIs processed. Check your Excel file column.")
            
    else:
        st.error("Unsupported file format.")
