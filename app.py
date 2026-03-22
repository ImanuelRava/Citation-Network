# app.py
import streamlit as st
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

uploaded_file = st.file_uploader(
    "Choose a file",
    type=['pdf', 'xlsx', 'xls'],
    help="Select a PDF or Excel file"
)

if uploaded_file is not None:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext == '.pdf':
        # --- Selection Box for PDF Mode ---
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
            
            # 1. DISPLAY PLOTS
            fig_net, fig_mat = plot_func(G)
            
            tab1, tab2 = st.tabs(["Citation Network", "Cross-Reference Matrix"])
            
            with tab1:
                st.plotly_chart(fig_net, use_container_width=True)
            with tab2:
                st.plotly_chart(fig_mat, use_container_width=True)

            # 2. DISPLAY SUGGESTIONS
            st.divider()
            if suggestions:
                st.subheader("📚 Recommended Articles")
                
                for i, paper in enumerate(suggestions):
                    title = paper.get('title', 'Unknown Title')
                    st.markdown(f"**{i+1}. {title}**")
                    
                    source_tag = paper.get('source', '')
                    if "Recent" in source_tag:
                        color = "green"
                    elif "Local" in source_tag:
                        color = "blue"
                    else:
                        color = "gray"
                        
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