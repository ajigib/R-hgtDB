import streamlit as st
import pandas as pd
from pyvis.network import Network
import tempfile
import os
import random
import base64
import math
import streamlit.components.v1 as components
import urllib.parse

# --- Page setup ---
st.set_page_config(page_title="Interactive Network", layout="wide")

# --- Hide built-in multipage sidebar navigation ---
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Custom CSS ---
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 1rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        section[data-testid="stSidebar"] { padding-right: 0rem; }
        h1, h2, h3 { margin-left: 1rem; }
        .external-link {
            display: block;
            text-align: center;
            background-color: #4CAF50;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
            margin: 5px 0;
            font-size: 14px;
        }
        .external-link:hover { background-color: #45a049; }
        .igv-link {
            display: block;
            text-align: center;
            background-color: #2196F3;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
            margin: 5px 0;
            font-size: 14px;
        }
        .igv-link:hover { background-color: #1976D2; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Title ---
st.title("🕸️ Network Graph with Collapsible Node Info Panel")

# --- Session State ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.image_size = 50
    st.session_state.font_size = 14
    st.session_state.connection_width = 2
    st.session_state.selected_classes = []
    st.session_state.bg_color = "#ffffff"
    st.session_state.node_colors = {}

# --- Load Data ---
@st.cache_data
def load_data():
    local_file_path = "file.txt"
    if os.path.exists(local_file_path):
        return pd.read_csv(local_file_path, sep="\t")
    else:
        st.error("Local file `file.txt` not found.")
        return None

df = load_data()
if df is None or not {"source", "target"}.issubset(df.columns):
    st.error("File must contain 'source' and 'target' columns.")
    st.stop()

# --- Helper: Rotifer image fallback ---
def get_rotifera_image_base64():
    try:
        with open("150px-Rotifer-1.jpg", "rb") as img:
            return f"data:image/jpeg;base64,{base64.b64encode(img.read()).decode()}"
    except:
        svg = """
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="40" fill="#ff6b6b" stroke="#333" stroke-width="2"/>
            <text x="50" y="55" text-anchor="middle" fill="white" font-size="14" font-weight="bold">R</text>
        </svg>
        """
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

rotifer_img = get_rotifera_image_base64()

# --- Sidebar Controls ---
st.sidebar.header("Visualization Controls")
st.session_state.image_size = st.sidebar.slider("Node Size", 20, 100, st.session_state.image_size)
st.session_state.font_size = st.sidebar.slider("Font Size", 8, 40, st.session_state.font_size)
st.session_state.connection_width = st.sidebar.slider("Connection Width", 1, 10, st.session_state.connection_width)
st.session_state.bg_color = st.sidebar.color_picker("Background Color", st.session_state.bg_color)

# Class filter
if "class" in df.columns:
    st.sidebar.subheader("Filter by Class")
    selected_classes = []
    for c in sorted(df["class"].dropna().unique()):
        if st.sidebar.checkbox(c, c in st.session_state.selected_classes, key=f"class_{c}"):
            selected_classes.append(c)
    st.session_state.selected_classes = selected_classes

# Node multi-select for info panel
st.sidebar.subheader("Select Node(s) for Info Panel")
selected_nodes = st.sidebar.multiselect("Nodes", sorted(df["source"].unique()))

# Sidebar toggle for right info panel
show_info = st.sidebar.checkbox("Show Node Info Panel", value=True)

# --- Helpers ---
def random_color():
    return "#" + ''.join(random.choices("0123456789ABCDEF", k=6))

def create_network(df, image_size, font_size, connection_width, selected_classes, bg_color, highlight_nodes):
    target_node = df["target"].value_counts().index[0]
    net = Network(height="750px", width="100%", bgcolor=bg_color, font_color="black", notebook=False)

    # Add target (center) node
    net.add_node(
        target_node, label="", shape="image", image=rotifer_img, size=image_size,
        color={"background":"#ffffff","border":"#ffffff"},
        font={"size":font_size,"color":"#000000"}, physics=False
    )

    filtered_df = df.copy()
    if "class" in df.columns and selected_classes:
        filtered_df = filtered_df[filtered_df["class"].isin(selected_classes)]

    # Persistent colors
    for node in filtered_df["source"].unique():
        if node not in st.session_state.node_colors:
            st.session_state.node_colors[node] = random_color()

    sources = filtered_df["source"].unique()
    n_sources = len(sources)
    radius = 400 + n_sources * 2

    for i, node in enumerate(sources):
        angle = 2 * math.pi * (i / n_sources)
        x, y = radius * math.cos(angle), radius * math.sin(angle)
        row = filtered_df[filtered_df["source"] == node].iloc[0]
        color = st.session_state.node_colors[node]
        font_color = "#000000" if int(color[1:],16) > 0x888888 else "#ffffff"
        border_width = 4 if node in highlight_nodes else 2
        title_text = "".join(f"{col}: {row[col]}\n" for col in df.columns)

        net.add_node(
            node, label=node, shape="box", size=image_size,
            font={"size":font_size,"color":font_color},
            color=color, borderWidth=border_width,
            title=title_text,
            x=x, y=y, physics=False
        )

        edge_color = "#FFD700" if node in highlight_nodes else "#7f8c8d"
        edge_width = connection_width*2 if node in highlight_nodes else connection_width
        net.add_edge(node, target_node, color=edge_color, width=edge_width)

    net.set_options(f"""
    {{
      "nodes": {{
        "font": {{ "size": {font_size}, "face": "Arial" }},
        "shapeProperties": {{ "borderRadius": 2 }}
      }},
      "edges": {{
        "smooth": {{ "enabled": true, "type": "curvedCW" }},
        "width": {connection_width}
      }},
      "physics": {{ "enabled": false }},
      "interaction": {{ "hover": true }}
    }}
    """)
    return net

# --- Layout ---
if show_info:
    col_graph, col_info = st.columns([5, 1])
else:
    col_graph = st.columns([1])[0]

# Graph
with col_graph:
    net = create_network(df, st.session_state.image_size, st.session_state.font_size,
                         st.session_state.connection_width, st.session_state.selected_classes,
                         st.session_state.bg_color, highlight_nodes=set(selected_nodes))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        html_content = open(tmp.name, "r", encoding="utf-8").read()
        os.unlink(tmp.name)
    components.html(html_content, height=750, scrolling=False)

# Info panel
if show_info:
    with col_info:
        st.subheader("Selected Node Information")
        info_container = st.container(height=750)

        with info_container:
            if selected_nodes:
                for i, node in enumerate(selected_nodes):
                    if node in df['source'].values:
                        row = df[df['source'] == node].iloc[0]
                        st.markdown(f"**📌 {row['source']}**")

                        # ✅ Detail Page Link
                        encoded_node = urllib.parse.quote(node)
                        node_detail_url = f"/Node_Details?node={encoded_node}"
                        base_url = f"http://localhost:{st.get_option('server.port') or 8501}"
                        full_url = base_url + node_detail_url

                        st.markdown(
                            f'<a href="{full_url}" target="_blank" class="external-link">📋 Open Detail Page</a>',
                            unsafe_allow_html=True
                        )

                        # ✅ NEW: IGV Browser Link
                        igv_url = f"/IGV_Browser?node={encoded_node}"
                        full_igv_url = base_url + igv_url
                        st.markdown(
                            f'<a href="{full_igv_url}" target="_blank" class="igv-link">🧬 Open Genome Browser</a>',
                            unsafe_allow_html=True
                        )

                        info_data = [
                            {"Property": col.capitalize(), "Value": row[col]}
                            for col in df.columns if col != "source"
                        ]
                        st.dataframe(pd.DataFrame(info_data), hide_index=True, use_container_width=True)

                        if i < len(selected_nodes) - 1:
                            st.divider()
            else:
                st.info("Select one or more nodes from the sidebar to see their details here.")

# --- Instructions ---
with st.expander("ℹ️ How to use this application"):
    st.markdown("""
    **Interactive Network Graph Features:**
    1. Select nodes from the sidebar to view information.
    2. Click "Open Detail Page" to open node details in a new tab.
    3. Click "Open Genome Browser" to view genomic information in IGV browser.
    4. Filter nodes by class using the sidebar.
    5. Customize visuals with sidebar sliders.

    **New Features:**
    - **Genome Browser**: Click the 🧬 button to open the IGV genome browser for selected genes
    - **Auto-navigation**: The genome browser automatically shows the genomic region for selected genes
    - **Full Integration**: Seamlessly switch between network view, detail pages, and genomic data
    """)

# --- Footer ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666;">
        <p>Built with Streamlit • Network Visualization • IGV Genome Browser Integration</p>
    </div>
    """,
    unsafe_allow_html=True
)
