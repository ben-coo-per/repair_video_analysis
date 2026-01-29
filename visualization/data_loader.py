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
        if "not economically viable" in reason_lower or "cost" in reason_lower:
            return "Not Economical"
        elif "part" in reason_lower and ("not available" in reason_lower or "not in stock" in reason_lower):
            return "Parts Unavailable"
        elif "damage" in reason_lower or "burnt" in reason_lower or "melted" in reason_lower:
            return "Severe Damage"
        elif "water" in reason_lower or "corrosion" in reason_lower:
            return "Water/Corrosion"
        else:
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
