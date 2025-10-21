import streamlit as st
import os
import pandas as pd
import threading
import http.server
import socketserver
import socket
import streamlit.components.v1 as components
import urllib.parse

# ======================================================
# ---------- CONFIG ------------------------------------
# ======================================================
st.set_page_config(page_title="IGV Browser — Adineta_vaga", layout="wide")
DATA_DIR = "data"

# ======================================================
# ---------- FILE SERVER (with CORS) -------------------
# ======================================================
class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "x-requested-with, content-type")
        return super().end_headers()

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def start_file_server():
    handler = CORSRequestHandler
    os.chdir(".")
    port = get_free_port()
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, port

server, PORT = start_file_server()

# ======================================================
# ---------- LOAD GENE TABLE ----------------------------
# ======================================================
gene_table_path = os.path.join(DATA_DIR, "vaga_proteins.tsv")

if os.path.exists(gene_table_path):
    df_genes = pd.read_csv(gene_table_path, sep="\t")
    df_genes.columns = [c.strip() for c in df_genes.columns]
    gene_names = sorted(df_genes["Locus tag"].dropna().unique().tolist())
else:
    df_genes = pd.DataFrame()
    gene_names = []

# ======================================================
# ---------- STREAMLIT UI ------------------------------
# ======================================================

# Hide built-in navigation
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True
)

# Back button
st.markdown(
    '<a href="/" target="_self" style="display:inline-block;padding:10px 20px;background-color:#6c757d;color:white;border-radius:5px;text-decoration:none;margin-bottom:20px;">← Back to Network</a>',
    unsafe_allow_html=True
)

st.title("🧬 IGV Genome Browser — Adineta_vaga")

st.info(f"Local file server running on: **http://localhost:{PORT}/data/**")

# Get node from query parameters
query_params = st.query_params
node_value = query_params.get("node")

# Handle both string or list types
if isinstance(node_value, list):
    node_name = node_value[0]
else:
    node_name = node_value

# Auto-select gene if node matches a locus tag
auto_locus = ""
if node_name:
    # Try to find the gene in the protein table
    match = df_genes[df_genes["Locus tag"] == node_name]
    if not match.empty:
        row = match.iloc[0]
        chrom = str(row["Accession"])
        start = int(row["Begin"])
        end = int(row["End"])
        auto_locus = f"{chrom}:{start}-{end}"
        st.success(f"Auto-selected gene: **{node_name}** → `{auto_locus}`")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🔍 Search Region or Gene")
    gene_choice = st.selectbox("Select gene:", [""] + gene_names, 
                              index=(gene_names.index(node_name) + 1 if node_name in gene_names else 0))
    manual_locus = st.text_input("Or enter locus manually (e.g. CP075492.1:20000-30000):", "")

with col2:
    st.markdown("### ℹ️ Selected Gene Info")

    if gene_choice:
        match = df_genes[df_genes["Locus tag"] == gene_choice]
        if not match.empty:
            row = match.iloc[0]
            chrom = str(row["Accession"])
            start = int(row["Begin"])
            end = int(row["End"])
            gene_locus = f"{chrom}:{start}-{end}"
            st.write(match)
        else:
            gene_locus = ""
    else:
        gene_locus = ""

# Final locus to display - priority: auto_locus > gene_locus > manual_locus
locus = auto_locus or gene_locus or manual_locus.strip() or ""

if locus:
    st.success(f"Displaying region: `{locus}`")
else:
    st.warning("Select a gene or enter a locus to display.")

height = st.slider("IGV browser height (px)", 300, 1000, 600)

# ======================================================
# ---------- IGV EMBEDDED HTML -------------------------
# ======================================================
igv_html = f"""
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/igv@2.15.5/dist/igv.min.js"></script>
</head>
<body>
  <div id="igv-container" style="height:{height}px; border:1px solid #ccc;"></div>
  <script>
    const container = document.getElementById("igv-container");

    const options = {{
      genome: {{
        fastaURL: "http://localhost:{PORT}/{DATA_DIR}/Adineta_vaga.fna",
        indexURL: "http://localhost:{PORT}/{DATA_DIR}/Adineta_vaga.fna.fai"
      }},
      locus: "{locus}" || undefined,
      tracks: [
        {{
          name: "Annotations (GFF3)",
          url: "http://localhost:{PORT}/{DATA_DIR}/Adineta_vaga.sorted.gff.gz",
          indexURL: "http://localhost:{PORT}/{DATA_DIR}/Adineta_vaga.sorted.gff.gz.tbi",
          format: "gff3",
          displayMode: "EXPANDED"
        }}
      ]
    }};

    igv.createBrowser(container, options).then(browser => {{
      console.log("✅ IGV loaded.");
      if ("{locus}") {{
        browser.search("{locus}");
      }}
    }});
  </script>
</body>
</html>
"""

components.html(igv_html, height=height + 80)
