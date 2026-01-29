"""Chart creation functions for the repair analysis dashboard."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

try:
    from .styles import (
        BRAND_COLORS,
        OUTCOME_COLORS,
        CHART_TEMPLATE,
        DEFAULT_COLORS,
        HEATMAP_COLORS,
    )
    from .data_loader import (
        compute_brand_stats,
        compute_component_stats,
        categorize_failure_reasons,
        get_tool_type_counts,
        get_brand_tool_matrix,
    )
except ImportError:
    from styles import (
        BRAND_COLORS,
        OUTCOME_COLORS,
        CHART_TEMPLATE,
        DEFAULT_COLORS,
        HEATMAP_COLORS,
    )
    from data_loader import (
        compute_brand_stats,
        compute_component_stats,
        categorize_failure_reasons,
        get_tool_type_counts,
        get_brand_tool_matrix,
    )


def create_brand_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create horizontal bar chart of repairs by brand."""
    brand_counts = df["brand"].value_counts().reset_index()
    brand_counts.columns = ["brand", "count"]
    brand_counts = brand_counts.sort_values("count", ascending=True)

    colors = [BRAND_COLORS.get(brand, "#6B7280") for brand in brand_counts["brand"]]

    fig = go.Figure(go.Bar(
        x=brand_counts["count"],
        y=brand_counts["brand"],
        orientation="h",
        marker_color=colors,
        text=brand_counts["count"],
        textposition="outside",
    ))

    fig.update_layout(
        title="Repairs by Brand",
        xaxis_title="Number of Repairs",
        yaxis_title="",
        template=CHART_TEMPLATE,
        height=400,
        margin=dict(l=100, r=50, t=50, b=50),
    )

    return fig


def create_success_rate_chart(df: pd.DataFrame) -> go.Figure:
    """Create grouped bar chart showing success/failure counts per brand."""
    stats = compute_brand_stats(df)
    stats = stats.sort_values("total_repairs", ascending=False)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Successful",
        x=stats["brand"],
        y=stats["successful_repairs"],
        marker_color=OUTCOME_COLORS["Successful"],
        text=stats["successful_repairs"],
        textposition="auto",
    ))

    fig.add_trace(go.Bar(
        name="Failed",
        x=stats["brand"],
        y=stats["failed_repairs"],
        marker_color=OUTCOME_COLORS["Failed"],
        text=stats["failed_repairs"],
        textposition="auto",
    ))

    fig.update_layout(
        title="Success vs Failure by Brand",
        xaxis_title="Brand",
        yaxis_title="Number of Repairs",
        barmode="group",
        template=CHART_TEMPLATE,
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_tool_type_chart(df: pd.DataFrame) -> go.Figure:
    """Create treemap of tool types."""
    tool_counts = get_tool_type_counts(df)

    fig = px.treemap(
        tool_counts,
        path=["tool_type"],
        values="count",
        color="count",
        color_continuous_scale="Blues",
    )

    fig.update_layout(
        title="Tool Types Distribution",
        template=CHART_TEMPLATE,
        height=400,
    )

    fig.update_traces(
        textinfo="label+value",
        textfont_size=12,
    )

    return fig


def create_component_bar_chart(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Create bar chart of top N failing components."""
    components = compute_component_stats(df).head(top_n)
    components = components.sort_values("count", ascending=True)

    fig = go.Figure(go.Bar(
        x=components["count"],
        y=components["component"],
        orientation="h",
        marker_color=DEFAULT_COLORS[0],
        text=components["count"],
        textposition="outside",
    ))

    fig.update_layout(
        title=f"Top {top_n} Failing Components",
        xaxis_title="Number of Failures",
        yaxis_title="",
        template=CHART_TEMPLATE,
        height=400,
        margin=dict(l=200, r=50, t=50, b=50),
    )

    return fig


def create_outcome_donut(df: pd.DataFrame) -> go.Figure:
    """Create donut chart of repair outcomes."""
    outcome_counts = df["outcome"].value_counts().reset_index()
    outcome_counts.columns = ["outcome", "count"]

    colors = [OUTCOME_COLORS.get(outcome, "#6B7280") for outcome in outcome_counts["outcome"]]

    fig = go.Figure(go.Pie(
        labels=outcome_counts["outcome"],
        values=outcome_counts["count"],
        hole=0.5,
        marker_colors=colors,
        textinfo="label+value+percent",
        textposition="outside",
    ))

    fig.update_layout(
        title="Repair Outcomes",
        template=CHART_TEMPLATE,
        height=400,
        annotations=[dict(text="Outcomes", x=0.5, y=0.5, font_size=16, showarrow=False)],
    )

    return fig


def create_failure_reason_pie(df: pd.DataFrame) -> go.Figure:
    """Create pie chart of categorized failure reasons."""
    failure_cats = categorize_failure_reasons(df)
    failure_cats.columns = ["category", "count"]

    fig = go.Figure(go.Pie(
        labels=failure_cats["category"],
        values=failure_cats["count"],
        marker_colors=DEFAULT_COLORS[:len(failure_cats)],
        textinfo="label+value+percent",
        textposition="auto",
    ))

    fig.update_layout(
        title="Failure Reasons (Categorized)",
        template=CHART_TEMPLATE,
        height=400,
    )

    return fig


def create_brand_tool_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create heatmap of brand vs tool type."""
    matrix = get_brand_tool_matrix(df)

    fig = go.Figure(go.Heatmap(
        z=matrix.values,
        x=matrix.columns.tolist(),
        y=matrix.index.tolist(),
        colorscale=HEATMAP_COLORS,
        text=matrix.values,
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False,
    ))

    fig.update_layout(
        title="Brand vs Tool Type Matrix",
        xaxis_title="Tool Type",
        yaxis_title="Brand",
        template=CHART_TEMPLATE,
        height=500,
        xaxis=dict(tickangle=45),
    )

    return fig


def create_data_table(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare dataframe for display as filterable table."""
    display_cols = [
        "brand",
        "tool_type",
        "model",
        "component",
        "outcome",
        "problem",
        "failure_reason",
        "video_url",
    ]

    table_df = df[display_cols].copy()
    table_df.columns = [
        "Brand",
        "Tool Type",
        "Model",
        "Component",
        "Outcome",
        "Problem",
        "Failure Reason",
        "Video URL",
    ]

    return table_df
