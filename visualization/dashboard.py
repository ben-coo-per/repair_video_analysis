"""Main Streamlit dashboard for repair video analysis."""

import streamlit as st
import pandas as pd

from data_loader import load_repairs, compute_brand_stats
from charts import (
    create_brand_bar_chart,
    create_success_rate_chart,
    create_tool_type_chart,
    create_component_bar_chart,
    create_outcome_donut,
    create_failure_reason_pie,
    create_brand_tool_heatmap,
    create_data_table,
)

# Page configuration
st.set_page_config(
    page_title="Repair Video Analysis Dashboard",
    page_icon="🔧",
    layout="wide",
)

# Load data
@st.cache_data
def get_data():
    return load_repairs()

df = get_data()

# Sidebar filters
st.sidebar.header("Filters")

# Brand filter
brands = sorted([b for b in df["brand"].unique() if b is not None])
selected_brands = st.sidebar.multiselect("Brand", brands)

# Tool type filter
tool_types = sorted([t for t in df["tool_type"].unique() if t is not None])
selected_tool_types = st.sidebar.multiselect("Tool Type", tool_types)

# Component filter (explode the lists to get unique values)
all_components = sorted(set(c for comp_list in df["components"] for c in comp_list if c))
selected_components = st.sidebar.multiselect("Failing Component", all_components)

# Outcome filter
outcomes = sorted(df["outcome"].dropna().unique().tolist())
selected_outcomes = st.sidebar.multiselect("Outcome", outcomes)

# Apply filters (empty selection = show all)
filtered_df = df.copy()
if selected_brands:
    filtered_df = filtered_df[filtered_df["brand"].isin(selected_brands)]
if selected_tool_types:
    filtered_df = filtered_df[filtered_df["tool_type"].isin(selected_tool_types)]
if selected_components:
    filtered_df = filtered_df[filtered_df["components"].apply(
        lambda cl: any(c in selected_components for c in cl)
    )]
if selected_outcomes:
    filtered_df = filtered_df[filtered_df["outcome"].isin(selected_outcomes)]

# Header
st.title("Repair Video Analysis Dashboard")
st.markdown("Analysis of power tool repairs from video transcripts")

# KPI Metrics
col1, col2, col3, col4 = st.columns(4)

total_repairs = len(filtered_df)
successful_repairs = len(filtered_df[filtered_df["successful"] == True])
failed_repairs = len(filtered_df[filtered_df["successful"] == False])
completed_repairs = successful_repairs + failed_repairs
success_rate = (successful_repairs / completed_repairs * 100) if completed_repairs > 0 else 0

with col1:
    st.metric("Total Repairs", total_repairs)
with col2:
    st.metric("Successful", successful_repairs)
with col3:
    st.metric("Failed", failed_repairs)
with col4:
    st.metric("Success Rate", f"{success_rate:.1f}%")

st.divider()

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["Overview", "Analysis", "Details"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(create_brand_bar_chart(filtered_df), use_container_width=True)

    with col2:
        st.plotly_chart(create_outcome_donut(filtered_df), use_container_width=True)

    st.plotly_chart(create_tool_type_chart(filtered_df), use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(create_success_rate_chart(filtered_df), use_container_width=True)

    with col2:
        st.plotly_chart(create_component_bar_chart(filtered_df), use_container_width=True)

    # Only show failure reasons if there are failures
    if len(filtered_df[filtered_df["successful"] == False]) > 0:
        st.plotly_chart(create_failure_reason_pie(filtered_df), use_container_width=True)

with tab3:
    st.plotly_chart(create_brand_tool_heatmap(filtered_df), use_container_width=True)

    st.subheader("Repair Records")

    # Create clickable links for video URLs
    table_df = create_data_table(filtered_df)

    # Make video URLs clickable
    table_df["Video URL"] = table_df["Video URL"].apply(
        lambda x: f'<a href="{x}" target="_blank">Watch</a>' if pd.notna(x) else ""
    )

    st.write(
        table_df.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )

# Footer
st.sidebar.divider()
st.sidebar.markdown(f"**Total records:** {len(df)}")
st.sidebar.markdown(f"**Filtered records:** {len(filtered_df)}")

# Bibliography
unique_videos = df[["video_url", "video_title"]].drop_duplicates().dropna(subset=["video_url"])
unique_videos = unique_videos.sort_values("video_title")

with st.expander("Sources", expanded=False):
    sources_md = "  \n".join(
        f'<span style="font-size: 0.8em; color: #888;">'
        f'[{i+1}] <a href="{row["video_url"]}" target="_blank">{row["video_title"]}</a>'
        f'</span>'
        for i, (_, row) in enumerate(unique_videos.iterrows())
    )
    st.markdown(sources_md, unsafe_allow_html=True)
