"""Data loading and processing functions for repair video analysis."""

import json
from pathlib import Path
import pandas as pd


_COMPONENT_RULES = [
    (
        "Motor Brushes",
        [
            "motor brushes",
            "brush holder",
            "brush spring",
            "motor windings and brushes",
            "motor brushes and",
            "brushes",
        ],
    ),
    (
        "Armature",
        [
            "armature",
        ],
    ),
    (
        "Battery",
        [
            "battery",
            "lithium ion cells",
        ],
    ),
    (
        "Power Cord",
        [
            "power cord",
            "power cable",
            "power wire",
            "cable guard",
        ],
    ),
    (
        "Controller / Circuit Board",
        [
            "circuit board",
            "controller",
            "control board",
            "speed controller",
            "power supply board",
            "selector switch board",
            "rotary encoder",
            "filter capacitor",
            "internal electronics",
            "capacitor",
        ],
    ),
    (
        "Switch",
        [
            "switch",
            "trigger",
        ],
    ),
    (
        "Motor",
        [
            "motor",
            "field coil",
            "field connection",
            "field",
            "motor/coil",
        ],
    ),
    (
        "Chuck",
        [
            "chuck",
            "collet",
            "bit holder",
        ],
    ),
    (
        "Bearing",
        [
            "bearing",
        ],
    ),
    (
        "Tool Holder",
        [
            "tool holder",
            "blade clamp",
            "blade holder",
            "blade lock",
            "blade mounting",
            "blade installation",
            "sds tool holder",
        ],
    ),
    (
        "Gearbox / Gears",
        [
            "gearbox",
            "gear",
            "clutch",
            "reduction gear",
        ],
    ),
    (
        "Housing / Case",
        [
            "housing",
            "case ",
            "base/guard",
            "base adjustment",
            "plastic cover",
            "rubber cap",
            "rubber front",
            "mounting bracket",
        ],
    ),
    (
        "Anvil",
        [
            "anvil",
        ],
    ),
    (
        "Belt / Drive",
        [
            "belt",
            "drive pin",
            "drive belt",
        ],
    ),
    (
        "Piston / Hammer Mechanism",
        [
            "piston",
            "hammer mechanism",
            "impact bolt",
            "connecting rod",
        ],
    ),
    (
        "Spring",
        [
            "spring",
            "lifter spring",
        ],
    ),
    (
        "Nail Gun Mechanism",
        [
            "nail",
            "firing pin",
            "magazine",
        ],
    ),
    (
        "Fan",
        [
            "fan",
        ],
    ),
    (
        "Wiring / Connectors",
        [
            "wiring",
            "connectors",
            "terminals",
            "cable,",
        ],
    ),
    (
        "O-Ring / Seal",
        [
            "o-ring",
            "gasket",
        ],
    ),
]


def _match_component(text: str) -> str | None:
    """Match a text fragment to a standardized component label."""
    text = text.lower().strip()
    for label, keywords in _COMPONENT_RULES:
        for kw in keywords:
            if kw in text:
                return label
    return None


def normalize_components(component: str) -> list[str]:
    """Normalize a raw component string into a list of standardized names.

    A value like "bearings, switch, flanges, belt" returns
    ["Bearing", "Belt / Drive", "Switch"].  One row per repair is preserved;
    the component column becomes a list.
    """
    import re

    if pd.isna(component) or not component:
        return []

    # Try matching the full string first (handles cases like
    # "motor brushes" that shouldn't be split on the comma).
    full_match = _match_component(component)
    if full_match:
        return [full_match]

    # Split on common delimiters and match each part.
    parts = re.split(r"[,/]| and ", component)
    matched = []
    seen = set()
    for part in parts:
        label = _match_component(part)
        if label and label not in seen:
            matched.append(label)
            seen.add(label)

    return matched if matched else [component.strip()]


def load_repairs(json_path: str = None) -> pd.DataFrame:
    """Load repair records from JSON file into a DataFrame."""
    if json_path is None:
        json_path = Path(__file__).parent.parent / "output.json"

    with open(json_path, "r") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # Handle both old format (component: string) and new format (components: list)
    if "component" in df.columns and "components" not in df.columns:
        # Old format: normalize string into list
        df["components"] = df["component"].apply(normalize_components)
        df = df.drop(columns=["component"])
    elif "component" in df.columns and "components" in df.columns:
        # Mixed: prefer components if present, fall back to component
        df["components"] = df.apply(
            lambda r: (
                r["components"]
                if isinstance(r["components"], list) and r["components"]
                else normalize_components(r["component"])
            ),
            axis=1,
        )
        df = df.drop(columns=["component"])
    elif "components" in df.columns:
        # New format: ensure lists, normalize any stray strings
        df["components"] = df["components"].apply(
            lambda c: c if isinstance(c, list) else normalize_components(c)
        )

    # Convert successful column to categorical for better handling
    df["outcome"] = df["successful"].map(
        {True: "Successful", False: "Failed", None: "Pending"}
    )

    return df


def compute_brand_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute repair counts and success rates by brand."""
    stats = (
        df.groupby("brand")
        .agg(
            total_repairs=("brand", "count"),
            successful_repairs=("successful", lambda x: (x == True).sum()),
            failed_repairs=("successful", lambda x: (x == False).sum()),
        )
        .reset_index()
    )

    # Calculate success rate (excluding pending)
    completed = df[df["successful"].notna()]
    success_rates = completed.groupby("brand")["successful"].mean() * 100
    stats = stats.merge(
        success_rates.reset_index().rename(columns={"successful": "success_rate"}),
        on="brand",
        how="left",
    )
    stats["success_rate"] = stats["success_rate"].fillna(0)

    return stats.sort_values("total_repairs", ascending=False)


def compute_component_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute failure counts by component (exploding the components list)."""
    exploded = df[["components", "successful"]].explode("components")
    exploded = exploded[exploded["components"].notna() & (exploded["components"] != "")]
    exploded = exploded.rename(columns={"components": "component"})
    counts = exploded["component"].value_counts().reset_index()
    counts.columns = ["component", "count"]
    return counts


def categorize_failure_reasons(df: pd.DataFrame) -> pd.DataFrame:
    """Categorize and count failure reasons."""
    failed = df[df["successful"] == False].copy()

    def categorize(reason):
        if pd.isna(reason):
            return "Unknown"
        reason_lower = reason.lower()

        # Check economic keywords first — most common reason
        econ_keywords = [
            "not econom",
            "uneconom",
            "not cost effective",
            "cost effective",
            "not worth",
            "too expensive",
            "exceed tool value",
            "exceed value",
            "cost more than",
            "costs more than",
            "cost nearly",
            "costs nearly",
            "costs as much",
            "cost as much",
            "cost equals",
            "costs equal",
            "making repair",
            "not viable",
        ]
        if any(kw in reason_lower for kw in econ_keywords):
            return "Not Economical"

        # Water, corrosion, or rust damage
        if (
            "water" in reason_lower
            or "corrosion" in reason_lower
            or "acid" in reason_lower
            or "rust" in reason_lower
        ):
            return "Water/Corrosion"

        # Parts unavailable or need ordering
        parts_keywords = [
            "not available",
            "no replacement",
            "not in stock",
            "need to be ordered",
            "needed to be ordered",
            "no longer available",
            "obsolete",
            "could not find",
            "did not have",
            "wrong size",
            "did not fit",
        ]
        if any(kw in reason_lower for kw in parts_keywords):
            return "Parts Unavailable"

        # Severe physical or electrical damage
        damage_keywords = [
            "burnt",
            "burned",
            "burn damage",
            "melted",
            "destroyed",
            "beyond repair",
            "shorted out",
            "completely failed",
            "severe",
            "trauma",
        ]
        if any(kw in reason_lower for kw in damage_keywords):
            return "Severe Damage"

        # Electrical / component failure
        elec_keywords = [
            "circuit board",
            "controller",
            "switch failure",
            "motor failure",
            "broken wires",
            "faulty",
            "cells",
            "battery",
            "board fail",
        ]
        if any(kw in reason_lower for kw in elec_keywords):
            return "Component Failure"

        return "Other"

    failed["failure_category"] = failed["failure_reason"].apply(categorize)
    return failed["failure_category"].value_counts().reset_index()


def get_tool_type_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Get counts of each tool type."""
    counts = df["tool_type"].value_counts().reset_index()
    counts.columns = ["tool_type", "count"]
    return counts


def get_brand_tool_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Create a matrix of brand vs tool type counts."""
    matrix = pd.crosstab(df["brand"], df["tool_type"])
    return matrix
