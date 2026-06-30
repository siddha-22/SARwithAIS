
import streamlit as st
import pandas as pd
import os, sys, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "app"))

from map_view   import build_map, SCENE_CENTRES
from stats_view import (render_sidebar_stats,
                         render_scene_table,
                         render_detection_table,
                         SCENE_DATES)
from streamlit_folium import st_folium

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title = "VarunEye — Dark Vessel Detection",
    page_icon  = "🛰️",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── CSS — white theme ────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #ffffff; }
    .block-container { padding-top: 1rem; }
    h1 { color: #0066cc; font-family: monospace; }
    h3 { color: #333333; }
    .stMetric label { color: #555555; font-size: 12px; }
    div[data-testid="stSidebarContent"] {
        background-color: #f5f5f5; }
    p, div, span, td, th { color: #1a1a1a; }
</style>
""", unsafe_allow_html=True)

# ── Load config ───────────────────────────────────────────
@st.cache_data
def load_config():
    with open(os.path.join(ROOT,"config.yaml")) as f:
        return yaml.safe_load(f)

config = load_config()

# ── Load detections ───────────────────────────────────────
@st.cache_data
def load_detections():
    det_path = os.path.join(
        ROOT, config["paths"]["detections"])
    return pd.read_csv(det_path)

df_all = load_detections()

# ── Header ────────────────────────────────────────────────
st.markdown("""
<h1>🛰️ VarunEye — Dark Vessel Detection</h1>
<p style="color:#555555; font-family:monospace;
          margin-top:-10px;">
    SAR + AIS Fusion &nbsp;|&nbsp;
    Sentinel-1 &nbsp;|&nbsp;
    YOLOv8s · 7 Scenes · Multi-Region (Europe + W.Africa) &nbsp;|&nbsp;
    Global Fishing Watch AIS
</p>
<hr style="border-color:#ddd; margin-bottom:1rem">
""", unsafe_allow_html=True)

# ── Sidebar filters ───────────────────────────────────────
st.sidebar.markdown("## 🔧 Filters")

all_scenes = sorted(df_all["scene_id"].unique())
scene_labels = {
    sid: f"{sid[:8]}... · {SCENE_DATES.get(sid,'?')}"
    for sid in all_scenes
}
selected_scenes = st.sidebar.multiselect(
    "Scenes",
    options  = all_scenes,
    default  = all_scenes,
    format_func = lambda x: scene_labels[x],
)

selected_labels = st.sidebar.multiselect(
    "Vessel Labels",
    options = ["Dark","Cooperative","Suspicious"],
    default = ["Dark","Cooperative","Suspicious"],
)

conf_min = float(df_all["conf"].min())
conf_max = float(df_all["conf"].max())
conf_range = st.sidebar.slider(
    "Confidence Range",
    min_value = conf_min,
    max_value = conf_max,
    value     = (conf_min, conf_max),
    format    = "%.5f",
)

ais_filter = st.sidebar.selectbox(
    "AIS Status",
    ["All","AIS Matched","AIS Unmatched"],
    index = 0,
)

df = df_all[
    df_all["scene_id"].isin(selected_scenes) &
    df_all["final_label"].isin(selected_labels) &
    (df_all["conf"] >= conf_range[0]) &
    (df_all["conf"] <= conf_range[1])
].copy()

if ais_filter == "AIS Matched":
    df = df[df["ais_matched"]==True]
elif ais_filter == "AIS Unmatched":
    df = df[df["ais_matched"]==False]

render_sidebar_stats(df, st)

# ── Top metrics bar ───────────────────────────────────────
m1,m2,m3,m4,m5,m6 = st.columns(6)
m1.metric("Scenes",      len(selected_scenes))
m2.metric("Detections",  len(df))
m3.metric("Dark",        (df["final_label"]=="Dark").sum())
m4.metric("Cooperative", (df["final_label"]=="Cooperative").sum())
m5.metric("Suspicious",  (df["final_label"]=="Suspicious").sum())
m6.metric("AIS Matched", df["ais_matched"].sum())

st.markdown("<hr style='border-color:#ddd'>",
            unsafe_allow_html=True)

# ── Main layout ───────────────────────────────────────────
col_map, col_info = st.columns([3, 1])

with col_map:
    st.markdown("### 🗺️ Interactive Vessel Map")
    st.caption(
        f"Showing {len(df)} of {len(df_all)} detections "
        f"across {len(selected_scenes)} scene(s) · "
        f"Dark={(df['final_label']=='Dark').sum()} · "
        f"Coop={(df['final_label']=='Cooperative').sum()} · "
        f"Susp={(df['final_label']=='Suspicious').sum()}"
    )

    if len(df) == 0:
        st.warning("No detections match current filters.")
    else:
        center_lat = df["lat"].mean()
        center_lon = df["lon"].mean()
        m = build_map(df,
                      center_lat=center_lat,
                      center_lon=center_lon,
                      zoom=4)
        st_folium(m, width=900, height=560,
                  returned_objects=[])

with col_info:
    st.markdown("### 📡 Mission Info")
    st.markdown(f"""
| Field | Value |
|---|---|
| **Sensor** | Sentinel-1A IW GRD |
| **Scenes** | 7 |
| **Regions** | N.Sea, Adriatic, Gulf of Guinea, Bay of Biscay, English Channel |
| **Period** | Jan–Jul 2020 |
| **Resolution** | 10 m/px |
| **Model** | YOLOv8s |
| **mAP@50** | 0.478 |
| **GT Recall** | 75.8% |
| **AIS Source** | GFW SAR v3 |
| **Total Dets** | {len(df_all)} |
""")

    st.markdown("### 🎨 Legend")
    st.markdown("""
🔴 **Dark** — SAR detected, no AIS

🟢 **Cooperative** — SAR + AIS matched

🟠 **Suspicious** — Unconfirmed AIS
""")

    st.markdown("### ⚙️ Pipeline")
    st.markdown("""
1. Sentinel-1 SAR chipping
2. Land masking (owiMask)
3. YOLOv8s detection
4. Pixel → Lat/Lon (UTM→WGS84, per-scene CRS)
5. Cross-chip NMS
6. GFW AIS correlation
7. Dark vessel labeling
""")

st.markdown("<hr style='border-color:#ddd'>",
            unsafe_allow_html=True)

render_scene_table(df, st)

st.markdown("<hr style='border-color:#ddd'>",
            unsafe_allow_html=True)

render_detection_table(df, st)

st.markdown("### 💾 Export")
col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    csv_filtered = df.to_csv(index=False)
    st.download_button(
        label     = "⬇ Download filtered CSV",
        data      = csv_filtered,
        file_name = "varuneye_filtered.csv",
        mime      = "text/csv",
    )

with col_dl2:
    csv_dark = df[df["final_label"]=="Dark"].to_csv(index=False)
    st.download_button(
        label     = "⬇ Download dark vessels only",
        data      = csv_dark,
        file_name = "varuneye_dark_only.csv",
        mime      = "text/csv",
    )

st.markdown("""
<hr style="border-color:#ddd">
<p style="color:#888; font-size:11px;
          text-align:center; font-family:monospace;">
VarunEye · 7-Scene Multi-Region SAR+AIS Fusion ·
YOLOv8s · Sentinel-1 · Global Fishing Watch ·
Built for PierSight Maritime Surveillance
</p>
""", unsafe_allow_html=True)
