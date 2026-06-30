
import folium
import pandas as pd
from folium.plugins import MarkerCluster, Fullscreen, MiniMap

# Corrected scene centres and regions
SCENE_CENTRES = {
    "05bc615a9b0e1159t": (42.5,  18.2, "Adriatic Sea · 22 Jul 2020"),
    "72dba3e82f782f67t": (58.45,  5.73, "North Sea · 18 Jul 2020"),
    "590dd08f71056cacv": (5.97,   4.05, "Gulf of Guinea · 24 Jul 2020"),
    "2899cfb18883251bt": (43.25, 14.25, "Adriatic Sea · 02 Jun 2020"),
    "b1844cde847a3942v": (5.96,   4.09, "Gulf of Guinea · 26 Jan 2020"),
    "cbe4ad26fe73f118t": (43.7,  -4.5,  "Bay of Biscay · 16 Jun 2020"),
    "e98ca5aba8849b06t": (49.16, -5.09, "English Channel · 10 May 2020"),
}

def get_color(label):
    return {
        "Dark"        : "#FF4136",
        "Cooperative" : "#2ECC40",
        "Suspicious"  : "#FF851B",
    }.get(label, "#AAAAAA")

def get_icon(label):
    return {
        "Dark"        : "exclamation-sign",
        "Cooperative" : "ok-sign",
        "Suspicious"  : "question-sign",
    }.get(label, "info-sign")

def get_folium_color(label):
    return {
        "Dark"        : "red",
        "Cooperative" : "green",
        "Suspicious"  : "orange",
    }.get(label, "gray")

def build_map(df, center_lat=45.0, center_lon=5.0, zoom=4):
    m = folium.Map(
        location      = [center_lat, center_lon],
        zoom_start    = zoom,
        tiles         = "CartoDB positron",
        prefer_canvas = True,
    )

    Fullscreen().add_to(m)
    MiniMap(toggle_display=True).add_to(m)

    dark_layer  = folium.FeatureGroup(
        name="🔴 Dark Vessels",        show=True)
    coop_layer  = folium.FeatureGroup(
        name="🟢 Cooperative Vessels", show=True)
    susp_layer  = folium.FeatureGroup(
        name="🟠 Suspicious Vessels",  show=True)

    layer_map = {
        "Dark"        : dark_layer,
        "Cooperative" : coop_layer,
        "Suspicious"  : susp_layer,
    }

    for _, row in df.iterrows():
        label    = row.get("final_label", "Unknown")
        color    = get_color(label)
        conf_pct = f"{row['conf']*100:.3f}%"

        scene_info = SCENE_CENTRES.get(
            row["scene_id"],
            (None, None, row["scene_id"]))
        scene_desc = scene_info[2]             if isinstance(scene_info, tuple)             else str(scene_info)

        ais_info = (
            f"MMSI: {row['ais_mmsi']}<br>"
            f"Category: {row['ais_category']}<br>"
            f"Length: {row['ais_length_m']:.1f} m"
            if row["ais_matched"] and
               pd.notna(row.get("ais_mmsi"))
            else "No AIS match found"
        )

        popup_html = f"""
        <div style="font-family:monospace;
                    font-size:12px; width:230px;
                    color:#1a1a1a;">
            <b style="color:{color}; font-size:14px;">
                {label} Vessel
            </b><br>
            <hr style="margin:4px 0">
            <b>Confidence:</b> {conf_pct}<br>
            <b>Model:</b> {row["class_name"].capitalize()}<br>
            <b>AIS Match:</b>
                {"Yes" if row["ais_matched"] else "No"}<br>
            <hr style="margin:4px 0">
            <b>AIS Info:</b><br>{ais_info}<br>
            <hr style="margin:4px 0">
            <b>Scene:</b> {scene_desc}<br>
            <b>Position:</b><br>
            Lat: {row["lat"]:.5f}<br>
            Lon: {row["lon"]:.5f}
        </div>
        """

        folium.Marker(
            location = [row["lat"], row["lon"]],
            popup    = folium.Popup(
                           popup_html, max_width=250),
            tooltip  = f"{label} | {conf_pct}",
            icon     = folium.Icon(
                color  = get_folium_color(label),
                icon   = get_icon(label),
                prefix = "glyphicon"),
        ).add_to(layer_map.get(label, coop_layer))

    for layer in layer_map.values():
        layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m
