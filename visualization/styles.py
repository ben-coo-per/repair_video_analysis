"""Color schemes and styling for charts."""

# Brand colors
BRAND_COLORS = {
    "Makita": "#00A3E0",      # Makita teal/blue
    "DeWalt": "#FEBD17",      # DeWalt yellow
    "Bosch": "#005691",       # Bosch blue
    "Milwaukee": "#DB0032",   # Milwaukee red
    "Metabo": "#00843D",      # Metabo green
    "Hitachi": "#E31937",     # Hitachi red
    "Panasonic": "#0068B5",   # Panasonic blue
    "Slugger": "#FF6600",     # Orange
    "HiTech": "#6B7280",      # Gray
}

# Outcome colors
OUTCOME_COLORS = {
    "Successful": "#22C55E",  # Green
    "Failed": "#EF4444",      # Red
    "Pending": "#F59E0B",     # Amber
}

# Chart template settings
CHART_TEMPLATE = "plotly_white"

# Default color sequence for charts
DEFAULT_COLORS = [
    "#00A3E0",  # Blue
    "#FEBD17",  # Yellow
    "#22C55E",  # Green
    "#EF4444",  # Red
    "#8B5CF6",  # Purple
    "#F59E0B",  # Amber
    "#EC4899",  # Pink
    "#06B6D4",  # Cyan
    "#84CC16",  # Lime
    "#6366F1",  # Indigo
]

# Heatmap color scale
HEATMAP_COLORS = [
    [0.0, "#F3F4F6"],   # Light gray for 0
    [0.25, "#BFDBFE"],  # Light blue
    [0.5, "#60A5FA"],   # Medium blue
    [0.75, "#2563EB"],  # Blue
    [1.0, "#1E40AF"],   # Dark blue
]
