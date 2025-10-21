import streamlit as st
import pandas as pd
import os
import urllib.parse
import streamlit.components.v1 as components  # ← ADD THIS IMPORT

# --- Setup ---
st.set_page_config(page_title="Node_Details", layout="wide")

# --- Hide built-in navigation ---
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .node-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            margin: 0.5rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Load Data ---
@st.cache_data
def load_data():
    path = "file.txt"
    if os.path.exists(path):
        return pd.read_csv(path, sep="\t")
    else:
        st.error("Data file 'file.txt' not found.")
        return None

df = load_data()
if df is None:
    st.stop()

# --- Get node name from URL ---
query_params = st.query_params
node_value = query_params.get("node")

# Handle both string or list types
if isinstance(node_value, list):
    node_name = node_value[0]
else:
    node_name = node_value

if not node_name:
    st.error("No node specified.")
    st.stop()

if node_name not in df["source"].values:
    st.error(f"Node '{node_name}' not found in data.")
    st.stop()

node_data = df[df["source"] == node_name].iloc[0]

# --- Header ---
st.markdown(f"""
<div class="node-header">
    <h1>📋 {node_name}</h1>
    <p>Detailed Node Information</p>
</div>
""", unsafe_allow_html=True)

# --- Back button ---
st.markdown(
    '<a href="/" target="_self" style="display:inline-block;padding:10px 20px;background-color:#6c757d;color:white;border-radius:5px;text-decoration:none;">← Back to Network</a>',
    unsafe_allow_html=True
)

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧬 Genome Browser", "📊 Overview", "🔍 Detailed Data", "🌐 External Links", "📈 Analysis"])

# --- Genome Browser tab ---
with tab1:
    st.subheader("IGV Genome Browser")
    
    # Create link to standalone IGV browser
    encoded_node = urllib.parse.quote(node_name)
    igv_url = f"/IGV_Browser?node={encoded_node}"
    base_url = f"http://localhost:{st.get_option('server.port') or 8501}"
    full_igv_url = base_url + igv_url
    
    st.markdown(f"""
    <div style="background-color: #e8f4fd; padding: 20px; border-radius: 10px; border-left: 4px solid #2196F3;">
        <h4>🚀 Open in Full Screen</h4>
        <p>For the best genome browsing experience, open the IGV browser in a dedicated page:</p>
        <a href="{full_igv_url}" target="_blank" style="display:inline-block;padding:10px 20px;background-color:#2196F3;color:white;border-radius:5px;text-decoration:none;font-weight:bold;">
            Open Genome Browser ↗
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**Embedded Genome Browser View**")
    
    # Embedded iframe for IGV
    components.iframe(full_igv_url, height=600, scrolling=True)

# --- Overview tab ---
with tab2:
    st.subheader("Basic Information")
    st.metric("Node ID", node_data["source"])
    st.metric("Target", node_data["target"])
    if "class" in node_data and pd.notna(node_data["class"]):
        st.metric("Class", node_data["class"])
    if "description" in node_data and pd.notna(node_data["description"]):
        st.write("**Description:**", node_data["description"])

# --- Detailed Data tab ---
with tab3:
    st.subheader("Complete Node Data")
    display_df = pd.DataFrame({
        "Property": node_data.index,
        "Value": node_data.values
    })
    st.dataframe(display_df, hide_index=True, use_container_width=True)

# --- External Links tab ---
with tab4:
    st.subheader("External Links")
    encoded_node = urllib.parse.quote(node_name)
    links = {
        "Google": f"https://www.google.com/search?q={encoded_node}",
        "NCBI": f"https://www.ncbi.nlm.nih.gov/search/?term={encoded_node}",
        "UniProt": f"https://www.uniprot.org/uniprotkb?query={encoded_node}",
        "PubMed": f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_node}"
    }
    for name, url in links.items():
        st.markdown(
            f'<a href="{url}" target="_blank" style="display:block;margin:6px 0;background-color:#008CBA;color:white;padding:10px;border-radius:5px;text-decoration:none;text-align:center;">{name}</a>',
            unsafe_allow_html=True
        )

# --- Analysis tab ---
with tab5:
    st.subheader("Node Analysis")
    st.write("Add advanced metrics or related nodes here.")

st.markdown("---")
st.markdown(f"*Node detail page for: {node_name}*")
