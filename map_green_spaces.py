"""
Generate an interactive OSM map of green spaces in Copenhagen.

Green space types included:
  - Parks and leisure gardens (leisure=park, leisure=garden, leisure=nature_reserve)
  - Forest and woodland (landuse=forest, natural=wood)
  - Grass, meadow and heath (landuse=grass, landuse=meadow, natural=grassland, natural=heath)
  - Allotments (landuse=allotments)

The script queries the Overpass API, then renders the results as a
colour-coded Folium (Leaflet.js) map saved to `copenhagen_green_spaces.html`.
"""

import json
import sys

import requests
import folium
from folium.plugins import MarkerCluster

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Bounding box for Copenhagen municipality (south, west, north, east)
COPENHAGEN_BBOX = (55.615, 12.450, 55.775, 12.700)

# Colour palette: one colour per OSM tag value shown in the legend
COLOUR_MAP = {
    "park": "#2ecc71",
    "garden": "#27ae60",
    "nature_reserve": "#1abc9c",
    "forest": "#145a32",
    "wood": "#1e8449",
    "grass": "#a9dfbf",
    "meadow": "#82e0aa",
    "grassland": "#58d68d",
    "heath": "#a3e4d7",
    "allotments": "#f0b27a",
}

DEFAULT_COLOUR = "#2ecc71"

# Map centre (approximately the centre of Copenhagen)
MAP_CENTRE = [55.6761, 12.5683]
MAP_ZOOM = 12

OUTPUT_FILE = "copenhagen_green_spaces.html"

# ---------------------------------------------------------------------------
# Overpass query
# ---------------------------------------------------------------------------

def build_query(bbox):
    south, west, north, east = bbox
    bbox_str = f"{south},{west},{north},{east}"

    tags = [
        ('leisure', 'park'),
        ('leisure', 'garden'),
        ('leisure', 'nature_reserve'),
        ('landuse', 'forest'),
        ('landuse', 'grass'),
        ('landuse', 'meadow'),
        ('landuse', 'allotments'),
        ('natural', 'wood'),
        ('natural', 'grassland'),
        ('natural', 'heath'),
    ]

    parts = []
    for key, value in tags:
        for element_type in ('way', 'relation'):
            parts.append(f'{element_type}["{key}"="{value}"]({bbox_str});')

    return f"""
[out:json][timeout:60];
(
  {''.join(parts)}
);
out center tags;
"""


def fetch_green_spaces(bbox):
    query = build_query(bbox)
    print("Querying Overpass API for green spaces in Copenhagen ...")
    response = requests.post(OVERPASS_URL, data={"data": query}, timeout=90)
    response.raise_for_status()
    return response.json()

# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def get_tag_value(tags):
    """Return the primary green-space tag value for colour lookup."""
    for key in ("leisure", "landuse", "natural"):
        if key in tags:
            return tags[key]
    return None


def extract_features(data):
    features = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})

        # Determine centre coordinates
        if "center" in element:
            lat = element["center"]["lat"]
            lon = element["center"]["lon"]
        elif element.get("type") == "node":
            lat = element.get("lat")
            lon = element.get("lon")
        else:
            continue

        if lat is None or lon is None:
            continue

        name = tags.get("name", "Unnamed green space")
        tag_value = get_tag_value(tags)
        colour = COLOUR_MAP.get(tag_value, DEFAULT_COLOUR)

        features.append({
            "lat": lat,
            "lon": lon,
            "name": name,
            "tag_value": tag_value or "green space",
            "colour": colour,
            "element_type": element.get("type", "way"),
            "osm_id": element.get("id"),
        })

    return features

# ---------------------------------------------------------------------------
# Map construction
# ---------------------------------------------------------------------------

def build_legend_html():
    items = "".join(
        f'<li><span style="background:{colour};display:inline-block;'
        f'width:14px;height:14px;margin-right:6px;border-radius:3px;'
        f'border:1px solid #555;"></span>{label.replace("_", " ").title()}</li>'
        for label, colour in COLOUR_MAP.items()
    )
    return f"""
    <div style="position:fixed;bottom:30px;right:10px;z-index:1000;
                background:white;padding:12px 16px;border-radius:8px;
                border:1px solid #ccc;font-size:13px;line-height:1.8;
                box-shadow:2px 2px 6px rgba(0,0,0,.2);">
      <b style="font-size:14px;">Green Space Types</b>
      <ul style="list-style:none;margin:6px 0 0;padding:0;">{items}</ul>
    </div>
    """


def build_map(features):
    m = folium.Map(location=MAP_CENTRE, zoom_start=MAP_ZOOM,
                   tiles="OpenStreetMap")

    cluster = MarkerCluster(name="Green spaces").add_to(m)

    for feat in features:
        popup_html = (
            f"<b>{feat['name']}</b><br>"
            f"Type: {feat['tag_value'].replace('_', ' ').title()}<br>"
            f"<a href='https://www.openstreetmap.org/"
            f"{feat['element_type']}/{feat['osm_id']}' target='_blank'>"
            f"View on OSM</a>"
        )
        folium.CircleMarker(
            location=[feat["lat"], feat["lon"]],
            radius=8,
            color=feat["colour"],
            fill=True,
            fill_color=feat["colour"],
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=feat["name"],
        ).add_to(cluster)

    m.get_root().html.add_child(folium.Element(build_legend_html()))

    folium.LayerControl().add_to(m)
    return m

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    try:
        data = fetch_green_spaces(COPENHAGEN_BBOX)
    except requests.RequestException as exc:
        print(f"Error fetching data from Overpass API: {exc}", file=sys.stderr)
        sys.exit(1)

    features = extract_features(data)
    print(f"Found {len(features)} green space features.")

    if not features:
        print("No features found – the map will be empty.", file=sys.stderr)

    m = build_map(features)
    m.save(OUTPUT_FILE)
    print(f"Map saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
