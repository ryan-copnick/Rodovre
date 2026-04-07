# Rodovre

## OSM Map of Green Spaces in Copenhagen

An interactive map that queries [OpenStreetMap](https://www.openstreetmap.org/) via the
[Overpass API](https://overpass-api.de/) and renders all green spaces in Copenhagen as a
colour-coded, zoomable HTML map.

### Green space types included

| OSM tag | Colour |
|---|---|
| `leisure=park` | green |
| `leisure=garden` | dark green |
| `leisure=nature_reserve` | teal |
| `landuse=forest` | deep green |
| `natural=wood` | forest green |
| `landuse=grass` | light green |
| `landuse=meadow` | mint green |
| `natural=grassland` | spring green |
| `natural=heath` | light teal |
| `landuse=allotments` | orange |

### Requirements

- Python 3.8+
- `folium` 0.19+
- `requests` 2.x

Install dependencies:

```bash
pip install -r requirements.txt
```

### Usage

```bash
python map_green_spaces.py
```

This generates **`copenhagen_green_spaces.html`** in the current directory.
Open it in any browser to explore the interactive map.

Each marker shows the name of the green space and a link to its OpenStreetMap page.
Markers are clustered at low zoom levels for readability.