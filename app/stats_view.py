
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

COLOR_MAP = {
    "Dark"        : "#FF4136",
    "Cooperative" : "#2ECC40",
    "Suspicious"  : "#FF851B",
}

SCENE_DATES = {
    "05bc615a9b0e1159t": "Adriatic Sea · 22 Jul 2020",
    "72dba3e82f782f67t": "North Sea · 18 Jul 2020",
    "590dd08f71056cacv": "Gulf of Guinea · 24 Jul 2020",
    "2899cfb18883251bt": "Adriatic Sea · 02 Jun 2020",
    "b1844cde847a3942v": "Gulf of Guinea · 26 Jan 2020",
    "cbe4ad26fe73f118t": "Bay of Biscay · 16 Jun 2020",
    "e98ca5aba8849b06t": "English Channel · 10 May 2020",
}

def render_sidebar_stats(df, st):
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Detection Summary")

    total = len(df)
    dark  = (df["final_label"]=="Dark").sum()
    coop  = (df["final_label"]=="Cooperative").sum()
    susp  = (df["final_label"]=="Suspicious").sum()

    col1, col2 = st.sidebar.columns(2)
    col1.metric("Total",       total)
    col2.metric("Dark",        dark,
                delta=f"{dark/total*100:.1f}%" if total else "0%")
    col1.metric("Cooperative", coop,
                delta=f"{coop/total*100:.1f}%" if total else "0%")
    col2.metric("Suspicious",  susp,
                delta=f"{susp/total*100:.1f}%" if total else "0%")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🥧 Label Distribution")

    label_counts = df["final_label"].value_counts(
        ).reset_index()
    label_counts.columns = ["Label","Count"]
    fig_pie = px.pie(
        label_counts,
        names  = "Label",
        values = "Count",
        color  = "Label",
        color_discrete_map = COLOR_MAP,
        hole   = 0.4,
    )
    fig_pie.update_layout(
        margin        = dict(t=10,b=10,l=10,r=10),
        paper_bgcolor = "rgba(255,255,255,1)",
        font_color    = "#1a1a1a",
        showlegend    = True,
        legend        = dict(font=dict(color="#1a1a1a")),
    )
    st.sidebar.plotly_chart(
        fig_pie, use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛳️ Detections per Scene")

    scene_counts = df.groupby(
        ["scene_id","final_label"]
    ).size().reset_index(name="Count")
    scene_counts["Date"] = scene_counts[
        "scene_id"].map(SCENE_DATES)
    scene_counts["Label_short"] = scene_counts[
        "scene_id"].str[:8]

    fig_bar = px.bar(
        scene_counts,
        x              = "Count",
        y              = "Label_short",
        color          = "final_label",
        orientation    = "h",
        color_discrete_map = COLOR_MAP,
        labels         = {"Label_short": "Scene",
                          "final_label": "Label"},
    )
    fig_bar.update_layout(
        margin        = dict(t=10,b=10,l=10,r=10),
        paper_bgcolor = "rgba(255,255,255,1)",
        plot_bgcolor  = "rgba(255,255,255,1)",
        font_color    = "#1a1a1a",
        xaxis         = dict(gridcolor="#dddddd"),
        yaxis         = dict(gridcolor="#dddddd"),
        showlegend    = False,
        barmode       = "stack",
    )
    st.sidebar.plotly_chart(
        fig_bar, use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 AIS Category")

    ais_matched = df[df["ais_matched"]==True]
    if len(ais_matched) > 0:
        cat_counts = ais_matched[
            "ais_category"].value_counts().reset_index()
        cat_counts.columns = ["Category","Count"]
        fig_cat = px.bar(
            cat_counts,
            x = "Count", y = "Category",
            orientation = "h",
            color_discrete_sequence = ["#2ECC40"],
        )
        fig_cat.update_layout(
            margin        = dict(t=10,b=10,l=10,r=10),
            paper_bgcolor = "rgba(255,255,255,1)",
            plot_bgcolor  = "rgba(255,255,255,1)",
            font_color    = "#1a1a1a",
            xaxis         = dict(gridcolor="#dddddd"),
            yaxis         = dict(gridcolor="#dddddd"),
        )
        st.sidebar.plotly_chart(
            fig_cat, use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Confidence Distribution")

    fig_hist = px.histogram(
        df, x="conf",
        color="final_label",
        nbins=40,
        color_discrete_map=COLOR_MAP,
        labels={"conf":"Confidence Score"},
    )
    fig_hist.update_layout(
        margin        = dict(t=10,b=10,l=10,r=10),
        paper_bgcolor = "rgba(255,255,255,1)",
        plot_bgcolor  = "rgba(255,255,255,1)",
        font_color    = "#1a1a1a",
        xaxis         = dict(gridcolor="#dddddd"),
        yaxis         = dict(gridcolor="#dddddd"),
        showlegend    = False,
    )
    st.sidebar.plotly_chart(
        fig_hist, use_container_width=True)


def render_scene_table(df, st):
    st.markdown("### 🗂️ Per-Scene Summary")

    rows = []
    for sid in df["scene_id"].unique():
        df_s  = df[df["scene_id"]==sid]
        rows.append({
            "Scene ID"    : sid[:16]+"...",
            "Region/Date" : SCENE_DATES.get(sid,"?"),
            "Total"       : len(df_s),
            "Dark"        : (df_s["final_label"]=="Dark").sum(),
            "Cooperative" : (df_s["final_label"]=="Cooperative").sum(),
            "Suspicious"  : (df_s["final_label"]=="Suspicious").sum(),
            "AIS Matched" : df_s["ais_matched"].sum(),
        })

    df_table = pd.DataFrame(rows)
    st.dataframe(df_table, use_container_width=True)


def render_detection_table(df, st):
    st.markdown("### 🔍 Detection Table")

    display_cols = [
        "final_label","scene_id","lat","lon","conf",
        "class_name","ais_matched",
        "ais_category","ais_mmsi","ais_length_m"
    ]
    display_cols = [c for c in display_cols
                    if c in df.columns]

    def highlight_label(val):
        colors = {
            "Dark"        : "background-color:#FF4136;"
                            "color:white",
            "Cooperative" : "background-color:#2ECC40;"
                            "color:black",
            "Suspicious"  : "background-color:#FF851B;"
                            "color:white",
        }
        return colors.get(val, "")

    styled = df[display_cols].style.applymap(
        highlight_label,
        subset=["final_label"]
    ).format({
        "lat"         : "{:.5f}",
        "lon"         : "{:.5f}",
        "conf"        : "{:.5f}",
        "ais_length_m": lambda x:
            f"{x:.1f}" if pd.notna(x) else "N/A",
    })
    st.dataframe(styled,
                 use_container_width=True,
                 height=320)
