"""Data loading and processing functions for repair video analysis."""

import json
from pathlib import Path
import pandas as pd


def load_repairs(json_path: str = None) -> pd.DataFrame:
    """Load repair records from JSON file into a DataFrame."""
    if json_path is None:
        json_path = Path(__file__).parent.parent / "output.json"

    with open(json_path, "r") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # Convert successful column to categorical for better handling
    df["outcome"] = df["successful"].map({
        True: "Successful",
        False: "Failed",
        None: "Pending"
    })

    return df


def compute_brand_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute repair counts and success rates by brand."""
    stats = df.groupby("brand").agg(
        total_repairs=("brand", "count"),
        successful_repairs=("successful", lambda x: (x == True).sum()),
        failed_repairs=("successful", lambda x: (x == False).sum())
    ).reset_index()

    # Calculate success rate (excluding pending)
    completed = df[df["successful"].notna()]
    success_rates = completed.groupby("brand")["successful"].mean() * 100
    stats = stats.merge(
        success_rates.reset_index().rename(columns={"successful": "success_rate"}),
        on="brand",
        how="left"
    )
    stats["success_rate"] = stats["success_rate"].fillna(0)

    return stats.sort_values("total_repairs", ascending=False)


def compute_component_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute failure counts by component."""
    # Filter out null components and get counts
    components = df[df["component"].notna()]["component"].value_counts().reset_index()
    components.columns = ["component", "count"]
    return components


def categorize_failure_reasons(df: pd.DataFrame) -> pd.DataFrame:
    """Categorize and count failure reasons."""
    failed = df[df["successful"] == False].copy()

    def categorize(reason):
        if pd.isna(reason):
            return "Unknown"
        reason_lower = reason.lower()

        # Check economic keywords first — most common reason
        econ_keywords = [
            "not econom", "uneconom", "not cost effective",
            "cost effective", "not worth", "too expensive",
            "exceed tool value", "exceed value",
            "cost more than", "costs more than",
            "cost nearly", "costs nearly",
            "costs as much", "cost as much",
            "cost equals", "costs equal",
            "making repair", "not viable",
            "better to replace",
        ]
        if any(kw in reason_lower for kw in econ_keywords):
            return "Not Economical"

        # Water, corrosion, or rust damage
        if "water" in reason_lower or "corrosion" in reason_lower or "acid" in reason_lower or "rust" in reason_lower:
            return "Water/Corrosion"

        # Parts unavailable or need ordering
        parts_keywords = [
            "not available", "no replacement", "not in stock",
            "need to be ordered", "needed to be ordered",
            "no longer available", "obsolete",
            "could not find", "did not have",
            "wrong size", "did not fit",
        ]
        if any(kw in reason_lower for kw in parts_keywords):
            return "Parts Unavailable"

        # Severe physical or electrical damage
        damage_keywords = [
            "burnt", "burned", "burn damage", "melted", "destroyed",
            "beyond repair", "shorted out",
            "completely failed", "severe", "trauma",
        ]
        if any(kw in reason_lower for kw in damage_keywords):
            return "Severe Damage"

        # Electrical / component failure
        elec_keywords = [
            "circuit board", "controller", "switch failure",
            "motor failure", "broken wires", "faulty",
            "cells", "battery", "board fail",
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
